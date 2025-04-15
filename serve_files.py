#!/usr/bin/env python
"""
Simple HTTP server to serve files from the output directory.
"""

import http.server
import socketserver
import os
import sys

# Default port
PORT = 8080

# Directory to serve files from
DIRECTORY = "output"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    # Change to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Check if output directory exists
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory '{DIRECTORY}' not found.")
        sys.exit(1)

    # Create the server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving files from '{DIRECTORY}' at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
