
import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    """
    This test script uses Playwright to verify that the proxy server is
    correctly serving the visualizer application. It checks if the main page
    loads and if there are any critical errors in the browser console.
    It also verifies that a processed frame is displayed on the output canvas.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        try:
            print("Navigating to proxy server at http://localhost:5008...")
            await page.goto("http://localhost:5008", wait_until="networkidle")
            
            print("Checking page title...")
            await expect(page).to_have_title("Visualizer V3")
            print("Page title is correct.")

            # Allow time for the video stream to start and the first frame to be processed
            print("Waiting for processed frame...")
            await page.wait_for_timeout(5000) # 5 seconds

            # Check if the output canvas has been drawn on
            output_canvas_blank = await page.evaluate('''() => {
                const canvas = document.getElementById('output');
                const context = canvas.getContext('2d');
                const pixelBuffer = new Uint32Array(
                    context.getImageData(0, 0, canvas.width, canvas.height).data.buffer
                );
                return !pixelBuffer.some(pixel => pixel !== 0);
            }''')

            if not output_canvas_blank:
                print("Test Passed: Processed frame detected on the output canvas.")
            else:
                print("Test Failed: Output canvas appears to be blank.")


            if console_errors:
                print("Console errors were detected:")
                for error in console_errors:
                    print(f"  - {error}")

        except Exception as e:
            print(f"An error occurred during the test: {e}")
            if console_errors:
                print("Console errors:")
                for error in console_errors:
                    print(f"  - {error}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
