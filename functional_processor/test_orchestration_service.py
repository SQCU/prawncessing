import unittest
from unittest.mock import patch, MagicMock
import json
import numpy as np
from orchestration_service import app
from frame_processor import process_frame_logic, DCT_SERVICE_URL, REFERENCE_FRAME_SERVICE_URL, DIFFERENCE_SERVICE_URL, ACCUMULATOR_SERVICE_URL
from output_retriever import get_processed_frame_logic
from reference_manager import set_reference_logic

class TestOrchestrationService(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('requests.post')
    @patch('requests.get')
    def test_process_frame_with_reference(self, mock_get, mock_post):
        # Mock DCT service response for forward_dct
        mock_dct_fwd_response = MagicMock()
        mock_dct_fwd_response.status_code = 200
        mock_dct_fwd_response.json.return_value = {'dct_data': ",".join(map(str, np.array([0.1, 0.2])))}
        mock_post.return_value = mock_dct_fwd_response

        # Mock Reference Frame service response for get_reference_frame
        mock_ref_get_response = MagicMock()
        mock_ref_get_response.status_code = 200
        mock_ref_get_response.json.return_value = {'reference_frame': ",".join(map(str, np.array([0.05, 0.1])))}
        mock_get.return_value = mock_ref_get_response

        # Mock Difference service response
        mock_diff_response = MagicMock()
        mock_diff_response.status_code = 200
        mock_diff_response.json.return_value = {'difference_data': ",".join(map(str, np.array([0.05, 0.1])))}
        mock_post.side_effect = [mock_dct_fwd_response, mock_diff_response, MagicMock(status_code=200)] # Order matters for side_effect

        # Mock Accumulator service response
        mock_accumulate_response = MagicMock()
        mock_accumulate_response.status_code = 200

        # Adjust side_effect for mock_post to handle multiple calls correctly
        # First call: DCT forward, Second call: Difference, Third call: Accumulate
        mock_post.side_effect = [
            mock_dct_fwd_response, # for /forward_dct
            mock_diff_response,    # for /calculate_difference
            mock_accumulate_response # for /accumulate_frame
        ]

        response = self.app.post('/process_frame', data=json.dumps({'frame_id': '1', 'image_data': '1,2'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'status': 'frame processed', 'frame_id': '1'})

        # Verify calls
        mock_post.assert_any_call(f"{DCT_SERVICE_URL}/forward_dct", json={'frame_id': '1', 'image_data': '1,2'})
        mock_get.assert_any_call(f"{REFERENCE_FRAME_SERVICE_URL}/get_reference_frame")
        mock_post.assert_any_call(f"{DIFFERENCE_SERVICE_URL}/calculate_difference", json={'dct1': ",".join(map(str, np.array([0.1, 0.2]))), 'dct2': ",".join(map(str, np.array([0.05, 0.1])))})
        mock_post.assert_any_call(f"{ACCUMULATOR_SERVICE_URL}/accumulate_frame", json={'frame_part': ",".join(map(str, np.array([0.05, 0.1])))})

    @patch('requests.post')
    @patch('requests.get')
    def test_process_frame_no_reference(self, mock_get, mock_post):
        # Mock DCT service response for forward_dct
        mock_dct_fwd_response = MagicMock()
        mock_dct_fwd_response.status_code = 200
        mock_dct_fwd_response.json.return_value = {'dct_data': ",".join(map(str, np.array([0.1, 0.2])))}

        # Mock Reference Frame service response for get_reference_frame (no reference)
        mock_ref_get_response = MagicMock()
        mock_ref_get_response.status_code = 200
        mock_ref_get_response.json.return_value = {'reference_frame': None}
        mock_get.return_value = mock_ref_get_response

        # Mock Accumulator service response
        mock_accumulate_response = MagicMock()
        mock_accumulate_response.status_code = 200

        mock_post.side_effect = [
            mock_dct_fwd_response, # for /forward_dct
            mock_accumulate_response # for /accumulate_frame
        ]

        response = self.app.post('/process_frame', data=json.dumps({'frame_id': '1', 'image_data': '1,2'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'status': 'frame processed', 'frame_id': '1'})

        # Verify calls
        mock_post.assert_any_call(f"{DCT_SERVICE_URL}/forward_dct", json={'frame_id': '1', 'image_data': '1,2'})
        mock_get.assert_any_call(f"{REFERENCE_FRAME_SERVICE_URL}/get_reference_frame")
        mock_post.assert_any_call(f"{ACCUMULATOR_SERVICE_URL}/accumulate_frame", json={'frame_part': ",".join(map(str, np.array([0.1, 0.2])))})
        # Ensure difference service was NOT called

    @patch('requests.post')
    @patch('requests.get')
    def test_get_processed_frame(self, mock_get, mock_post):
        # Mock Accumulator service response
        mock_accumulated_response = MagicMock()
        mock_accumulated_response.status_code = 200
        mock_accumulated_response.json.return_value = {'accumulated_frame': ",".join(map(str, np.array([0.3, 0.4])))}
        mock_get.return_value = mock_accumulated_response

        # Mock IDCT service response
        mock_idct_response = MagicMock()
        mock_idct_response.status_code = 200
        mock_idct_response.json.return_value = {'image_data': ",".join(map(str, np.array([1.0, 2.0])))}
        mock_post.return_value = mock_idct_response

        response = self.app.get('/get_processed_frame')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'status': 'success', 'image_data': ",".join(map(str, np.array([1.0, 2.0])))})

        mock_get.assert_called_once_with(f"{ACCUMULATOR_SERVICE_URL}/get_accumulated_frame")
        expected_idct_payload = {'frame_id': 'accumulated', 'dct_data': ",".join(map(str, np.array([0.3, 0.4])))}
        mock_post.assert_called_once_with(f"{DCT_SERVICE_URL}/inverse_dct", json=expected_idct_payload)

    @patch('requests.post')
    def test_set_reference(self, mock_post):
        # Mock DCT service response for forward_dct
        mock_dct_fwd_response = MagicMock()
        mock_dct_fwd_response.status_code = 200
        mock_dct_fwd_response.json.return_value = {'dct_data': ",".join(map(str, np.array([0.1, 0.2])))}

        # Mock Reference Frame service response for set_reference_frame
        mock_set_ref_response = MagicMock()
        mock_set_ref_response.status_code = 200

        mock_post.side_effect = [
            mock_dct_fwd_response, # for /forward_dct
            mock_set_ref_response  # for /set_reference_frame
        ]

        response = self.app.post('/set_reference', data=json.dumps({'image_data': '1,2,3'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'status': 'reference frame set'})

        mock_post.assert_any_call(f"{DCT_SERVICE_URL}/forward_dct", json={'frame_id': 'reference', 'image_data': '1,2,3'})
        expected_set_ref_payload = {'frame_data': ",".join(map(str, np.array([0.1, 0.2])))}
        mock_post.assert_any_call(f"{REFERENCE_FRAME_SERVICE_URL}/set_reference_frame", json=expected_set_ref_payload)

if __name__ == '__main__':
    unittest.main()