

import requests
import time
import numpy as np
import cv2
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from tqdm import tqdm
import pandas as pd
import random
import math

# --- Helper Functions for Data Generation (moved from orchestrate_benchmark.py) ---

def generate_float_matrix(rows, cols, min_val=0.0, max_val=255.0):
    """Generates a 2D list of floats."""
    return [[random.uniform(min_val, max_val) for _ in range(cols)] for _ in range(rows)]

def generate_complex_string_matrix(rows, cols):
    """Generates a 2D list of strings representing complex numbers."""
    return [[str(complex(random.uniform(-100, 100), random.uniform(-100, 100))) for _ in range(cols)] for _ in range(rows)]

# --- Helper Functions for API Interaction and Validation (moved from orchestrate_benchmark.py) ---

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

def test_api_endpoint(url, payload, expected_output_type, endpoint_name, log_success=True):
    """Sends a request and validates the response against the contract."""
    try:
        response = requests.post(url, json=payload, timeout=10)
        response_json = response.json()

        if response.status_code == 200:
            is_valid, msg = validate_response_structure(response_json, ["result"])
            if not is_valid:
                if log_success: print(f"[{endpoint_name}] Invalid success response structure: {msg}", file=os.sys.stderr)
                return False, f"[{endpoint_name}] Invalid success response structure: {msg}"

            is_valid, msg = validate_matrix_of_type(response_json["result"], expected_output_type)
            if not is_valid:
                if log_success: print(f"[{endpoint_name}] Invalid success result type: {msg}", file=os.sys.stderr)
                return False, f"[{endpoint_name}] Invalid success result type: {msg}"
            if log_success: print(f"[{endpoint_name}] Contract valid.", file=os.sys.stderr)
            return True, f"[{endpoint_name}] Contract valid."
        else:
            is_valid, msg = validate_response_structure(response_json, ["error"])
            if not is_valid:
                print(f"[{endpoint_name}] Invalid error response structure: {msg}", file=os.sys.stderr)
                return False, f"[{endpoint_name}] Invalid error response structure: {msg}"
            print(f"[{endpoint_name}] API returned error status {response.status_code}: {response_json.get('error', 'No error message')}", file=os.sys.stderr)
            return False, f"[{endpoint_name}] API returned error status {response.status_code}: {response_json.get('error', 'No error message')}"
    except requests.exceptions.RequestException as e:
        print(f"[{endpoint_name}] Network or request error: {e}", file=os.sys.stderr)
        return False, f"[{endpoint_name}] Network or request error: {e}"
    except json.JSONDecodeError:
        print(f"[{endpoint_name}] Invalid JSON response.", file=os.sys.stderr)
        return False, f"[{endpoint_name}] Invalid JSON response."
    except Exception as e:
        print(f"[{endpoint_name}] Unexpected error during test: {e}", file=os.sys.stderr)
        return False, f"[{endpoint_name}] Unexpected error during test: {e}"

# Global variable to track consecutive successes for logarithmic backoff
consecutive_api_successes = 0

# Configuration
VIDEOSTREAM_URL = "http://127.0.0.1:8003/frame"
# JS_DCT_URL = "http://127.0.0.1:3000/dct" # DISABLED: Persistent issues, not critical for core goal
# JS_IDCT_URL = "http://127.0.0.1:3000/idct" # DISABLED: Persistent issues, not critical for core goal
SCIPY_DCT_URL = "http://127.0.0.1:8001/dct"
SCIPY_IDCT_URL = "http://127.0.0.1:8001/idct"
NUMPY_FFT_URL = "http://127.0.0.1:8002/fft2"
NUMPY_IFFT_URL = "http://127.0.0.1:8002/ifft2"

NUM_FRAMES_TO_PROCESS = 10 # Process around 10 frames (reduced for faster execution)

# Grid Search Parameters
# Original resolution is 3840x1080. Starting with approx 1/10th pixels.
RESOLUTIONS = [
    (1280, 360), # Approx 1/10th pixels of 3840x1080
    (640, 180),
    (320, 90),
    (160, 45)
]
BLOCK_SIZES = [8, 16, 32] # Common block sizes

# Ensure output directories exist
os.makedirs("benchmark_results", exist_ok=True)
os.makedirs("benchmark_plots", exist_ok=True)

def fetch_frame():
    try:
        print("  [benchmark_dct] Fetching frame...", file=os.sys.stderr)
        response = requests.get(VIDEOSTREAM_URL, timeout=5)
        response.raise_for_status()
        print("  [benchmark_dct] Frame fetched successfully.", file=os.sys.stderr)
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"  [benchmark_dct] Error fetching frame: {e}", file=os.sys.stderr) # Print to stderr
        return None

