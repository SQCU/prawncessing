#!/usr/bin/env python
import http.server
import socketserver

PORT = 8002

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"App server started at localhost:{PORT}")
    httpd.serve_forever()

# This server is typically started by `start.sh`.

