from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

# In-memory store for the reference frame
_reference_frame_data = None

def _set_reference_frame_data(frame_data: str) -> str:
    """
    Pure function to validate and prepare reference frame data.
    """
    try:
        # Validate that the data can be converted to a numpy array
        frame_array = np.fromstring(frame_data, sep=',')
        return ','.join(map(str, frame_array))
    except Exception as e:
        logging.error(f"Error processing reference frame data: {e}")
        raise

@app.route('/set_reference_frame', methods=['POST'])
def set_reference_frame():
    global _reference_frame_data
    data = request.json
    if not data or 'frame_data' not in data:
        return jsonify({"error": "Invalid request: 'frame_data' is required."}), 400

    frame_data = data.get('frame_data')
    
    try:
        _reference_frame_data = _set_reference_frame_data(frame_data)
        logging.info(f"Reference frame set.")
        return jsonify({"status": "reference frame set"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_reference_frame', methods=['GET'])
def get_reference_frame():
    if _reference_frame_data is not None:
        return jsonify({"status": "success", "reference_frame": _reference_frame_data}), 200
    else:
        return jsonify({"error": "Reference frame not set"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