def process_frame(frame_data, target_width, target_height):
    try:
        print("  [benchmark_dct] Processing frame...", file=os.sys.stderr)
        # Decode JPEG to OpenCV image
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print("  [benchmark_dct] Error: cv2.imdecode returned None.", file=os.sys.stderr)
            return None

        # Resize using Lanczos interpolation
        resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Convert to grayscale
        gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        print("  [benchmark_dct] Frame processed successfully.", file=os.sys.stderr)
        return gray_img
    except Exception as e:
        print(f"  [benchmark_dct] Error processing frame: {e}", file=os.sys.stderr)
        return None

def run_dct_benchmark():
    results = []

    total_configurations = len(RESOLUTIONS) * len(BLOCK_SIZES)
    with tqdm(total=total_configurations * NUM_FRAMES_TO_PROCESS, desc="Overall Benchmark Progress") as pbar_overall:
        for res_width, res_height in RESOLUTIONS:
            for block_size in BLOCK_SIZES:
                if res_width % block_size != 0 or res_height % block_size != 0:
                    print(f"[benchmark_dct] Skipping resolution {res_width}x{res_height} with block size {block_size} (not divisible).", file=os.sys.stderr)
                    pbar_overall.update(NUM_FRAMES_TO_PROCESS) # Update progress for skipped config
                    continue

                print(f"[benchmark_dct] Benchmarking Resolution: {res_width}x{res_height}, Block Size: {block_size}")
                
                dct_times = {'scipy': [], 'numpy': []}
                idct_times = {'scipy': [], 'numpy': []}
                reconstruction_errors = {'scipy': [], 'numpy': []}

                for i in range(NUM_FRAMES_TO_PROCESS):
                    print(f"[benchmark_dct]   Processing frame {i+1}/{NUM_FRAMES_TO_PROCESS} for {res_width}x{res_height} with block size {block_size}")
                    frame_data = fetch_frame()
                    if frame_data is None:
                        print("[benchmark_dct] Failed to fetch frame, stopping benchmark for current config.", file=os.sys.stderr)
                        pbar_overall.update(NUM_FRAMES_TO_PROCESS - i) # Update remaining progress for failed config
                        break

                    gray_img = process_frame(frame_data, res_width, res_height)
                    if gray_img is None:
                        print("[benchmark_dct] Failed to process frame, stopping benchmark for current config.", file=os.sys.stderr)
                        pbar_overall.update(NUM_FRAMES_TO_PROCESS - i) # Update remaining progress for failed config
                        break

                    # Iterate through blocks
                    num_blocks_x = res_width // block_size
                    num_blocks_y = res_height // block_size
                    
                    for y_block in range(num_blocks_y):
                        for x_block in range(num_blocks_x):
                            x = x_block * block_size
                            y = y_block * block_size
                            block = gray_img[y:y+block_size, x:x+block_size]
                            block_list = block.tolist() # For JSON serialization

                            # SciPy DCT/IDCT
                            global consecutive_api_successes
                            log_this_api_call = True
                            if consecutive_api_successes > 0:
                                probability = 1.0 / math.log(consecutive_api_successes + 2)
                                if random.random() > probability:
                                    log_this_api_call = False

                            try:
                                if log_this_api_call: print(f"  [benchmark_dct] Sending DCT request to SciPy server for block ({x_block}, {y_block})", file=os.sys.stderr)
                                start_time = time.perf_counter()
                                success, msg = test_api_endpoint(SCIPY_DCT_URL, {"data": block_list}, float, "SciPy DCT", log_success=log_this_api_call)
                                if not success:
                                    consecutive_api_successes = 0
                                    print(f"[benchmark_dct] SciPy DCT/IDCT error for block ({x_block}, {y_block}): {msg}", file=os.sys.stderr)
                                    continue # Skip to next block
                                dct_coeffs = requests.post(SCIPY_DCT_URL, json={"data": block_list}).json()["result"]
                                dct_times['scipy'].append(time.perf_counter() - start_time)
                                if log_this_api_call: print(f"  [benchmark_dct] SciPy DCT successful. Response status: 200", file=os.sys.stderr)

                                if log_this_api_call: print(f"  [benchmark_dct] Sending IDCT request to SciPy server for block ({x_block}, {y_block})", file=os.sys.stderr)
                                start_time = time.perf_counter()
                                success, msg = test_api_endpoint(SCIPY_IDCT_URL, {"data": dct_coeffs}, float, "SciPy IDCT", log_success=log_this_api_call)
                                if not success:
                                    consecutive_api_successes = 0
                                    print(f"[benchmark_dct] SciPy DCT/IDCT error for block ({x_block}, {y_block}): {msg}", file=os.sys.stderr)
                                    continue # Skip to next block
                                reconstructed_block = np.array(requests.post(SCIPY_IDCT_URL, json={"data": dct_coeffs}).json()["result"])
                                idct_times['scipy'].append(time.perf_counter() - start_time)
                                if log_this_api_call: print(f"  [benchmark_dct] SciPy IDCT successful. Response status: 200", file=os.sys.stderr)

                                error = np.mean((block - reconstructed_block)**2)
                                reconstruction_errors['scipy'].append(error)
                                consecutive_api_successes += 1

                            except Exception as e:
                                print(f"[benchmark_dct] SciPy DCT/IDCT error for block ({x_block}, {y_block}): {e}", file=os.sys.stderr)
                                consecutive_api_successes = 0

                            # NumPy FFT/IFFT (as a comparison)
                            log_this_api_call = True
                            if consecutive_api_successes > 0:
                                probability = 1.0 / math.log(consecutive_api_successes + 2)
                                if random.random() > probability:
                                    log_this_api_call = False

                            try:
                                if log_this_api_call: print(f"  [benchmark_dct] Sending FFT request to NumPy server for block ({x_block}, {y_block})", file=os.sys.stderr)
                                start_time = time.perf_counter()
                                success, msg = test_api_endpoint(NUMPY_FFT_URL, {"data": block_list}, str, "NumPy FFT", log_success=log_this_api_call)
                                if not success:
                                    consecutive_api_successes = 0
                                    print(f"[benchmark_dct] NumPy FFT/IFFT error for block ({x_block}, {y_block}): {msg}", file=os.sys.stderr)
                                    continue # Skip to next block
                                fft_coeffs_raw = requests.post(NUMPY_FFT_URL, json={"data": block_list}).json()["result"]
                                # Convert list of lists of complex number strings to numpy array of complex numbers
                                fft_coeffs = np.array(fft_coeffs_raw, dtype=complex)
                                dct_times['numpy'].append(time.perf_counter() - start_time) # Renaming for consistency
                                if log_this_api_call: print(f"  [benchmark_dct] NumPy FFT successful. Response status: 200", file=os.sys.stderr)

                                if log_this_api_call: print(f"  [benchmark_dct] Sending IFFT request to NumPy server for block ({x_block}, {y_block})", file=os.sys.stderr)
                                start_time = time.perf_counter()
                                # Send complex numbers as a list of lists to the server
                                success, msg = test_api_endpoint(NUMPY_IFFT_URL, json={"data": fft_coeffs.astype(str).tolist()}, expected_output_type=float, endpoint_name="NumPy IFFT", log_success=log_this_api_call)
                                if not success:
                                    consecutive_api_successes = 0
                                    print(f"[benchmark_dct] NumPy FFT/IFFT error for block ({x_block}, {y_block}): {msg}", file=os.sys.stderr)
                                    continue # Skip to next block
                                reconstructed_block = np.array(requests.post(NUMPY_IFFT_URL, json={"data": fft_coeffs.astype(str).tolist()}).json()["result"])
                                idct_times['numpy'].append(time.perf_counter() - start_time) # Renaming for consistency
                                if log_this_api_call: print(f"  [benchmark_dct] NumPy IFFT successful. Response status: 200", file=os.sys.stderr)

                                error = np.mean((block - reconstructed_block)**2)
                                reconstruction_errors['numpy'].append(error)
                                consecutive_api_successes += 1

                            except Exception as e:
                                print(f"[benchmark_dct] NumPy FFT/IFFT error for block ({x_block}, {y_block}): {e}", file=os.sys.stderr)
                                consecutive_api_successes = 0
                    pbar_overall.update(1) # Update progress for each frame processed

                # Aggregate results for this configuration
                for impl in dct_times.keys():
                    if dct_times[impl]: # Only add if data exists
                        results.append({
                            "resolution": f"{res_width}x{res_height}",
                            "block_size": block_size,
                            "implementation": impl,
                            "avg_dct_time_ms": np.mean(dct_times[impl]) * 1000,
                            "avg_idct_time_ms": np.mean(idct_times[impl]) * 1000,
                            "avg_reconstruction_error": np.mean(reconstruction_errors[impl])
                        })
    return results

