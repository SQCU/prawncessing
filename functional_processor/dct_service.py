from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from scipy.fftpack import dct, idct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

def _perform_forward_dct(image_data: str, frame_id: str) -> str:
    """
    Pure function to perform a forward Discrete Cosine Transform (DCT).
    """
    try:
        # Convert the input string to a numpy array
        image_array = np.fromstring(image_data, sep=',')
        
        # Perform the DCT with orthogonal normalization
        dct_data = dct(image_array, norm='ortho')
        
        # Convert the numpy array to a string for JSON serialization
        return ','.join(map(str, dct_data))
    except Exception as e:
        logging.error(f"Error in _perform_forward_dct for frame {frame_id}: {e}")
        raise

def _perform_inverse_dct(dct_data: str, frame_id: str) -> str:
    """
    Pure function to perform an inverse Discrete Cosine Transform (IDCT).
    """
    try:
        # Convert the input string to a numpy array
        dct_array = np.fromstring(dct_data, sep=',')
        
        # Perform the IDCT with orthogonal normalization
        image_data = idct(dct_array, norm='ortho')
        
        # Convert the numpy array to a string for JSON serialization
        return ','.join(map(str, image_data))
    except Exception as e:
        logging.error(f"Error in _perform_inverse_dct for frame {frame_id}: {e}")
        raise

@app.route('/forward_dct', methods=['POST'])
def forward_dct():
    """
    Performs a forward Discrete Cosine Transform (DCT) on input image data.
    Expects 'frame_id' and 'image_data' in the request body.
    """
    data = request.json
    if not data or 'frame_id' not in data or 'image_data' not in data:
        return jsonify({"error": "Invalid request: 'frame_id' and 'image_data' are required."}), 400

    frame_id = data.get('frame_id')
    image_data = data.get('image_data')

    try:
        dct_data = _perform_forward_dct(image_data, frame_id)
        logging.info(f"Performing forward DCT for frame: {frame_id}")
        return jsonify({"status": "forward DCT complete", "frame_id": frame_id, "dct_data": dct_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/inverse_dct', methods=['POST'])
def inverse_dct():
    """
    Performs an inverse Discrete Cosine Transform (IDCT) on input DCT data.
    Expects 'frame_id' and 'dct_data' in the request body.
    """
    data = request.json
    if not data or 'frame_id' not in data or 'dct_data' not in data:
        return jsonify({"error": "Invalid request: 'frame_id' and 'dct_data' are required."}), 400

    frame_id = data.get('frame_id')
    dct_data = data.get('dct_data')

    try:
        image_data = _perform_inverse_dct(dct_data, frame_id)
        logging.info(f"Performing inverse DCT for frame: {frame_id}")
        return jsonify({"status": "inverse DCT complete", "frame_id": frame_id, "image_data": image_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

