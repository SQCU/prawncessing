from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw
import io
import random

app = Flask(__name__)
CORS(app)

@app.route('/echo', methods=['POST'])
def echo():
    if 'image' not in request.files:
        return 'No image file provided', 400
    
    image_file = request.files['image']
    image = Image.open(image_file.stream)

    # Add pink stripes
    draw = ImageDraw.Draw(image)
    for i in range(0, image.height, 10):
        draw.line([(0, i), (image.width, i)], fill=(255, 192, 203), width=5)

    # Apply a random shear
    x_shear = random.uniform(-0.03, 0.03)
    y_shear = random.uniform(-0.03, 0.03)
    image = image.transform(image.size, Image.AFFINE, (1, x_shear, 0, y_shear, 1, 0))

    # Save the modified image to a byte stream
    byte_io = io.BytesIO()
    image.save(byte_io, 'PNG')
    byte_io.seek(0)

    return send_file(byte_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010)