def visualize_results(results):
    if not results:
        print("No benchmark results to visualize.", file=os.sys.stderr)
        return

    try:
        df = pd.DataFrame(results)
        print("DataFrame columns:", df.columns.tolist(), file=os.sys.stderr)
        print("First 5 rows of DataFrame:\n", df.head(), file=os.sys.stderr)
    except Exception as e:
        print(f"Error creating DataFrame: {e}", file=os.sys.stderr)
        return

    # Plotting average DCT time
    plt.figure(figsize=(12, 8))
    sns.barplot(x="resolution", y="avg_dct_time_ms", hue="implementation", data=df, errorbar="sd")
    plt.title("Average DCT Time by Resolution and Implementation")
    plt.xlabel("Resolution")
    plt.ylabel("Average DCT Time (ms)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("benchmark_plots/avg_dct_time_resolution.png")
    plt.close()

    plt.figure(figsize=(12, 8))
    sns.barplot(x="block_size", y="avg_dct_time_ms", hue="implementation", data=df, errorbar="sd")
    plt.title("Average DCT Time by Block Size and Implementation")
    plt.xlabel("Block Size")
    plt.ylabel("Average DCT Time (ms)")
    plt.tight_layout()
    plt.savefig("benchmark_plots/avg_dct_time_block_size.png")
    plt.close()

    # Plotting average IDCT time
    plt.figure(figsize=(12, 8))
    sns.barplot(x="resolution", y="avg_idct_time_ms", hue="implementation", data=df, errorbar="sd")
    plt.title("Average IDCT Time by Resolution and Implementation")
    plt.xlabel("Resolution")
    plt.ylabel("Average IDCT Time (ms)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("benchmark_plots/avg_idct_time_resolution.png")
    plt.close()

    plt.figure(figsize=(12, 8))
    sns.barplot(x="block_size", y="avg_idct_time_ms", hue="implementation", data=df, errorbar="sd")
    plt.title("Average IDCT Time by Block Size and Implementation")
    plt.xlabel("Block Size")
    plt.ylabel("Average IDCT Time (ms)")
    plt.tight_layout()
    plt.savefig("benchmark_plots/avg_idct_time_block_size.png")
    plt.close()

    # Plotting average Reconstruction Error
    plt.figure(figsize=(12, 8))
    sns.barplot(x="resolution", y="avg_reconstruction_error", hue="implementation", data=df, errorbar="sd")
    plt.title("Average Reconstruction Error by Resolution and Implementation")
    plt.xlabel("Resolution")
    plt.ylabel("Average Reconstruction Error (MSE)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("benchmark_plots/avg_reconstruction_error_resolution.png")
    plt.close()

    plt.figure(figsize=(12, 8))
    sns.barplot(x="block_size", y="avg_reconstruction_error", hue="implementation", data=df, errorbar="sd")
    plt.title("Average Reconstruction Error by Block Size and Implementation")
    plt.xlabel("Block Size")
    plt.ylabel("Average Reconstruction Error (MSE)")
    plt.tight_layout()
    plt.savefig("benchmark_plots/avg_reconstruction_error_block_size.png")
    plt.close()

def generate_report(results):
    report_content = "# DCT Benchmark Report\n\n"
    report_content += "This report summarizes the performance benchmark of different DCT implementations.\n\n"
    report_content += "## Configuration\n"
    report_content += f"- Number of frames processed per configuration: {NUM_FRAMES_TO_PROCESS}\n"
    report_content += f"- Resolutions tested: {RESOLUTIONS}\n"
    report_content += f"- Block sizes tested: {BLOCK_SIZES}\n\n"

    report_content += "## Raw Results\n"
    report_content += "```json\n"
    report_content += json.dumps(results, indent=2)
    report_content += "\n```\n\n"

    report_content += "## Visualizations\n"
    report_content += "### Average DCT Time by Resolution\n"
    report_content += "![Average DCT Time by Resolution](benchmark_plots/avg_dct_time_resolution.png)\n\n"
    report_content += "### Average DCT Time by Block Size\n"
    report_content += "![Average DCT Time by Block Size](benchmark_plots/avg_dct_time_block_size.png)\n\n"
    report_content += "### Average IDCT Time by Resolution\n"
    report_content += "![Average IDCT Time by Resolution](benchmark_plots/avg_idct_time_resolution.png)\n\n"
    report_content += "### Average IDCT Time by Block Size\n"
    report_content += "![Average IDCT Time by Block Size](benchmark_plots/avg_idct_time_block_size.png)\n\n"
    report_content += "### Average Reconstruction Error by Resolution\n"
    report_content += "![Average Reconstruction Error by Resolution](benchmark_plots/avg_reconstruction_error_resolution.png)\n\n"
    report_content += "### Average Reconstruction Error by Block Size\n"
    report_content += "![Average Reconstruction Error by Block Size](benchmark_plots/avg_reconstruction_error_block_size.png)\n\n"

    with open("benchmark_results/DCT_Benchmark_Report.md", "w") as f:
        f.write(report_content)

if __name__ == "__main__":
    print("Starting DCT benchmark...")
    all_results = run_dct_benchmark()
    
    with open("benchmark_results/raw_benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Raw results saved to benchmark_results/raw_benchmark_results.json")

    print("Generating visualizations...")
    visualize_results(all_results)
    print("Plots saved to benchmark_plots/")

    print("Generating report...")
    generate_report(all_results)
    print("Benchmark complete.")
