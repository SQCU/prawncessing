from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

def _calculate_dct_difference(dct1: str, dct2: str) -> str:
    """
    Pure function to calculate the difference between two DCTs.
    """
    try:
        dct1_array = np.fromstring(dct1, sep=',')
        dct2_array = np.fromstring(dct2, sep=',')
        
        # Ensure arrays have the same shape before subtraction
        if dct1_array.shape != dct2_array.shape:
            max_len = max(len(dct1_array), len(dct2_array))
            dct1_array = np.pad(dct1_array, (0, max_len - len(dct1_array)), 'constant')
            dct2_array = np.pad(dct2_array, (0, max_len - len(dct2_array)), 'constant')

        difference_array = dct1_array - dct2_array
        return ','.join(map(str, difference_array))
    except Exception as e:
        logging.error(f"Error in _calculate_dct_difference: {e}")
        raise

@app.route('/calculate_difference', methods=['POST'])
def calculate_difference():
    data = request.json
    if not data or 'dct1' not in data or 'dct2' not in data:
        return jsonify({"error": "Invalid request: 'dct1' and 'dct2' are required."}), 400

    dct1 = data.get('dct1')
    dct2 = data.get('dct2')
    
    try:
        difference_data = _calculate_dct_difference(dct1, dct2)
        logging.info(f"Calculating difference between two DCTs.")
        return jsonify({"status": "difference calculated", "difference_data": difference_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)

