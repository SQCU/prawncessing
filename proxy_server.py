#!/usr/bin/env python
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import json

PORT = 8000
SAVE_SERVER = "http://localhost:8001"
APP_SERVER = "http://localhost:8002"

class ProxyHandler(BaseHTTPRequestHandler):
    def _get_service_info(self):
        return {
            "proxy_port": PORT,
            "services": {
                "save_log": {
                    "url": f"{SAVE_SERVER}/savelog",
                    "description": "Endpoint for saving logs and screenshots."
                },
                "ethos": {
                    "url": f"{SAVE_SERVER}/ETHOS.MD",
                    "description": "The project's ethos."
                },
                "about": {
                    "url": f"{SAVE_SERVER}/ABOUT",
                    "description": "System resource information."
                },
                "application": {
                    "url": f"{APP_SERVER}",
                    "description": "The main web application."
                }
            }
        }

    def _proxy_request(self, method, url, data=None, headers=None):
        try:
            resp = requests.request(method, url, data=data, headers=headers, stream=True)
            self.send_response(resp.status_code)
            for key, value in resp.headers.items():
                if key.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                    self.send_header(key, value)
            self.send_header('Content-Length', str(len(resp.content)))
            self.end_headers()
            self.wfile.write(resp.content)
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Proxy Error: {e}")

    def do_GET(self):
        if self.path.startswith('/savelog') or self.path.startswith('/ETHOS.MD') or self.path.startswith('/ABOUT'):
            self._proxy_request('GET', f"{SAVE_SERVER}{self.path}", headers=self.headers)
        elif self.path == '/' or self.path.startswith('/index.html') or self.path.endswith(('.js', '.css')):
            self._proxy_request('GET', f"{APP_SERVER}{self.path}", headers=self.headers)
        elif self.path == '/discover':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self._get_service_info()).encode('utf-8'))
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path.startswith('/savelog'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self._proxy_request('POST', f"{SAVE_SERVER}{self.path}", data=post_data, headers=self.headers)
        else:
            self.send_error(404, 'Not Found')

if __name__ == '__main__':
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f"Proxy server started at localhost:{PORT}")
    print("Discover services at http://localhost:8000/discover")
    httpd.serve_forever()
