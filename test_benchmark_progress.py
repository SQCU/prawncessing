import requests
import time
import numpy as np
import cv2
import os

VIDEOSTREAM_URL = "http://127.0.0.1:8003/frame"

print("[TEST] test_benchmark_progress.py started.", flush=True)

def fetch_frame():
    try:
        response = requests.get(VIDEOSTREAM_URL, timeout=5)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"[TEST] Error fetching frame: {e}", file=os.sys.stderr, flush=True)
        return None

def process_frame(frame_data, target_width, target_height):
    try:
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print("[TEST] Error: cv2.imdecode returned None.", file=os.sys.stderr, flush=True)
            return None

        resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
        gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        return gray_img
    except Exception as e:
        print(f"[TEST] Error processing frame: {e}", file=os.sys.stderr, flush=True)
        return None

def simulate_benchmark_loop(num_frames=10, resolutions=[(1280, 360)], block_sizes=[8]):
    print("[TEST] Starting simulated benchmark loop...", flush=True)
    for res_width, res_height in resolutions:
        for block_size in block_sizes:
            if res_width % block_size != 0 or res_height % block_size != 0:
                print(f"[TEST] Skipping resolution {res_width}x{res_height} with block size {block_size} (not divisible).", flush=True)
                continue

            print(f"[TEST] Simulating for Resolution: {res_width}x{res_height}, Block Size: {block_size}", flush=True)
            for i in range(num_frames):
                print(f"[TEST]   Processing frame {i+1}/{num_frames}", flush=True)
                frame_data = fetch_frame()
                if frame_data is None:
                    print("[TEST]   Failed to fetch frame. Stopping simulation for current config.", file=os.sys.stderr, flush=True)
                    break

                gray_img = process_frame(frame_data, res_width, res_height)
                if gray_img is None:
                    print("[TEST]   Failed to process frame. Stopping simulation for current config.", file=os.sys.stderr, flush=True)
                    break

                # Simulate block processing
                num_blocks_x = res_width // block_size
                num_blocks_y = res_height // block_size
                
                for y_block in range(num_blocks_y):
                    for x_block in range(num_blocks_x):
                        # print(f"[TEST]     Processing block ({x_block}, {y_block})", flush=True)
                        # Simulate network request and processing time
                        time.sleep(0.001) 

                print(f"[TEST]   Frame {i+1} processed successfully.", flush=True)
    print("[TEST] Simulated benchmark loop finished.", flush=True)

if __name__ == "__main__":
    simulate_benchmark_loop()