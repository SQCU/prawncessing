
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from scipy.fftpack import dct, idct

app = FastAPI()

class DCTRequest(BaseModel):
    data: list[list[float]]

@app.get("/")
async def read_root():
    return {"status": "ok"}

@app.post("/dct")
async def calculate_dct(request: DCTRequest):
    """
    API Contract:
    - Request Body:
        - `data`: `list[list[float]]` - A 2D list of floats representing the input matrix.
                  Each inner list is a row. Must be a rectangular matrix.
                  Expected values are typically 0-255 (pixel intensities).
    - Response Body (Success):
        - `result`: `list[list[float]]` - A 2D list of floats representing the DCT coefficients.
                    Dimensions are the same as the input `data`.
    - Response Body (Error):
        - `error`: `str` - A string containing the error message.
    """
    try:
        # Convert list of lists to a NumPy array
        data_array = np.array(request.data)
        
        # Perform 2D DCT
        # Apply DCT along rows, then along columns
        dct_result = dct(dct(data_array, axis=0, norm='ortho'), axis=1, norm='ortho')
        
        return {"result": dct_result.tolist()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/idct")
async def calculate_idct(request: DCTRequest):
    """
    API Contract:
    - Request Body:
        - `data`: `list[list[float]]` - A 2D list of floats representing the DCT coefficients.
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
        data_array = np.array(request.data)
        
        # Perform 2D IDCT
        # Apply IDCT along columns, then along rows
        idct_result = idct(idct(data_array, axis=0, norm='ortho'), axis=1, norm='ortho')
        
        return {"result": idct_result.tolist()}
    except Exception as e:
        return {"error": str(e)}

