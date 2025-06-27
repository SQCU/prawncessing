import asyncio
import subprocess
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variable to hold the current frame and its readiness status
current_frame = None
frame_ready = False

async def generate_frames():
    global current_frame, frame_ready
    video_path = "processed_video.mp4"
    width = 1920 # From ffprobe output
    height = 1080 # From ffprobe output

    while True:
        # Forward playback
        cmd_forward = [
            "ffmpeg",
            "-i", video_path,
            "-f", "rawvideo",
            "-pix_fmt", "bgr24", # Use bgr24 for OpenCV compatibility
            "-s", f"{width}x{height}",
            "-vsync", "0", # Ensure all frames are output
            "-vcodec", "rawvideo",
            "-"
        ]
        logging.info(f"Starting ffmpeg for forward playback: {' '.join(cmd_forward)}")
        try:
            process_forward = await asyncio.create_subprocess_exec(
                *cmd_forward,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            logging.error("ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH.")
            break
        except Exception as e:
            logging.error(f"Error starting ffmpeg subprocess for forward playback: {e}")
            break

        bytes_per_frame = width * height * 3 # 3 bytes for BGR

        while True:
            try:
                # Read exactly one frame's worth of data
                in_bytes = b''
                while len(in_bytes) < bytes_per_frame:
                    chunk = await process_forward.stdout.read(bytes_per_frame - len(in_bytes))
                    if not chunk:
                        break # End of stream
                    in_bytes += chunk

                logging.info(f"Read {len(in_bytes)} bytes from ffmpeg stdout (expected {bytes_per_frame})")

                if len(in_bytes) < bytes_per_frame:
                    logging.info("End of forward stream or incomplete frame received.")
                    break
                
                frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
                ret, jpeg = cv2.imencode('.jpg', frame)
                logging.info(f"cv2.imencode returned ret={ret}")
                if ret:
                    current_frame = jpeg.tobytes()
                    frame_ready = True # Set flag when a valid frame is available
                    logging.info(f"Encoded JPEG size: {len(current_frame)} bytes")
                else:
                    logging.warning("cv2.imencode failed to encode frame to JPEG.")
                await asyncio.sleep(0.033) # Simulate ~30fps
            except asyncio.IncompleteReadError as e:
                logging.error(f"Incomplete read from ffmpeg stdout (forward): {e}")
                break
            except Exception as e:
                logging.error(f"Error processing frame from ffmpeg (forward): {e}")
                break

        stderr_output = await process_forward.stderr.read()
        if stderr_output:
            logging.error(f"ffmpeg stderr (forward): {stderr_output.decode().strip()}")
        else:
            logging.info("ffmpeg stderr (forward): (empty)")
        await process_forward.wait()
        logging.info(f"ffmpeg forward process exited with code: {process_forward.returncode}")

        # Reverse playback
        cmd_reverse = [
            "ffmpeg",
            "-i", video_path,
            "-vf", "reverse", # Reverse the video frames
            "-f", "rawvideo",
            "-pix_fmt", "bgr24", # Use bgr24 for OpenCV compatibility
            "-s", f"{width}x{height}",
            "-vsync", "0", # Ensure all frames are output
            "-vcodec", "rawvideo",
            "-"
        ]
        logging.info(f"Starting ffmpeg for reverse playback: {' '.join(cmd_reverse)}")
        try:
            process_reverse = await asyncio.create_subprocess_exec(
                *cmd_reverse,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            logging.error("ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH.")
            break
        except Exception as e:
            logging.error(f"Error starting ffmpeg subprocess for reverse playback: {e}")
            break

        while True:
            try:
                # Read exactly one frame's worth of data
                in_bytes = b''
                while len(in_bytes) < bytes_per_frame:
                    chunk = await process_reverse.stdout.read(bytes_per_frame - len(in_bytes))
                    if not chunk:
                        break # End of stream
                    in_bytes += chunk

                logging.info(f"Read {len(in_bytes)} bytes from ffmpeg stdout (expected {bytes_per_frame})")

                if len(in_bytes) < bytes_per_frame:
                    logging.info("End of reverse stream or incomplete frame received.")
                    break
                
                frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
                ret, jpeg = cv2.imencode('.jpg', frame)
                logging.info(f"cv2.imencode returned ret={ret}")
                if ret:
                    current_frame = jpeg.tobytes()
                    frame_ready = True # Set flag when a valid frame is available
                    logging.info(f"Encoded JPEG size: {len(current_frame)} bytes")
                else:
                    logging.warning("cv2.imencode failed to encode frame to JPEG.")
                await asyncio.sleep(0.033) # Simulate ~30fps
            except asyncio.IncompleteReadError as e:
                logging.error(f"Incomplete read from ffmpeg stdout (reverse): {e}")
                break
            except Exception as e:
                logging.error(f"Error processing frame from ffmpeg (reverse): {e}")
                break

        stderr_output = await process_reverse.stderr.read()
        if stderr_output:
            logging.error(f"ffmpeg stderr (reverse): {stderr_output.decode().strip()}")
        else:
            logging.info("ffmpeg stderr (reverse): (empty)")
        await process_reverse.wait()
        logging.info(f"ffmpeg reverse process exited with code: {process_reverse.returncode}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_frames())

@app.get("/frame")
async def get_frame():
    if current_frame:
        return Response(content=current_frame, media_type="image/jpeg")
    else:
        return {"message": "No frame available yet"}

@app.get("/ready")
async def get_ready_status():
    return {"ready": frame_ready}