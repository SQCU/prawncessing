from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

# In-memory store for frame data
frame_store = {}

@app.route('/input_frame', methods=['POST'])
def input_frame():
    """
    Receives a video frame as JSON data and stores it.
    Expects 'frame_id' and 'frame_data' in the request body.
    """
    data = request.json
    if not data or 'frame_id' not in data or 'frame_data' not in data:
        logging.error("Invalid request: 'frame_id' and 'frame_data' are required.")
        return jsonify({"error": "Invalid request: 'frame_id' and 'frame_data' are required."}), 400

    frame_id = data.get('frame_id')
    frame_data = data.get('frame_data')
    
    frame_store[frame_id] = frame_data
    logging.info(f"Stored frame {frame_id}. Data size: {len(frame_data) if isinstance(frame_data, str) else 'N/A'} bytes.")

    return jsonify({"status": "frame stored", "frame_id": frame_id}), 200

@app.route('/get_frame/<frame_id>', methods=['GET'])
def get_frame(frame_id):
    """
    Retrieves a stored frame by its ID.
    """
    if frame_id in frame_store:
        logging.info(f"Retrieved frame {frame_id}.")
        return jsonify({"status": "success", "frame_id": frame_id, "frame_data": frame_store[frame_id]})
    else:
        logging.warning(f"Frame {frame_id} not found.")
        return jsonify({"error": "Frame not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

