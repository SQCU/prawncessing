import unittest
import numpy as np
from accumulator_service import _accumulate

class TestAccumulatorService(unittest.TestCase):

    def test_accumulate_first_part(self):
        new_part = np.array([1.0, 2.0, 3.0])
        new_part_str = ",".join(map(str, new_part))

        accumulated_str = _accumulate(None, new_part_str)
        accumulated_array = np.fromstring(accumulated_str, sep=',')

        self.assertTrue(np.allclose(accumulated_array, new_part))

    def test_accumulate_multiple_parts_same_size(self):
        current_data = np.array([1.0, 2.0, 3.0])
        new_part = np.array([0.5, 1.0, 1.5])
        expected_accumulation = current_data + new_part

        current_data_str = ",".join(map(str, current_data))
        new_part_str = ",".join(map(str, new_part))

        accumulated_str = _accumulate(current_data_str, new_part_str)
        accumulated_array = np.fromstring(accumulated_str, sep=',')

        self.assertTrue(np.allclose(accumulated_array, expected_accumulation))

    def test_accumulate_multiple_parts_different_size(self):
        current_data = np.array([1.0, 2.0])
        new_part = np.array([0.5, 1.0, 1.5, 2.0])
        
        # Expected behavior: smaller array is padded with zeros
        padded_current_data = np.pad(current_data, (0, len(new_part) - len(current_data)), 'constant')
        expected_accumulation = padded_current_data + new_part

        current_data_str = ",".join(map(str, current_data))
        new_part_str = ",".join(map(str, new_part))

        accumulated_str = _accumulate(current_data_str, new_part_str)
        accumulated_array = np.fromstring(accumulated_str, sep=',')

        self.assertTrue(np.allclose(accumulated_array, expected_accumulation))

    def test_accumulate_with_empty_new_part(self):
        current_data = np.array([1.0, 2.0, 3.0])
        new_part = np.array([])
        expected_accumulation = current_data # Should remain unchanged if new_part is empty after padding

        current_data_str = ",".join(map(str, current_data))
        new_part_str = ",".join(map(str, new_part))

        accumulated_str = _accumulate(current_data_str, new_part_str)
        accumulated_array = np.fromstring(accumulated_str, sep=',')
        
        # Pad expected_accumulation to match the length of accumulated_array if new_part was empty
        if len(new_part) == 0 and len(current_data) > 0:
            expected_accumulation = np.pad(expected_accumulation, (0, len(accumulated_array) - len(expected_accumulation)), 'constant')

        self.assertTrue(np.allclose(accumulated_array, expected_accumulation))

if __name__ == '__main__':
    unittest.main()