from flask import Flask, Response, send_from_directory
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/video')
def video_proxy():
    r = requests.get('http://localhost:5001/video', stream=True)
    return Response(r.iter_content(chunk_size=1024), content_type = r.headers['content-type'])

@app.route('/visualizer.html')
def visualizer():
    return send_from_directory('.', 'visualizer.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
