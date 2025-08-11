# server.py
import http.server, socketserver, os
from http.server import SimpleHTTPRequestHandler

PORT = 8001
os.chdir(os.path.dirname(__file__))

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '86400')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🚀 CORS-enabled server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {os.getcwd()}")
        print(f"🔒 CORS headers enabled for all origins")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")