
import requests
import numpy as np
import random
import time
import math
import json

# Configuration
SCIPY_DCT_URL = "http://127.0.0.1:8001/dct"
SCIPY_IDCT_URL = "http://127.0.0.1:8001/idct"
NUMPY_FFT_URL = "http://127.0.0.1:8002/fft2"
NUMPY_IFFT_URL = "http://127.0.0.1:8002/ifft2"

# --- Helper Functions for Data Generation ---

def generate_float_matrix(rows, cols, min_val=0.0, max_val=255.0):
    """Generates a 2D list of floats."""
    return [[random.uniform(min_val, max_val) for _ in range(cols)] for _ in range(rows)]

def generate_complex_string_matrix(rows, cols):
    """Generates a 2D list of strings representing complex numbers."""
    return [[str(complex(random.uniform(-100, 100), random.uniform(-100, 100))) for _ in range(cols)] for _ in range(rows)]

# --- Helper Functions for API Interaction and Validation ---

def validate_response_structure(response_json, expected_keys):
    """Validates if the response JSON has the expected top-level keys."""
    if not isinstance(response_json, dict):
        return False, "Response is not a dictionary."
    for key in expected_keys:
        if key not in response_json:
            return False, f"Missing expected key: {key}"
    return True, "Structure valid."

def validate_matrix_of_type(matrix, expected_type):
    """Validates if a 2D list contains elements of the expected type."""
    if not isinstance(matrix, list):
        return False, "Not a list."
    if not all(isinstance(row, list) for row in matrix):
        return False, "Not a list of lists."
    if not all(all(isinstance(item, expected_type) for item in row) for row in matrix):
        return False, f"Not all elements are of type {expected_type.__name__}."
    return True, "Type valid."

def test_api_endpoint(url, payload, expected_output_type, endpoint_name):
    """Sends a request and validates the response against the contract."""
    try:
        response = requests.post(url, json=payload, timeout=10)
        response_json = response.json()

        if response.status_code == 200:
            is_valid, msg = validate_response_structure(response_json, ["result"])
            if not is_valid:
                return False, f"[{endpoint_name}] Invalid success response structure: {msg}"

            is_valid, msg = validate_matrix_of_type(response_json["result"], expected_output_type)
            if not is_valid:
                return False, f"[{endpoint_name}] Invalid success result type: {msg}"
            return True, f"[{endpoint_name}] Contract valid."
        else:
            is_valid, msg = validate_response_structure(response_json, ["error"])
            if not is_valid:
                return False, f"[{endpoint_name}] Invalid error response structure: {msg}"
            return False, f"[{endpoint_name}] API returned error status {response.status_code}: {response_json.get('error', 'No error message')}"
    except requests.exceptions.RequestException as e:
        return False, f"[{endpoint_name}] Network or request error: {e}"
    except json.JSONDecodeError:
        return False, f"[{endpoint_name}] Invalid JSON response."
    except Exception as e:
        return False, f"[{endpoint_name}] Unexpected error during test: {e}"

# --- Stochastic Tester Logic ---

def run_stochastic_tester(num_iterations=1000):
    consecutive_successes = 0
    print("Starting stochastic API contract tester...")

    for i in range(num_iterations):
        # Logarithmic backoff
        if consecutive_successes > 0:
            probability = 1.0 / math.log(consecutive_successes + 2)
            if random.random() > probability:
                print(f"Iteration {i+1}: Skipping test due to backoff (consecutive successes: {consecutive_successes})")
                consecutive_successes += 1 # Still count as success for backoff
                continue

        rows = random.randint(8, 64)
        cols = random.randint(8, 64)

        print(f"Iteration {i+1}: Testing with matrix size {rows}x{cols}")

        # Test SciPy DCT
        data_scipy_dct = generate_float_matrix(rows, cols)
        success, msg = test_api_endpoint(SCIPY_DCT_URL, {"data": data_scipy_dct}, float, "SciPy DCT")
        print(msg)
        if not success:
            consecutive_successes = 0
            print("Contract violation detected. Resetting backoff.")
            continue
        
        # Test SciPy IDCT
        # For IDCT, we need valid DCT coefficients. For simplicity, we'll use the same float matrix.
        # In a real scenario, you might want to run DCT first and then feed its output to IDCT.
        data_scipy_idct = generate_float_matrix(rows, cols) 
        success, msg = test_api_endpoint(SCIPY_IDCT_URL, {"data": data_scipy_idct}, float, "SciPy IDCT")
        print(msg)
        if not success:
            consecutive_successes = 0
            print("Contract violation detected. Resetting backoff.")
            continue

        # Test NumPy FFT
        data_numpy_fft = generate_float_matrix(rows, cols)
        success, msg = test_api_endpoint(NUMPY_FFT_URL, {"data": data_numpy_fft}, str, "NumPy FFT")
        print(msg)
        if not success:
            consecutive_successes = 0
            print("Contract violation detected. Resetting backoff.")
            continue

        # Test NumPy IFFT
        data_numpy_ifft = generate_complex_string_matrix(rows, cols)
        success, msg = test_api_endpoint(NUMPY_IFFT_URL, {"data": data_numpy_ifft}, float, "NumPy IFFT")
        print(msg)
        if not success:
            consecutive_successes = 0
            print("Contract violation detected. Resetting backoff.")
            continue

        consecutive_successes += 1
        time.sleep(0.1) # Small delay to avoid hammering the servers

    print(f"Stochastic API contract tester finished after {num_iterations} iterations.")
    print(f"Longest streak of consecutive successes: {consecutive_successes}")

if __name__ == "__main__":
    run_stochastic_tester()
