import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import config

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("I am alive!".encode('utf-8'))

def run_server():
    server = HTTPServer(("0.0.0.0", config.PORT), Handler)
    print(f"✅ Пищалка запущена на порту {config.PORT}")
    server.serve_forever()

def start_pinger():
    threading.Thread(target=run_server, daemon=True).start().
