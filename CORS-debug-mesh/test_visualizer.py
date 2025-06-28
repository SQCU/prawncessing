import asyncio
import re
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("file:///home/bigboi/prawncessing/CORS-debug-mesh/visualizer.html")

        # Wait for the image to have a src attribute that matches the pattern
        await expect(page.locator("#video-stream")).to_have_attribute("src", re.compile(r"http:\/\/localhost:5000\/video.*"))

        # Check for updates
        frame_count = 0
        start_time = asyncio.get_event_loop().time()
        
        async def get_frame_src():
            return await page.locator("#video-stream").get_attribute("src")

        last_src = await get_frame_src()

        while asyncio.get_event_loop().time() - start_time < 2: # run for 2 seconds
            current_src = await get_frame_src()
            if current_src != last_src:
                frame_count += 1
                last_src = current_src
            await asyncio.sleep(0.05) # check every 50ms

        print(f"Frames captured in 2 seconds: {frame_count}")
        
        # Expecting at least 10 frames in 2 seconds (5 FPS) as a baseline
        if frame_count >= 10:
             print("Test passed: Frame rate is acceptable.")
        else:
            print(f"Test failed: Frame rate is too low ({frame_count/2} FPS).")


        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
