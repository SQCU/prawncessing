from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64
import time
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

VIDEOSTREAM_MOCK_SERVER_URL = "http://localhost:8003"
ORCHESTRATION_SERVICE_URL = "http://localhost:5006"

_latest_frame_data = None
_is_streaming = False
_frame_counter = 0

def _process_input_frame(frame_id: str, frame_data: str) -> dict:
    """
    Pure function to process an input video frame.
    Forwards the frame to the orchestration service.
    """
    global _latest_frame_data
    _latest_frame_data = frame_data # Store the latest frame data
    logging.info(f"Received frame {frame_id}. Data size: {len(frame_data) if isinstance(frame_data, str) else 'N/A'} bytes.")

    try:
        # Forward the frame to the orchestration service
        response = requests.post(f"{ORCHESTRATION_SERVICE_URL}/process_frame", json={'frame_id': frame_id, 'image_data': frame_data})
        response.raise_for_status()
        logging.info(f"Frame {frame_id} forwarded to orchestration service. Response: {response.json()}")
        return {"status": "frame received and forwarded", "frame_id": frame_id}
    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding frame {frame_id} to orchestration service: {e}")
        return {"status": "error", "message": f"Failed to forward frame: {e}"}

def _stream_frames():
    global _is_streaming, _frame_counter
    _frame_counter = 0
    while _is_streaming:
        try:
            # Fetch frame from videostream_mock_server
            response = requests.get(f"{VIDEOSTREAM_MOCK_SERVER_URL}/frame")
            response.raise_for_status()
            
            # The videostream_mock_server returns JPEG binary data directly
            # We need to base64 encode it to send as JSON
            frame_data_b64 = base64.b64encode(response.content).decode('utf-8')
            
            _frame_counter += 1
            frame_id = f"mock_frame_{_frame_counter}"
            
            _process_input_frame(frame_id, frame_data_b64)
            
            time.sleep(0.033) # Simulate ~30fps

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching frame from videostream_mock_server: {e}")
            _is_streaming = False # Stop streaming on error
        except Exception as e:
            logging.error(f"An unexpected error occurred during streaming: {e}")
            _is_streaming = False

@app.route('/input_frame', methods=['POST'])
def input_frame():
    """
    Receives a video frame as JSON data.
    Expects 'frame_id' and 'frame_data' in the request body.
    """
    data = request.json
    if not data or 'frame_id' not in data or 'frame_data' not in data:
        return jsonify({"error": "Invalid request: 'frame_id' and 'frame_data' are required."}), 400

    frame_id = data.get('frame_id')
    frame_data = data.get('frame_data')

    result = _process_input_frame(frame_id, frame_data)
    return jsonify(result), 200

@app.route('/start_stream', methods=['POST'])
def start_stream():
    global _is_streaming
    if not _is_streaming:
        _is_streaming = True
        threading.Thread(target=_stream_frames).start()
        logging.info("Started streaming frames from videostream_mock_server.")
        return jsonify({"status": "streaming started"}), 200
    return jsonify({"status": "streaming already active"}), 200

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global _is_streaming
    if _is_streaming:
        _is_streaming = False
        logging.info("Stopped streaming frames.")
        return jsonify({"status": "streaming stopped"}), 200
    return jsonify({"status": "streaming not active"}), 200

@app.route('/latest_frame', methods=['GET'])
def get_latest_frame():
    """
    Returns the latest received frame data.
    """
    return jsonify({"status": "success", "latest_frame": _latest_frame_data, "frame_count": _frame_counter})

if __name__ == '__main__':
    app.run(port=5001)

# This service is typically started by `start_functional_processors_orchestration.sh`.

