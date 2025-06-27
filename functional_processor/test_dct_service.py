import unittest
import numpy as np
from scipy.fftpack import dct, idct
from dct_service import _perform_forward_dct, _perform_inverse_dct

class TestDCTService(unittest.TestCase):

    def test_forward_dct_numpy_direct(self):
        # Create a sample numpy array
        image_data = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=float)

        # Calculate the expected DCT using scipy's dct with orthogonal normalization
        expected_dct = dct(image_data, norm='ortho')

        # Perform the forward DCT using the service's internal function (after string conversion)
        dct_data_str = _perform_forward_dct(",".join(map(str, image_data)), "test_frame")
        actual_dct = np.fromstring(dct_data_str, sep=',')

        # Compare the results
        self.assertTrue(np.allclose(actual_dct, expected_dct))

    def test_inverse_dct_numpy_direct(self):
        # Create a sample DCT array
        dct_data = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=float)

        # Calculate the expected inverse DCT using scipy's idct with orthogonal normalization
        expected_image = idct(dct_data, norm='ortho')

        # Perform the inverse DCT using the service's internal function (after string conversion)
        image_data_str = _perform_inverse_dct(",".join(map(str, dct_data)), "test_frame")
        actual_image = np.fromstring(image_data_str, sep=',')

        # Compare the results
        self.assertTrue(np.allclose(actual_image, expected_image))

    def test_forward_inverse_dct_identity(self):
        # Create a sample numpy array
        original_image_data = np.random.rand(10)
        original_image_data_str = ",".join(map(str, original_image_data))

        # Perform forward DCT
        dct_data_str = _perform_forward_dct(original_image_data_str, "test_frame")

        # Perform inverse DCT
        reconstructed_image_data_str = _perform_inverse_dct(dct_data_str, "test_frame")
        reconstructed_image_data = np.fromstring(reconstructed_image_data_str, sep=",")

        # Compare the original and reconstructed data
        self.assertTrue(np.allclose(original_image_data, reconstructed_image_data))

if __name__ == '__main__':
    unittest.main()