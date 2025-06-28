import pytest
from playwright.sync_api import sync_playwright, expect
import subprocess
import time

@pytest.fixture(scope="module")
def services():
    p = subprocess.Popen(["./start_services.sh"], cwd="cors_debug_mesh")
    time.sleep(5) # give services time to start
    yield
    p.terminate()

def test_visualizer_shows_timestamp(services, page):
    page.goto("http://localhost:5000/visualizer.html")
    expect(page.locator("#video-stream")).to_be_visible()
