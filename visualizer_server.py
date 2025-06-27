import http.server
import socketserver

PORT = 5007

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving visualizer at http://localhost:{PORT}/visualizer.html")
    httpd.serve_forever()