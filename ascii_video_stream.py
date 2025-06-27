

import requests
import cv2
import numpy as np
import time

VIDEOSTREAM_URL = "http://127.0.0.1:8003/frame"

# ASCII characters ordered by perceived density
ASCII_CHARS = [" ", ".", ",", ":", ";", "+", "*", "?", "%", "S", "#", "@"]

def get_ascii_char(pixel_intensity):
    # Map pixel intensity (0-255) to an ASCII character
    return ASCII_CHARS[int(pixel_intensity / 256 * len(ASCII_CHARS))]

def frame_to_ascii(frame_data, width=80, height=25):
    try:
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return "Error: Could not decode image."

        # Convert to grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Resize for ASCII conversion
        resized_img = cv2.resize(gray_img, (width, height), interpolation=cv2.INTER_AREA)

        ascii_frame = ""
        for row in resized_img:
            for pixel in row:
                ascii_frame += get_ascii_char(pixel)
            ascii_frame += "\n"
        return ascii_frame
    except Exception as e:
        return f"Error processing frame to ASCII: {e}"

def display_video_stream():
    print("\nStarting ASCII video stream...\n")
    while True:
        try:
            response = requests.get(VIDEOSTREAM_URL, timeout=1)
            response.raise_for_status()
            frame_data = response.content
            ascii_output = frame_to_ascii(frame_data)
            
            # Clear previous frame (by printing newlines) and print new frame
            # This will create a scrolling effect, not a fixed PIP
            print(ascii_output)
            time.sleep(0.1) # Adjust for desired frame rate
        except requests.exceptions.RequestException as e:
            # print(f"ASCII stream error: {e}") # Suppress frequent errors if server not ready
            time.sleep(0.5) # Wait a bit before retrying
        except KeyboardInterrupt:
            print("Stopping ASCII video stream.")
            break

if __name__ == "__main__":
    display_video_stream()

