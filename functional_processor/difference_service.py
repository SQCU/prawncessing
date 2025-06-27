from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_latest_difference_data = None

import numpy as np

def _calculate_dct_difference(dct1: str, dct2: str) -> str:
    """
    Pure function to calculate the difference between two DCTs.
    """
    dct1_array = np.fromstring(dct1, sep=',')
    dct2_array = np.fromstring(dct2, sep=',')
    
    # Ensure arrays have the same shape before subtraction
    if dct1_array.shape != dct2_array.shape:
        # Pad the smaller array with zeros to match the larger one
        max_len = max(len(dct1_array), len(dct2_array))
        dct1_array = np.pad(dct1_array, (0, max_len - len(dct1_array)), 'constant')
        dct2_array = np.pad(dct2_array, (0, max_len - len(dct2_array)), 'constant')

    difference_array = dct1_array - dct2_array
    return ','.join(map(str, difference_array))

@app.route('/calculate_difference', methods=['POST'])
def calculate_difference():
    global _latest_difference_data
    # Placeholder for difference calculation
    data = request.json
    dct1 = data.get('dct1')
    dct2 = data.get('dct2')
    # In a real implementation, calculate the difference between DCTs
    print(f"Calculating difference between {dct1} and {dct2}")
    difference_data = _calculate_dct_difference(dct1, dct2)
    _latest_difference_data = difference_data # Store the latest difference data
    return jsonify({"status": "difference calculated", "difference_data": difference_data})

@app.route('/latest_difference', methods=['GET'])
def get_latest_difference():
    """
    Returns the latest calculated difference data.
    """
    return jsonify({"status": "success", "latest_difference": _latest_difference_data})

if __name__ == '__main__':
    app.run(port=5004)

# This service is typically started by `functional_processor/start_functional_processors.sh` or `start_functional_processors_orchestration.sh`.

