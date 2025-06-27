from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

import numpy as np

# In a real implementation, this would be a more robust storage
_reference_frame_data = None

def _set_reference_frame_data(frame_data: str) -> str:
    """
    Pure function to set the reference frame data.
    Converts the input string to a numpy array for internal consistency.
    """
    # Convert the input string to a numpy array
    frame_array = np.fromstring(frame_data, sep=',')
    
    # For now, we just return the string representation of the array
    return ','.join(map(str, frame_array))

@app.route('/set_reference_frame', methods=['POST'])
def set_reference_frame():
    global _reference_frame_data
    data = request.json
    frame_data = data.get('frame_data')
    if not frame_data:
        return jsonify({"error": "Invalid request: 'frame_data' is required."}), 400

    _reference_frame_data = _set_reference_frame_data(frame_data)
    print(f"Reference frame set.")
    return jsonify({"status": "reference frame set"})

@app.route('/get_reference_frame', methods=['GET'])
def get_reference_frame():
    return jsonify({"status": "success", "reference_frame": _reference_frame_data})

@app.route('/latest_reference_frame', methods=['GET'])
def get_latest_reference_frame():
    """
    Returns the latest reference frame data.
    """
    return jsonify({"status": "success", "latest_reference_frame": _reference_frame_data})

if __name__ == '__main__':
    app.run(port=5003)
