import unittest
import numpy as np
from reference_frame_service import _set_reference_frame_data

class TestReferenceFrameService(unittest.TestCase):

    def test_set_reference_frame_data(self):
        # Create a sample numpy array
        frame_data = np.array([1.0, 2.0, 3.0, 4.0])
        frame_data_str = ",".join(map(str, frame_data))

        # Set the reference frame data
        set_data_str = _set_reference_frame_data(frame_data_str)
        set_data_array = np.fromstring(set_data_str, sep=',')

        # Compare the results
        self.assertTrue(np.allclose(set_data_array, frame_data))

    def test_set_reference_frame_empty_data(self):
        # Create an empty numpy array
        frame_data = np.array([])
        frame_data_str = ",".join(map(str, frame_data))

        # Set the reference frame data
        set_data_str = _set_reference_frame_data(frame_data_str)
        set_data_array = np.fromstring(set_data_str, sep=',')

        # Compare the results
        self.assertTrue(np.allclose(set_data_array, frame_data))

    def test_set_reference_frame_different_data(self):
        frame_data1 = np.array([1.0, 2.0])
        frame_data1_str = ",".join(map(str, frame_data1))
        _set_reference_frame_data(frame_data1_str)

        frame_data2 = np.array([5.0, 6.0, 7.0])
        frame_data2_str = ",".join(map(str, frame_data2))
        set_data_str = _set_reference_frame_data(frame_data2_str)
        set_data_array = np.fromstring(set_data_str, sep=',')

        self.assertTrue(np.allclose(set_data_array, frame_data2))

if __name__ == '__main__':
    unittest.main()