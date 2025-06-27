import unittest
from unittest.mock import patch, MagicMock
import json
import base64
import time
import threading
import numpy as np

from image_input_service import app, VIDEOSTREAM_MOCK_SERVER_URL, ORCHESTRATION_SERVICE_URL, _is_streaming

class TestImageInputService(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Ensure streaming is off before each test
        global _is_streaming
        _is_streaming = False

    @patch('requests.post')
    @patch('requests.get')
    def test_start_stream(self, mock_get, mock_post):
        # Mock videostream_mock_server response
        mock_video_stream_response = MagicMock()
        mock_video_stream_response.status_code = 200
        mock_video_stream_response.content = b"mock_jpeg_data"
        mock_get.return_value = mock_video_stream_response

        # Mock orchestration service response
        mock_orchestration_response = MagicMock()
        mock_orchestration_response.status_code = 200
        mock_orchestration_response.json.return_value = {"status": "frame received and forwarded"}
        mock_post.return_value = mock_orchestration_response

        response = self.app.post('/start_stream')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"status": "streaming started"})

        # Give the streaming thread a moment to run
        time.sleep(0.1)
        global _is_streaming
        self.assertTrue(_is_streaming)

        # Verify that frames were fetched and forwarded
        mock_get.assert_called_with(f"{VIDEOSTREAM_MOCK_SERVER_URL}/frame")
        
        # Check that the orchestration service was called with base64 encoded data
        expected_image_data_b64 = base64.b64encode(b"mock_jpeg_data").decode('utf-8')
        mock_post.assert_called_with(f"{ORCHESTRATION_SERVICE_URL}/process_frame", json={'frame_id': 'mock_frame_1', 'image_data': expected_image_data_b64})

        # Stop the stream to clean up the thread
        self.app.post('/stop_stream')

    @patch('requests.post')
    @patch('requests.get')
    def test_stop_stream(self, mock_get, mock_post):
        # Start the stream first
        global _is_streaming
        _is_streaming = True
        # Mock responses to allow _stream_frames to run briefly
        mock_video_stream_response = MagicMock()
        mock_video_stream_response.status_code = 200
        mock_video_stream_response.content = b"mock_jpeg_data"
        mock_get.return_value = mock_video_stream_response
        mock_orchestration_response = MagicMock()
        mock_orchestration_response.status_code = 200
        mock_orchestration_response.json.return_value = {"status": "frame received and forwarded"}
        mock_post.return_value = mock_orchestration_response

        response = self.app.post('/start_stream')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"status": "streaming started"})
        time.sleep(0.1) # Give time for the streaming thread to become active

        response = self.app.post('/stop_stream')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"status": "streaming stopped"})
        self.assertFalse(_is_streaming)

    def test_get_latest_frame(self):
        # Manually set _latest_frame_data for testing
        with patch('image_input_service._latest_frame_data', 'test_frame_data'):
            with patch('image_input_service._frame_counter', 5):
                response = self.app.get('/latest_frame')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.data), {"status": "success", "latest_frame": "test_frame_data", "frame_count": 5})

if __name__ == '__main__':
    unittest.main()