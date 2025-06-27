
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

app = FastAPI()

class FFTFloatRequest(BaseModel):
    data: list[list[float]]

class FFTStringRequest(BaseModel):
    data: list[list[str]]

@app.get("/")
async def read_root():
    return {"status": "ok"}

@app.post("/fft2")
async def calculate_fft2(request: FFTFloatRequest):
    """
    API Contract:
    - Request Body:
        - `data`: `list[list[float]]` - A 2D list of floats representing the input matrix.
                  Each inner list is a row. Must be a rectangular matrix.
                  Expected values are typically 0-255 (pixel intensities).
    - Response Body (Success):
        - `result`: `list[list[str]]` - A 2D list of strings, where each string represents a complex number.
                    Dimensions are the same as the input `data`.
    - Response Body (Error):
        - `error`: `str` - A string containing the error message.
    """
    try:
        # Convert list of lists to a NumPy array
        data_array = np.array(request.data)
        
        # Perform 2D FFT
        fft_result = np.fft.fft2(data_array)
        
        # FFT results are complex, convert to a format that can be JSON serialized
        # For simplicity, we'll return the real and imaginary parts separately or magnitude/phase
        # For this benchmark, we'll return a list of lists of complex numbers as strings
        # The client (benchmark_dct.py) will need to parse these back into complex numbers
        return {"result": fft_result.astype(str).tolist()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/ifft2")
async def calculate_ifft2(request: FFTStringRequest):
    """
    API Contract:
    - Request Body:
        - `data`: `list[list[str]]` - A 2D list of strings, where each string represents a complex number.
                  Each inner list is a row. Must be a rectangular matrix.
    - Response Body (Success):
        - `result`: `list[list[float]]` - A 2D list of floats representing the reconstructed matrix.
                    Dimensions are the same as the input `data`.
                    Expected values are typically 0-255 (pixel intensities).
    - Response Body (Error):
        - `error`: `str` - A string containing the error message.
    """
    try:
        # Convert list of lists to a NumPy array
        # The input data will be a list of lists of complex numbers (as strings)
        # We need to convert them back to complex numbers
        data_array = np.array(request.data, dtype=complex)
        
        # Perform 2D IFFT
        ifft_result = np.fft.ifft2(data_array)
        
        # IFFT results can have small imaginary components due to floating point inaccuracies.
        # Since the original image data is real, we take the real part.
        return {"result": ifft_result.real.astype(float).tolist()}
    except Exception as e:
        return {"error": str(e)}

