import requests
import json
import numpy as np

# Define the URLs for the functional services
DCT_SERVICE_URL = "http://localhost:5002"
ACCUMULATOR_SERVICE_URL = "http://localhost:5005"

def get_processed_frame_logic():
    """
    Retrieves the currently accumulated frame data, performs inverse DCT,
    and returns the reconstructed image data.
    """
    # Get the accumulated frame data
    accumulated_response = requests.get(f"{ACCUMULATOR_SERVICE_URL}/get_accumulated_frame")
    accumulated_response.raise_for_status()
    accumulated_data = accumulated_response.json().get('accumulated_frame')

    if not accumulated_data:
        return {"status": "no accumulated data"}

    # Perform inverse DCT on the accumulated data
    # We need a dummy frame_id for the IDCT service
    idct_response = requests.post(f"{DCT_SERVICE_URL}/inverse_dct", json={'frame_id': 'accumulated', 'dct_data': accumulated_data})
    idct_response.raise_for_status()
    image_data = idct_response.json().get('image_data')

    return {"status": "success", "image_data": image_data}
