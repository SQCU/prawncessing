
import time
import requests
import base64
import os

# It's a good practice to define constants for URLs and file paths
# to make the code cleaner and easier to maintain.
PROXY_URL = "http://localhost:5008/api/v1/process-frame"
IMAGE_PATH = "ref.PNG"

def test_proxy_orchestration():
    """
    This test verifies the end-to-end functionality of the proxy server's
    orchestration logic. It sends a sample image to the proxy's public
    endpoint and expects a processed image in return, confirming that the
    entire backend service chain is working correctly.
    """
    # Give the services a moment to start up
    time.sleep(1)

    # 1. Load the sample input image
    # We check if the image exists to provide a clear error message if it's missing.
    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError(
            f"The test image '{IMAGE_PATH}' was not found. "
            "Please ensure the image exists in the root directory."
        )

    with open(IMAGE_PATH, "rb") as image_file:
        # 2. Encode the image data as a Base64 string
        # This is a standard way to transmit binary data in JSON payloads.
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    # 3. Make a POST request to the proxy's public endpoint
    # The payload is a JSON object with the image data.
    payload = {"image": image_data}
    
    print(f"Sending request to {PROXY_URL} with image: {IMAGE_PATH}")

    try:
        response = requests.post(PROXY_URL, json=payload)

        # 4. Assert that the HTTP response code is 200 OK
        # This is the primary check for success.
        assert response.status_code == 200, (
            f"Expected status code 200, but got {response.status_code}. "
            f"Response: {response.text}"
        )

        # 5. Assert that the response content is a valid image
        # We check for a non-empty content-type and content.
        assert response.headers.get('Content-Type'), (
            "Response is missing the 'Content-Type' header."
        )
        assert response.content, "Response content is empty."

        print("Test passed: Received a successful response with image data.")

        # Optional: Save the processed image for manual verification
        # This can be useful for debugging the image processing logic.
        output_image_path = "processed_test_image.png"
        with open(output_image_path, "wb") as f:
            f.write(response.content)
        print(f"Processed image saved to {output_image_path}")

    except requests.exceptions.RequestException as e:
        # This block catches network-related errors, such as the server not being reachable.
        assert False, f"An error occurred while communicating with the proxy: {e}"

if __name__ == "__main__":
    # This allows the script to be run directly from the command line.
    test_proxy_orchestration()
