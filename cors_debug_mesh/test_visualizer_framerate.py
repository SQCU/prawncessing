# ======================================================================================
# VISUALIZER FRAMERATE TEST
#
# This script uses a browser automation framework (Playwright) to test the
# end-user experience of the visualizer. It embodies the following principles:
#
# 1.  **End-to-End Testing:** It tests the system from the user's perspective by
#     loading the actual visualizer.html page in a real browser engine. This
#     allows it to catch issues that might be missed by service-level tests,
#     such as client-side JavaScript errors or rendering problems.
#
# 2.  **Asynchronous Operations:** The test is written using `async/await` to
#     handle the asynchronous nature of web pages and network requests
#     efficiently.
#
# 3.  **Behavioral Assertions:** Instead of just checking for a static element,
#     it observes the behavior of the page over time (checking for src attribute
#     changes) to verify that the video stream is not just present, but actively
#     updating. This provides a much stronger guarantee that the system is
#     working correctly.
#
# 4.  **Performance Baseline:** It establishes a simple performance baseline
#     (at least 5 FPS) to catch potential regressions that could make the
#     application unusable, even if it's technically "working."
# ======================================================================================

import pytest
import asyncio
from playwright.async_api import Page, expect

# Mark the test as a pytest test
@pytest.mark.asyncio
async def test_visualizer_frame_rate(page: Page):
    """
    Tests that the video stream is updating at a reasonable frame rate.
    """
    # Explicitly navigate to the proxy server's address.
    await page.goto("http://localhost:5000")

    # Wait for the image element to be present and visible.
    video_stream_element = page.locator("#video-stream")
    await expect(video_stream_element).to_be_visible(timeout=10000) # 10s timeout

    # Check for src attribute updates over a short period.
    frame_count = 0
    start_time = asyncio.get_event_loop().time()
    
    async def get_frame_src():
        return await video_stream_element.get_attribute("src")

    last_src = await get_frame_src()

    # Observe for 2 seconds.
    while asyncio.get_event_loop().time() - start_time < 2:
        current_src = await get_frame_src()
        if current_src != last_src:
            frame_count += 1
            last_src = current_src
        await asyncio.sleep(0.05)  # Check every 50ms

    # Assert that the frame rate is at least 5 FPS (10 frames in 2 seconds).
    # This is a baseline to ensure the stream is active and not stalled.
    print(f"Frames captured in 2 seconds: {frame_count}")
    assert frame_count >= 10, f"Test failed: Frame rate is too low ({frame_count / 2} FPS)."
