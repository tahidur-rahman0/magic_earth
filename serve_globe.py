import http.server
import socketserver
import webbrowser
import os
import time

PORT = 8000
DIRECTORY = "/Users/tohidur/Project/magic"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving globe at http://localhost:{PORT}/globe.html")
        print("Opening your browser now... Press Ctrl+C to stop the server.")
        
        # Give server a moment to start
        time.sleep(1)
        # Automatically open the browser
        webbrowser.open(f"http://localhost:{PORT}/globe.html")
        
        httpd.serve_forever()
except OSError as e:
    if e.errno == 98 or e.errno == 48:
        print(f"Port {PORT} is already in use. Please try a different port or kill the process.")
    else:
        raise
