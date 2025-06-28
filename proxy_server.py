# !!! WARNING !!!
# THIS IS A REVERSE PROXY. ITS SOLE PURPOSE IS TO ROUTE DYNAMIC API REQUESTS
# TO THE APPROPRIATE BACKEND SERVICE. IT SHOULD NOT, UNDER ANY CIRCUMSTANCES,
# BE USED TO SERVE STATIC FILES. THAT IS THE JOB OF A DEDICATED STATIC
# FILE SERVER (E.G., NGINX). ADDING STATIC FILE SERVING LOGIC TO THIS
# PROXY WILL ONLY LEAD TO CONFUSION AND MAINTENANCE HEADACHES.
#
# IF YOU ARE TEMPTED TO ADD STATIC FILE SERVING TO THIS PROXY, PLEASE
# RESIST THE URGE AND SET UP A PROPER STATIC FILE SERVER INSTEAD.

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import requests
import logging
import base64
from PIL import Image
import numpy as np
import io


# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Define the base URLs for the backend services
SERVICE_MAP = {
    "videostream_mock_server": "http://localhost:8003",
    "dct_service": "http://localhost:5002",
    "reference_frame_service": "http://localhost:5003",
    "difference_service": "http://localhost:5004",
    "accumulator_service": "http://localhost:5005",
    "orchestration_service": "http://localhost:5006",
    "visualizer_server": "http://localhost:5007" # The server for static visualizer files
}







@app.route('/api/v1/process-frame', methods=['POST'])
def process_frame():
    """
    This is the core orchestration endpoint. It receives an image from the client,
    sends it through the entire backend processing pipeline, and returns the
    final processed image. This function implements the logic defined in the
    `DCT-DIFF-DELAY-DATAMOSH.png` architectural schema.
    """
    logging.info("Received request at /api/v1/process-frame")

    # 1. Get the image data from the client request
    try:
        client_data = request.get_json()
        if not client_data or 'image' not in client_data:
            logging.error("Invalid request: 'image' field missing.")
            return jsonify({"error": "Invalid request: 'image' field missing."}), 400
        image_data_b64 = client_data['image']
        # Decode the Base64 string and open it as an image
        image_bytes = base64.b64decode(image_data_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert('L') # Convert to grayscale
        image_shape = np.array(image).shape
        image_array = np.array(image)
        # Flatten the array and convert it to a comma-separated string
        image_data = ','.join(map(str, image_array.flatten()))
    except Exception as e:
        logging.error(f"Failed to parse client request: {e}")
        return jsonify({"error": f"Invalid request format: {e}"}), 400

    # --- Backend Service Orchestration ---
    # This is the sequence of internal, server-to-server HTTP requests
    # that constitute the full data processing pipeline.

    try:
        # Step 2: Send image to DCT Service
        logging.info("Forwarding to DCT Service for main image...")
        dct_response = requests.post(
            f"{SERVICE_MAP['dct_service']}/forward_dct",
            json={"image_data": image_data, "frame_id": "main"}
        )
        dct_response.raise_for_status()
        dct_result = dct_response.json()['dct_data']

        # Step 3: Get reference frame from Reference Frame Service
        # (This assumes the reference frame service provides a reference frame)
        logging.info("Forwarding to Reference Frame Service...")
        ref_frame_response = requests.get(f"{SERVICE_MAP['reference_frame_service']}/get_reference_frame")
        ref_frame_response.raise_for_status()
        ref_frame_result = ref_frame_response.json()

        # Step 4: Send reference frame to DCT service
        logging.info("Forwarding reference frame to DCT Service...")
        ref_dct_response = requests.post(
            f"{SERVICE_MAP['dct_service']}/forward_dct",
            json={"image_data": ref_frame_result['reference_frame'], "frame_id": "reference"}
        )
        ref_dct_response.raise_for_status()
        ref_dct_result = ref_dct_response.json()['dct_data']

        # Step 5: Send both DCTs to Difference Service
        logging.info("Forwarding to Difference Service...")
        diff_payload = {
            "dct_A": dct_result,
            "dct_B": ref_dct_result,
            "frame_id": "difference"
        }
        diff_response = requests.post(
            f"{SERVICE_MAP['difference_service']}/calculate_difference",
            json=diff_payload
        )
        diff_response.raise_for_status()
        diff_result = diff_response.json()['difference_data']

        # Step 6: Send difference and original DCT to Accumulator Service
        logging.info("Forwarding to Accumulator Service...")
        accum_payload = {
            "frame_part": diff_result
        }
        accum_response = requests.post(
            f"{SERVICE_MAP['accumulator_service']}/accumulate_frame",
            json=accum_payload
        )
        accum_response.raise_for_status()
        get_accum_response = requests.get(f"{SERVICE_MAP['accumulator_service']}/get_accumulated_frame")
        get_accum_response.raise_for_status()
        accum_result = get_accum_response.json()['accumulated_frame']

        # Step 7: Send accumulated result to Inverse DCT (which is the same DCT service)
        logging.info("Forwarding to Inverse DCT Service...")
        idct_response = requests.post(
            f"{SERVICE_MAP['dct_service']}/inverse_dct",
            json={"dct_data": accum_result, "frame_id": "final"}
        )
        idct_response.raise_for_status()
        final_image_data = idct_response.json()['image_data']

        # Convert the comma-separated string back to an image
        final_image_array = np.fromstring(final_image_data, sep=',')
        # Reshape the array to the original image dimensions.
        final_image_array = final_image_array.reshape(image_shape)
        final_image = Image.fromarray(final_image_array.astype(np.uint8))
        
        # Save the image to a byte buffer
        buf = io.BytesIO()
        final_image.save(buf, format='PNG')
        buf.seek(0)

        return Response(buf, mimetype='image/png')

    except requests.exceptions.RequestException as e:
        # This is a catch-all for network errors during backend communication.
        logging.error(f"A backend service was unreachable: {e}")
        return jsonify({"error": f"A backend service was unreachable: {e}"}), 502
    except Exception as e:
        # This catches other unexpected errors during the orchestration.
        logging.error(f"An unexpected error occurred during orchestration: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@app.route('/')
def serve_index():
    """
    Serves the main visualizer HTML file. This is the entry point for the
    web-based client.
    """
    logging.info("Serving index.html")
    return send_from_directory('.', 'visualizer_v3.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """
    Serves any other static files (like JavaScript, CSS) requested by the
    visualizer.
    """
    logging.info(f"Serving static file: {path}")
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(port=5008) # Proxy server will run on port 5008


# This server is typically started by `start_visualizer_services.sh`.
