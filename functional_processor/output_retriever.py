import requests
import json
import numpy as np
import cv2
import base64

# Define the URLs for the functional services
DCT_SERVICE_URL = "http://localhost:5002"
ACCUMULATOR_SERVICE_URL = "http://localhost:5005"

# Assuming the video dimensions from videostream_mock_server.py
# These should ideally be passed along the pipeline or configured globally
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

def get_processed_frame_logic():
    """
    Retrieves the currently accumulated frame data, performs inverse DCT,
    and returns the reconstructed image data as a base64 encoded JPEG.
    """
    # Get the accumulated frame data
    accumulated_response = requests.get(f"{ACCUMULATOR_SERVICE_URL}/get_accumulated_frame")
    accumulated_response.raise_for_status()
    accumulated_data_str = accumulated_response.json().get('accumulated_frame')

    if not accumulated_data_str:
        return {"status": "no accumulated data"}

    # Perform inverse DCT on the accumulated data
    # We need a dummy frame_id for the IDCT service
    idct_response = requests.post(f"{DCT_SERVICE_URL}/inverse_dct", json={'frame_id': 'accumulated', 'dct_data': accumulated_data_str})
    idct_response.raise_for_status()
    reconstructed_1d_str = idct_response.json().get('image_data')

    if not reconstructed_1d_str:
        return {"status": "failed to reconstruct image data"}

    # Convert the reconstructed 1D string to a numpy array
    reconstructed_array = np.fromstring(reconstructed_1d_str, sep=',')

    # Ensure the array has the correct number of elements for a BGR image
    expected_elements = VIDEO_WIDTH * VIDEO_HEIGHT * 3
    if len(reconstructed_array) != expected_elements:
        # This indicates a mismatch in data size, which needs to be handled
        # For now, we'll log an error and return
        print(f"Error: Reconstructed array length ({len(reconstructed_array)}) does not match expected ({expected_elements})")
        return {"status": "error", "message": "Reconstructed image data size mismatch"}

    # Reshape the 1D array into a 2D image array (Height, Width, Channels)
    # Ensure data type is uint8 and values are clamped to 0-255
    reconstructed_image = reconstructed_array.reshape((VIDEO_HEIGHT, VIDEO_WIDTH, 3)).astype(np.uint8)
    reconstructed_image = np.clip(reconstructed_image, 0, 255) # Clamp values

    # Encode the numpy array as a JPEG image
    ret, jpeg = cv2.imencode('.jpg', reconstructed_image)

    if not ret:
        print("Error: cv2.imencode failed to encode image to JPEG.")
        return {"status": "error", "message": "Failed to encode image to JPEG"}

    # Base64 encode the JPEG bytes
    encoded_jpeg_b64 = base64.b64encode(jpeg.tobytes()).decode('utf-8')

    return {"status": "success", "image_data_b64": encoded_jpeg_b64}
