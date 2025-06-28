from flask import Flask, Response
from PIL import Image, ImageDraw, ImageFont
import datetime
import io

app = Flask(__name__)

@app.route('/video')
def video_feed():
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
