import requests
import numpy as np
import cv2
import os
import sys

VIDEOSTREAM_URL = "http://127.0.0.1:8003/frame"
JS_DCT_URL = "http://127.0.0.1:3000/dct"
JS_IDCT_URL = "http://127.0.0.1:3000/idct"

LOG_FILE = "simple_dct_test.log"

def log_message(message, level="INFO"):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{level}] {message}\n")
    # Also print to stderr for immediate visibility in case of critical errors
    if level == "ERROR":
        print(f"[{level}] {message}", file=sys.stderr)

def fetch_frame():
    try:
        response = requests.get(VIDEOSTREAM_URL, timeout=5)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching frame: {e}", level="ERROR")
        return None

def process_frame(frame_data, target_width, target_height):
    try:
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            log_message("Error: cv2.imdecode returned None.", level="ERROR")
            return None

        resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
        gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        return gray_img
    except Exception as e:
        log_message(f"Error processing frame: {e}", level="ERROR")
        return None

def run_single_dct_test():
    log_message("--- Running Single DCT Test ---")
    
    # Fetch a frame
    frame_data = fetch_frame()
    if frame_data is None:
        log_message("Failed to fetch frame. Exiting.", level="ERROR")
        return

    # Process frame to grayscale and resize to a manageable size for testing
    # Using a smaller resolution for this quick test
    test_width, test_height = 160, 45 
    gray_img = process_frame(frame_data, test_width, test_height)
    if gray_img is None:
        log_message("Failed to process frame. Exiting.", level="ERROR")
        return

    # Extract a single 8x8 block
    block_size = 8
    if test_width < block_size or test_height < block_size:
        log_message(f"Test resolution {test_width}x{test_height} is too small for block size {block_size}.", level="ERROR")
        return

    block = gray_img[0:block_size, 0:block_size]
    block_list = block.tolist()

    log_message(f"Original Block (first 8x8 pixels):\n{block}")

    # Test JavaScript DCT
    try:
        log_message("\n--- Testing JavaScript DCT/IDCT ---")
        response = requests.post(JS_DCT_URL, json={"data": block_list, "rows": block_size, "cols": block_size})
        response.raise_for_status()
        dct_coeffs = response.json()["result"]
        log_message(f"JS DCT Coefficients (first few values):{np.array(dct_coeffs).flatten()[:5]}")

        response = requests.post(JS_IDCT_URL, json={"data": dct_coeffs, "rows": block_size, "cols": block_size})
        response.raise_for_status()
        reconstructed_block = np.array(response.json()["result"])
        log_message(f"JS Reconstructed Block (first 8x8 pixels):\n{reconstructed_block}")

        error = np.mean((block - reconstructed_block)**2)
        log_message(f"JS Reconstruction Error (MSE): {error}")

    except Exception as e:
        log_message(f"Error during JavaScript DCT/IDCT test: {e}", level="ERROR")
        if hasattr(e, 'response') and e.response is not None:
            log_message(f"JS Server Response: {e.response.text}", level="ERROR")

    log_message("\n--- Single DCT Test Complete ---")

if __name__ == "__main__":
    # Clear the log file before running
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    run_single_dct_test()