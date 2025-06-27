import requests
import json
import numpy as np

# Define the URLs for the functional services
DCT_SERVICE_URL = "http://localhost:5002"
REFERENCE_FRAME_SERVICE_URL = "http://localhost:5003"

def set_reference_logic(image_data: str):
    """
    Sets the reference frame for the processing pipeline.
    Expects 'image_data' in the request body.
    """
    if not image_data:
        raise ValueError("Invalid request: 'image_data' is required.")

    # First, perform forward DCT on the image data to get the reference frame in DCT domain
    dct_response = requests.post(f"{DCT_SERVICE_URL}/forward_dct", json={'frame_id': 'reference', 'image_data': image_data})
    dct_response.raise_for_status()
    reference_dct_data = dct_response.json().get('dct_data')

    # Then, set this DCT data as the reference frame
    set_ref_response = requests.post(f"{REFERENCE_FRAME_SERVICE_URL}/set_reference_frame", json={'frame_data': reference_dct_data})
    set_ref_response.raise_for_status()

    return {"status": "reference frame set"}
