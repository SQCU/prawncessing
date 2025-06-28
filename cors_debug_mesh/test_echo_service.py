import pytest
from PIL import Image, ImageDraw
import io
import random
from echo_service import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_test_image(width=100, height=100, color='blue'):
    """Creates a simple image for testing."""
    image = Image.new('RGB', (width, height), color)
    byte_io = io.BytesIO()
    image.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io

def test_echo_with_image(client):
    """Test the /echo endpoint with a valid image."""
    image_bytes = create_test_image()
    
    response = client.post('/echo', data={'image': (image_bytes, 'test.png')})
    
    assert response.status_code == 200
    
    # Check that the returned image is a PNG
    assert response.content_type == 'image/png'
    
    # Open the returned image and check its properties
    returned_image = Image.open(io.BytesIO(response.data))
    assert returned_image.format == 'PNG'
    assert returned_image.size == (100, 100)

    # Check for pink pixels (the stripes)
    has_pink = False
    pink_color = (255, 192, 203)
    for x in range(returned_image.width):
        for y in range(returned_image.height):
            if returned_image.getpixel((x, y))[:3] == pink_color:
                has_pink = True
                break
        if has_pink:
            break
    assert has_pink, "The returned image should have pink stripes."

def test_echo_no_image(client):
    """Test the /echo endpoint with no image provided."""
    response = client.post('/echo')
    assert response.status_code == 400
    assert b'No image file provided' in response.data
