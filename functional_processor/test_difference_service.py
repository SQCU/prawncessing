import unittest
import numpy as np
from difference_service import _calculate_dct_difference

class TestDifferenceService(unittest.TestCase):

    def test_calculate_difference_same_size(self):
        dct1 = np.array([1.0, 2.0, 3.0, 4.0])
        dct2 = np.array([0.5, 1.0, 1.5, 2.0])
        expected_diff = dct1 - dct2

        dct1_str = ",".join(map(str, dct1))
        dct2_str = ",".join(map(str, dct2))

        actual_diff_str = _calculate_dct_difference(dct1_str, dct2_str)
        actual_diff = np.fromstring(actual_diff_str, sep=',')

        self.assertTrue(np.allclose(actual_diff, expected_diff))

    def test_calculate_difference_different_size(self):
        dct1 = np.array([1.0, 2.0, 3.0])
        dct2 = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
        
        # Expected behavior: smaller array is padded with zeros
        padded_dct1 = np.pad(dct1, (0, len(dct2) - len(dct1)), 'constant')
        expected_diff = padded_dct1 - dct2

        dct1_str = ",".join(map(str, dct1))
        dct2_str = ",".join(map(str, dct2))

        actual_diff_str = _calculate_dct_difference(dct1_str, dct2_str)
        actual_diff = np.fromstring(actual_diff_str, sep=',')

        self.assertTrue(np.allclose(actual_diff, expected_diff))

    def test_calculate_difference_empty_arrays(self):
        dct1 = np.array([])
        dct2 = np.array([])
        expected_diff = np.array([])

        dct1_str = ",".join(map(str, dct1))
        dct2_str = ",".join(map(str, dct2))

        actual_diff_str = _calculate_dct_difference(dct1_str, dct2_str)
        actual_diff = np.fromstring(actual_diff_str, sep=',')

        self.assertTrue(np.allclose(actual_diff, expected_diff))

    def test_calculate_difference_one_empty_array(self):
        dct1 = np.array([1.0, 2.0])
        dct2 = np.array([])
        
        # Expected behavior: smaller array is padded with zeros
        padded_dct2 = np.pad(dct2, (0, len(dct1) - len(dct2)), 'constant')
        expected_diff = dct1 - padded_dct2

        dct1_str = ",".join(map(str, dct1))
        dct2_str = ",".join(map(str, dct2))

        actual_diff_str = _calculate_dct_difference(dct1_str, dct2_str)
        actual_diff = np.fromstring(actual_diff_str, sep=',')

        self.assertTrue(np.allclose(actual_diff, expected_diff))

if __name__ == '__main__':
    unittest.main()