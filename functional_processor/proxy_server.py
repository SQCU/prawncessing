from flask import Flask, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def visualizer_proxy():
    r = requests.get('http://localhost:8080/')
    return Response(r.content, content_type = r.headers['content-type'])

@app.route('/<path:subpath>')
def service_proxy(subpath):
    # This will proxy all other requests to the orchestration_service
    r = requests.get(f'http://localhost:5006/{subpath}')
    return Response(r.content, content_type = r.headers['content-type'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)