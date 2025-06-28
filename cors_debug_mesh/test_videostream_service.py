import pytest
from cors_debug_mesh.videostream_service import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_video_feed(client):
    """Test the /video endpoint to ensure it returns a multipart JPEG stream."""
    response = client.get('/video')
    
    assert response.status_code == 200
    assert 'multipart/x-mixed-replace; boundary=frame' in response.content_type
    
    # Check that the response contains some data
    assert len(response.data) > 0