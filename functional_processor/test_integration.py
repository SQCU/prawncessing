import pytest
from playwright.sync_api import sync_playwright, expect
import subprocess
import time
import os
import signal

# Define the paths to the service scripts
SERVICE_SCRIPTS = [
    "functional_processor/image_input_service.py",
    "functional_processor/dct_service.py",
    "functional_processor/reference_frame_service.py",
    "functional_processor/difference_service.py",
    "functional_processor/accumulator_service.py",
    "functional_processor/proxy_server.py",
]

@pytest.fixture(scope="session")
def services():
    """
    Fixture to start and stop all the necessary services for the integration test.
    """
    # Kill any lingering processes before starting new ones
    subprocess.run(["./functional_processor/kill_ports.sh"], capture_output=True)
    
    processes = []
    for script in SERVICE_SCRIPTS:
        process = subprocess.Popen(["python", script])
        processes.append(process)
    
    # Give the services time to start
    time.sleep(5)
    
    yield
    
    for process in processes:
        os.kill(process.pid, signal.SIGTERM)
    
    # Kill any lingering processes after the tests are done
    subprocess.run(["./functional_processor/kill_ports.sh"], capture_output=True)

def test_end_to_end_flow(services):
    """
    An integration test that uses Playwright to simulate a client interacting
    with the system through the proxy server.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # The proxy server is running on port 5000
        proxy_url = "http://localhost:5000"

        # 1. Reset the accumulator
        response = page.request.post(f"{proxy_url}/accumulator/reset_accumulator", data={})
        expect(response).to_be_ok()

        # 2. Set a reference frame
        reference_frame_data = "1,2,3,4"
        response = page.request.post(f"{proxy_url}/reference_frame/set_reference_frame", json={"frame_data": reference_frame_data})
        expect(response).to_be_ok()

        # 3. Input a new frame
        frame_id = "test_frame_1"
        frame_data = "5,6,7,8"
        response = page.request.post(f"{proxy_url}/image_input/input_frame", json={"frame_id": frame_id, "frame_data": frame_data})
        expect(response).to_be_ok()

        # 4. Get the frame back to ensure it was stored
        response = page.request.get(f"{proxy_url}/image_input/get_frame/{frame_id}")
        expect(response).to_be_ok()
        assert response.json()["frame_data"] == frame_data

        # 5. Perform forward DCT on the input frame
        response = page.request.post(f"{proxy_url}/dct/forward_dct", json={"frame_id": frame_id, "image_data": frame_data})
        expect(response).to_be_ok()
        dct_data = response.json()["dct_data"]

        # 6. Get the reference frame's DCT (we'll just use the same dct for simplicity)
        response = page.request.post(f"{proxy_url}/dct/forward_dct", json={"frame_id": "ref_frame", "image_data": reference_frame_data})
        expect(response).to_be_ok()
        reference_dct_data = response.json()["dct_data"]

        # 7. Calculate the difference
        response = page.request.post(f"{proxy_url}/difference/calculate_difference", json={"dct1": dct_data, "dct2": reference_dct_data})
        expect(response).to_be_ok()
        difference_data = response.json()["difference_data"]

        # 8. Accumulate the difference
        response = page.request.post(f"{proxy_url}/accumulator/accumulate_frame", json={"frame_part": difference_data})
        expect(response).to_be_ok()

        # 9. Get the accumulated frame
        response = page.request.get(f"{proxy_url}/accumulator/get_accumulated_frame")
        expect(response).to_be_ok()
        assert response.json()["accumulated_frame"] is not None

        browser.close()

if __name__ == "__main__":
    pytest.main(["-s", __file__])

