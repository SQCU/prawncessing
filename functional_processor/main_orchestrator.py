import requests
import json
import time

# Service URLs
IMAGE_INPUT_SERVICE = "http://localhost:5001"
DCT_SERVICE = "http://localhost:5002"
REFERENCE_FRAME_SERVICE = "http://localhost:5003"
DIFFERENCE_SERVICE = "http://localhost:5004"
ACCUMULATOR_SERVICE = "http://localhost:5005"
OUTPUT_SERVICE = "http://localhost:5006"

# Simple memoization cache for DCT results
dct_cache = {}

def process_video_frame(frame_id, frame_data):
    print(f"Orchestrator: Processing frame {frame_id}")

    # 1. Send frame to Image Input Service
    response = requests.post(f"{IMAGE_INPUT_SERVICE}/input_frame", json={"frame_id": frame_id, "frame_data": frame_data})
    print(f"Image Input Service response: {response.json()}")

    # 2. Perform Forward DCT (with memoization)
    if frame_id in dct_cache:
        dct_data = dct_cache[frame_id]
        print(f"Forward DCT for frame {frame_id} retrieved from cache.")
    else:
        response = requests.post(f"{DCT_SERVICE}/forward_dct", json={"frame_id": frame_id, "image_data": frame_data})
        dct_data = response.json().get("dct_data")
        dct_cache[frame_id] = dct_data # Store in cache
        print(f"Forward DCT Service response: {response.json()}")

    # 3. Get Reference Frame (for simplicity, let's assume it's already set or we set it once)
    # In a real scenario, you might have logic to update the reference frame
    response = requests.get(f"{REFERENCE_FRAME_SERVICE}/get_reference_frame")
    reference_dct_data = response.json().get("reference_frame")
    print(f"Reference Frame Service response: {response.json()}")

    # If no reference frame is set, set the first frame's DCT as reference
    if not reference_dct_data:
        print(f"No reference frame found. Setting current frame {frame_id} as reference.")
        requests.post(f"{REFERENCE_FRAME_SERVICE}/set_reference_frame", json={"frame_data": dct_data})
        reference_dct_data = dct_data # Set for current processing

    # 4. Calculate Difference
    response = requests.post(f"{DIFFERENCE_SERVICE}/calculate_difference", json={"dct1": dct_data, "dct2": reference_dct_data})
    difference_data = response.json().get("difference_data")
    print(f"Difference Service response: {response.json()}")

    # 5. Accumulate Frame
    response = requests.post(f"{ACCUMULATOR_SERVICE}/accumulate_frame", json={"frame_part": difference_data})
    print(f"Accumulator Service response: {response.json()}")

    # 6. Get Accumulated Frame and Display (simplified for demo)
    response = requests.get(f"{ACCUMULATOR_SERVICE}/get_accumulated_frame")
    final_frame_data = response.json().get("accumulated_frame")
    print(f"Accumulated Frame: {final_frame_data}")

    response = requests.post(f"{OUTPUT_SERVICE}/display_video", json={"video_data": final_frame_data})
    print(f"Output Service response: {response.json()}")

if __name__ == '__main__':
    # Example usage: Simulate processing a few frames
    for i in range(1, 3):
        mock_frame_data = f"frame_content_{i}"
        process_video_frame(i, mock_frame_data)
        time.sleep(1) # Simulate time between frames
