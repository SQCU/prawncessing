import pytest
from unittest.mock import patch, MagicMock
from cors_debug_mesh.videostream_service import monitor_usage

def test_monitor_usage_decorator():
    # Mock the function to be decorated
    mock_func = MagicMock()

    # Decorate the mock function
    decorated_func = monitor_usage(mock_func)

    # Mock psutil and logging
    with patch('cors_debug_mesh.videostream_service.psutil.Process') as mock_process, \
         patch('cors_debug_mesh.videostream_service.logging.info') as mock_logging_info:
        
        # Configure the mock process to return specific values
        mock_process.return_value.cpu_percent.return_value = 50.0
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB

        # Call the decorated function
        decorated_func()

        # Assert that the original function was called
        mock_func.assert_called_once()

        # Assert that logging.info was called with the correct message
        mock_logging_info.assert_called_once_with("CPU Usage: 50.0% | Memory Usage: 100.00 MB")

