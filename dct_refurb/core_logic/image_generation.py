

from PIL import Image, ImageDraw, ImageFont
import datetime
import io

def generate_image(worker_name):
    """
    Generates an image with a timestamp and the worker's name.
    This is a stateless function that returns an image as a byte stream.
    """
    img = Image.new('RGB', (400, 300), color = 'darkslateblue')
    d = ImageDraw.Draw(img)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    d.text((10,10), f"Worker [{worker_name}] Stream:\n{now}", fill=(255,255,0), font=font)
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return img_io.read()

