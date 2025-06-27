from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from scipy.fftpack import dct, idct

_HIGH_VERBOSITY_MODE = False # Set to True to enable in-program identity test

app = Flask(__name__)
CORS(app)

_latest_forward_dct_data = None
_latest_inverse_dct_data = None

def _run_identity_test_if_verbose(func):
    """
    Decorator to run an in-program identity test for DCT/IDCT round-trip
    when _HIGH_VERBOSITY_MODE is True.

    Purpose: This in-program test verifies the perfect invertibility of the
             DCT and IDCT operations.
    Expectation: For a perfectly invertible transform, the original data
                 should be nearly identical to the data reconstructed after
                 a forward and inverse transform. Without proper normalization
                 (e.g., `norm='ortho'`), this test is expected to fail due
                 to scaling discrepancies.
    """
    def wrapper(data_str, frame_id):
        result = func(data_str, frame_id) # Call the original function

        if _HIGH_VERBOSITY_MODE:
            print(f"--- Running in-program identity test for frame {frame_id} ---")
            # Generate some sample data for the test
            original_sample_data = np.random.rand(10)
            original_sample_data_str = ",".join(map(str, original_sample_data))

            # Perform forward DCT
            test_dct_data_str = _perform_forward_dct(original_sample_data_str, "test_identity_fwd")

            # Perform inverse DCT on the result of the forward DCT
            reconstructed_sample_data_str = _perform_inverse_dct(test_dct_data_str, "test_identity_inv")
            reconstructed_sample_data = np.fromstring(reconstructed_sample_data_str, sep=',')

            # Compare original and reconstructed data
            is_close = np.allclose(original_sample_data, reconstructed_sample_data)
            if is_close:
                print("In-program identity test PASSED.")
            else:
                print("In-program identity test FAILED: Original and reconstructed data are not close.")
                print(f"  Original: {original_sample_data}")
                print(f"  Reconstructed: {reconstructed_sample_data}")
            print("--- In-program identity test finished ---")
        return result
    return wrapper

def _perform_forward_dct(image_data: str, frame_id: str) -> str:
    """
    Pure function to perform a forward Discrete Cosine Transform (DCT).
    """
    # Convert the input string to a numpy array
    # Assuming image_data is a comma-separated string of numbers
    image_array = np.fromstring(image_data, sep=',')
    
    # Perform the DCT with orthogonal normalization
    dct_data = dct(image_array, norm='ortho')
    
    # Convert the numpy array to a string for JSON serialization
    return ','.join(map(str, dct_data))

@_run_identity_test_if_verbose
def _perform_inverse_dct(dct_data: str, frame_id: str) -> str:
    """
    Pure function to perform an inverse Discrete Cosine Transform (IDCT).
    """
    # Convert the input string to a numpy array
    dct_array = np.fromstring(dct_data, sep=',')
    
    # Perform the IDCT with orthogonal normalization
    image_data = idct(dct_array, norm='ortho')
    
    # Convert the numpy array to a string for JSON serialization
    return ','.join(map(str, image_data))

@app.route('/forward_dct', methods=['POST'])
def forward_dct():
    """
    Performs a forward Discrete Cosine Transform (DCT) on input image data.
    Expects 'frame_id' and 'image_data' in the request body.
    Returns mock 'dct_data'.
    """
    global _latest_forward_dct_data
    data = request.json
    if not data or 'frame_id' not in data or 'image_data' not in data:
        return jsonify({"error": "Invalid request: 'frame_id' and 'image_data' are required."}), 400

    frame_id = data.get('frame_id')
    image_data = data.get('image_data')

    dct_data = _perform_forward_dct(image_data, frame_id)
    _latest_forward_dct_data = dct_data # Store the latest forward DCT data
    print(f"Performing forward DCT for frame: {frame_id}")
    return jsonify({"status": "forward DCT complete", "frame_id": frame_id, "dct_data": dct_data}), 200

@app.route('/inverse_dct', methods=['POST'])
def inverse_dct():
    """
    Performs an inverse Discrete Cosine Transform (IDCT) on input DCT data.
    Expects 'frame_id' and 'dct_data' in the request body.
    Returns mock 'image_data'.
    """
    global _latest_inverse_dct_data
    data = request.json
    if not data or 'frame_id' not in data or 'dct_data' not in data:
        return jsonify({"error": "Invalid request: 'frame_id' and 'dct_data' are required."}), 400

    frame_id = data.get('frame_id')
    dct_data = data.get('dct_data')

    image_data = _perform_inverse_dct(dct_data, frame_id)
    _latest_inverse_dct_data = image_data # Store the latest inverse DCT data
    print(f"Performing inverse DCT for frame: {frame_id}")
    return jsonify({"status": "inverse DCT complete", "frame_id": frame_id, "image_data": image_data}), 200

@app.route('/latest_forward_dct', methods=['GET'])
def get_latest_forward_dct():
    """
    Returns the latest forward DCT data.
    """
    return jsonify({"status": "success", "latest_dct": _latest_forward_dct_data})

@app.route('/latest_inverse_dct', methods=['GET'])
def get_latest_inverse_dct():
    """
    Returns the latest inverse DCT data.
    """
    return jsonify({"status": "success", "latest_image": _latest_inverse_dct_data})

if __name__ == '__main__':
    app.run(port=5002)
