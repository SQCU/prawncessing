from flask import Flask, Response
from PIL import Image, ImageDraw, ImageFont
import datetime
import io
import psutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

def monitor_usage(func):
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        logging.info(f"CPU Usage: {cpu_percent}% | Memory Usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        return func(*args, **kwargs)
    return wrapper

@app.route('/video')
def video_feed():
    @monitor_usage
    def generate():
        while True:
            # Create a blank image
            img = Image.new('RGB', (400, 300), color = 'black')
            d = ImageDraw.Draw(img)

            # Get current time
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            # Draw text
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            d.text((10,10), now, fill=(255,255,0), font=font)

            # Save image to a byte stream
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=70)
            img_io.seek(0)
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_io.read() + b'\r\n')

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
