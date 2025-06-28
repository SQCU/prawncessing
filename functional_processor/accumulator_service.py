from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

# In-memory store for the accumulated frame
_accumulated_frame_data = None

def _accumulate(current_data: str | None, new_part: str) -> str:
    """
    Pure function to accumulate frame data.
    """
    try:
        new_part_array = np.fromstring(new_part, sep=',')

        if current_data:
            current_data_array = np.fromstring(current_data, sep=',')
            max_len = max(len(current_data_array), len(new_part_array))
            current_data_array = np.pad(current_data_array, (0, max_len - len(current_data_array)), 'constant')
            new_part_array = np.pad(new_part_array, (0, max_len - len(new_part_array)), 'constant')
            accumulated_array = current_data_array + new_part_array
        else:
            accumulated_array = new_part_array

        return ','.join(map(str, accumulated_array))
    except Exception as e:
        logging.error(f"Error in _accumulate: {e}")
        raise

@app.route('/accumulate_frame', methods=['POST'])
def accumulate_frame():
    global _accumulated_frame_data
    data = request.json
    if not data or 'frame_part' not in data:
        return jsonify({"error": "Invalid request: 'frame_part' is required."}), 400

    frame_part = data.get('frame_part')
    
    try:
        _accumulated_frame_data = _accumulate(_accumulated_frame_data, frame_part)
        logging.info(f"Accumulating frame part.")
        return jsonify({"status": "frame accumulated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_accumulated_frame', methods=['GET'])
def get_accumulated_frame():
    if _accumulated_frame_data is not None:
        return jsonify({"status": "success", "accumulated_frame": _accumulated_frame_data}), 200
    else:
        return jsonify({"error": "Accumulated frame not available"}), 404

@app.route('/reset_accumulator', methods=['POST'])
def reset_accumulator():
    """
    Resets the accumulator to its initial state.
    """
    global _accumulated_frame_data
    _accumulated_frame_data = None
    logging.info("Accumulator reset.")
    return jsonify({"status": "accumulator reset"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)

