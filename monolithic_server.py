'''
import http.server
import socketserver
import json
import os
import shutil
from pathlib import Path

PORT = 8000
LOG_DIR = Path("./seqlog")

class MonolithicHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/savelog':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                if 'type' not in data or 'payload' not in data or 'filename' not in data:
                    raise ValueError("Missing required fields in post data")

                LOG_DIR.mkdir(exist_ok=True)
                file_path = LOG_DIR / data['filename']

                if data['type'] == 'screenshot':
                    import base64
                    img_data = base64.b64decode(data['payload'].split(',')[1])
                    with open(file_path, 'wb') as f:
                        f.write(img_data)
                elif data['type'] == 'log' or data['type'] == 'metadata':
                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write(data['payload'])
                else:
                    raise ValueError(f"Unknown data type: {data['type']}")

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/ETHOS.MD':
            try:
                with open('ETHOS.md', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/markdown')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
        elif self.path == '/ABOUT':
            total, used, free = shutil.disk_usage('/')
            about_data = {
                "total_storage_gb": total // (2**30),
                "used_storage_gb": used // (2**30),
                "free_storage_gb": free // (2**30)
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(about_data).encode('utf-8'))
        else:
            # Fall back to serving static files
            super().do_GET()

with socketserver.TCPServer(("", PORT), MonolithicHandler) as httpd:
    print("Monolithic server started at localhost:" + str(PORT))
    httpd.serve_forever()
''