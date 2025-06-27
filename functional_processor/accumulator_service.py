from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

import numpy as np

# In a real implementation, this would accumulate frame data
_accumulated_frame_data = None

def _accumulate(current_data: str | None, new_part: str) -> str:
    """
    Pure function to accumulate frame data.
    This combines the new_part (numpy array as string) with current_data (numpy array as string).
    """
    new_part_array = np.fromstring(new_part, sep=',')

    if current_data:
        current_data_array = np.fromstring(current_data, sep=',')
        # Ensure arrays have the same shape before addition
        max_len = max(len(current_data_array), len(new_part_array))
        current_data_array = np.pad(current_data_array, (0, max_len - len(current_data_array)), 'constant')
        new_part_array = np.pad(new_part_array, (0, max_len - len(new_part_array)), 'constant')

        accumulated_array = current_data_array + new_part_array
    else:
        accumulated_array = new_part_array

    return ','.join(map(str, accumulated_array))

@app.route('/accumulate_frame', methods=['POST'])
def accumulate_frame():
    global _accumulated_frame_data
    data = request.json
    frame_part = data.get('frame_part')
    if not frame_part:
        return jsonify({"error": "Invalid request: 'frame_part' is required."}), 400

    _accumulated_frame_data = _accumulate(_accumulated_frame_data, frame_part)
    print(f"Accumulating frame part: {frame_part}")
    return jsonify({"status": "frame accumulated"})

@app.route('/get_accumulated_frame', methods=['GET'])
def get_accumulated_frame():
    return jsonify({"status": "success", "accumulated_frame": _accumulated_frame_data})

if __name__ == '__main__':
    app.run(port=5005)
