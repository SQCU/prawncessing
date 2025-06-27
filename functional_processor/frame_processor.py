import requests
import json
import numpy as np

# Define the URLs for the functional services
DCT_SERVICE_URL = "http://localhost:5002"
REFERENCE_FRAME_SERVICE_URL = "http://localhost:5003"
DIFFERENCE_SERVICE_URL = "http://localhost:5004"
ACCUMULATOR_SERVICE_URL = "http://localhost:5005"

def process_frame_logic(frame_id: str, image_data: str):
    """
    Orchestrates the processing of a single video frame.
    1. Performs forward DCT on the input image.
    2. Calculates the difference with the reference frame.
    3. Accumulates the difference.
    """
    if not frame_id or not image_data:
        raise ValueError("Invalid request: 'frame_id' and 'image_data' are required.")

    # 1. Perform forward DCT
    dct_response = requests.post(f"{DCT_SERVICE_URL}/forward_dct", json={'frame_id': frame_id, 'image_data': image_data})
    dct_response.raise_for_status()
    dct_data = dct_response.json().get('dct_data')

    # Get the current reference frame
    ref_frame_response = requests.get(f"{REFERENCE_FRAME_SERVICE_URL}/get_reference_frame")
    ref_frame_response.raise_for_status()
    reference_frame_data = ref_frame_response.json().get('reference_frame')

    if reference_frame_data:
        # 2. Calculate the difference with the reference frame
        diff_response = requests.post(f"{DIFFERENCE_SERVICE_URL}/calculate_difference", json={'dct1': dct_data, 'dct2': reference_frame_data})
        diff_response.raise_for_status()
        difference_data = diff_response.json().get('difference_data')

        # 3. Accumulate the difference
        accumulate_response = requests.post(f"{ACCUMULATOR_SERVICE_URL}/accumulate_frame", json={'frame_part': difference_data})
        accumulate_response.raise_for_status()
    else:
        # If no reference frame, just accumulate the DCT data directly
        accumulate_response = requests.post(f"{ACCUMULATOR_SERVICE_URL}/accumulate_frame", json={'frame_part': dct_data})
        accumulate_response.raise_for_status()

    return {"status": "frame processed", "frame_id": frame_id}
