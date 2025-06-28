import pytest
import requests
from PIL import Image, ImageDraw
import io

# Service endpoints
ECHO_URL = "http://localhost:5010/echo"
VIDEO_URL = "http://localhost:5001/video"

def create_test_image(width=100, height=100, color='red'):
    """Creates a simple image for testing."""
    image = Image.new('RGB', (width, height), color)
    byte_io = io.BytesIO()
    image.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io

def test_echo_service_contract():
    """
    Tests the contract of the echo service.
    It should accept a PNG image and return a modified PNG image.
    """
    image_bytes = create_test_image()
    files = {'image': ('test.png', image_bytes, 'image/png')}
    
    try:
        response = requests.post(ECHO_URL, files=files, timeout=5)
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Connection to echo service failed: {e}")

    # 1. Check status code and content type
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/png'

    # 2. Check if the response is a valid image
    try:
        returned_image = Image.open(io.BytesIO(response.content))
        returned_image.verify()  # Verify that it is a valid image
    except Exception as e:
        pytest.fail(f"The response from the echo service was not a valid image: {e}")

    # 3. Check if the image was modified (by checking for pink stripes)
    has_pink = False
    pink_color = (255, 192, 203)
    returned_image = Image.open(io.BytesIO(response.content)) # Re-open after verify
    for x in range(returned_image.width):
        for y in range(returned_image.height):
            if returned_image.getpixel((x, y))[:3] == pink_color:
                has_pink = True
                break
        if has_pink:
            break
    assert has_pink, "The returned image should have pink stripes, indicating it was processed."


def test_videostream_service_contract():
    """
    Tests the contract of the videostream service.
    It should return a multipart JPEG stream.
    """
    try:
        response = requests.get(VIDEO_URL, stream=True, timeout=5)
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Connection to videostream service failed: {e}")

    # 1. Check status code and content type
    assert response.status_code == 200
    assert 'multipart/x-mixed-replace' in response.headers['Content-Type']

    # 2. Check if the stream contains valid JPEG images
    content = response.content
    boundary = b'--frame'
    if boundary in content:
        parts = content.split(boundary)
        # The first part is empty, the second part contains the headers and image
        if len(parts) > 1 and b'Content-Type: image/jpeg' in parts[1]:
            image_data_parts = parts[1].split(b'\r\n\r\n')
            if len(image_data_parts) > 1:
                image_bytes = image_data_parts[1].strip() # Strip trailing whitespace/newlines
                try:
                    img = Image.open(io.BytesIO(image_bytes))
                    assert img.format == 'JPEG'
                    # If we get one valid JPEG, the contract is met.
                    return
                except Exception as e:
                    pytest.fail(f"Stream did not contain a valid JPEG image: {e}")

    pytest.fail("Did not receive a valid JPEG frame from the video stream.")

