# !!! WARNING !!!
# THIS IS A REVERSE PROXY. ITS SOLE PURPOSE IS TO ROUTE DYNAMIC API REQUESTS
# TO THE APPROPRIATE BACKEND SERVICE. IT SHOULD NOT, UNDER ANY CIRCUMSTANCES,
# BE USED TO SERVE STATIC FILES. THAT IS THE JOB OF A DEDICATED STATIC
# FILE SERVER (E.G., NGINX). ADDING STATIC FILE SERVING LOGIC TO THIS
# PROXY WILL ONLY LEAD TO CONFUSION AND MAINTENANCE HEADACHES.
#
# IF YOU ARE TEMPTED TO ADD STATIC FILE SERVING TO THIS PROXY, PLEASE
# RESIST THE URGE AND SET UP A PROPER STATIC FILE SERVER INSTEAD.

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import logging


# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Define the base URLs for the backend services
SERVICE_MAP = {
    "videostream_mock_server": "http://localhost:8003",
    "dct_service": "http://localhost:5002",
    "reference_frame_service": "http://localhost:5003",
    "difference_service": "http://localhost:5004",
    "accumulator_service": "http://localhost:5005",
    "orchestration_service": "http://localhost:5006",
    "visualizer_server": "http://localhost:5007" # The server for static visualizer files
}







@app.route('/<service_name>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request(service_name, subpath):
    base_url = SERVICE_MAP.get(service_name)
    if not base_url:
        logging.error(f"Unknown service: {service_name}")
        return jsonify({"error": "Unknown service"}), 404

    target_url = f"{base_url}/{subpath}"
    method = request.method
    headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'content-length']}
    data = request.get_data() if method in ['POST', 'PUT'] else None

    logging.info(f"Proxying {method} request to {target_url}")

    try:
        resp = requests.request(method, target_url, headers=headers, data=data, params=request.args, stream=True)

        # Create a new response object
        response = Response(resp.iter_content(chunk_size=8192), status=resp.status_code)

        # Copy headers from the backend response to the proxy response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response.headers[key] = value
        
        # Add CORS headers to the proxy response
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'

        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Proxy communication error with {base_url}: {e}")
        return jsonify({"error": f"Proxy communication error: {e}"}), 500

if __name__ == '__main__':
    app.run(port=5008) # Proxy server will run on port 5008

# This server is typically started by `start_visualizer_services.sh`.
