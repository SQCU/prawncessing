from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from logging.handlers import RotatingFileHandler
import os

from frame_processor import process_frame_logic
from output_retriever import get_processed_frame_logic
from reference_manager import set_reference_logic

app = Flask(__name__)
CORS(app)

# Configure logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/orchestration_service.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Orchestration service startup')

# Define the URLs for the functional services (for direct exposure if needed)
DCT_SERVICE_URL = "http://localhost:5002"
REFERENCE_FRAME_SERVICE_URL = "http://localhost:5003"
DIFFERENCE_SERVICE_URL = "http://localhost:5004"
ACCUMULATOR_SERVICE_URL = "http://localhost:5005"

@app.route('/process_frame', methods=['POST'])
def process_frame():
    try:
        data = request.json
        frame_id = data.get('frame_id')
        image_data = data.get('image_data')
        result = process_frame_logic(frame_id, image_data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service communication error: {e}"}), 500

@app.route('/get_processed_frame', methods=['GET'])
def get_processed_frame():
    try:
        result = get_processed_frame_logic()
        return jsonify(result), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service communication error: {e}"}), 500

@app.route('/set_reference', methods=['POST'])
def set_reference():
    try:
        data = request.json
        image_data = data.get('image_data')
        result = set_reference_logic(image_data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service communication error: {e}"}), 500

# This section defines routes that act as an inter-service router.
# Its functional role is to proxy requests from the visualizer (or other clients)
# to specific functional processing services (e.g., DCT, Difference, Accumulator).
# This design helps avoid CORS errors by centralizing communication through a single origin
# (the orchestration service) and reduces unnecessary coupling by abstracting the direct
# URLs of individual services from the frontend.
@app.route('/dct_service/<path:subpath>', methods=['GET', 'POST'])
def proxy_dct_service(subpath):
    return _proxy_request(DCT_SERVICE_URL, subpath)

@app.route('/reference_frame_service/<path:subpath>', methods=['GET', 'POST'])
def proxy_reference_frame_service(subpath):
    return _proxy_request(REFERENCE_FRAME_SERVICE_URL, subpath)

@app.route('/difference_service/<path:subpath>', methods=['GET', 'POST'])
def proxy_difference_service(subpath):
    return _proxy_request(DIFFERENCE_SERVICE_URL, subpath)

@app.route('/accumulator_service/<path:subpath>', methods=['GET', 'POST'])
def proxy_accumulator_service(subpath):
    return _proxy_request(ACCUMULATOR_SERVICE_URL, subpath)

# Helper function to proxy requests to other internal services.
# This centralizes the logic for forwarding requests, handling headers,
# and managing potential communication errors.
def _proxy_request(base_url, subpath):
    url = f"{base_url}/{subpath}"
    method = request.method
    headers = {key: value for key, value in request.headers if key.lower() not in ['content-length', 'host']}
    data = request.get_data() if method == 'POST' else None

    try:
        resp = requests.request(method, url, headers=headers, data=data)
        response = jsonify(resp.json())
        response.status_code = resp.status_code
        return response
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Proxy communication error with {base_url}: {e}"}), 500

if __name__ == '__main__':
    app.run(port=5006)

# This service is typically started by `functional_processor/start_functional_processors.sh` or `start_functional_processors_orchestration.sh`.
