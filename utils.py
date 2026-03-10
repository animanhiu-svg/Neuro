import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import config

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Если запрос к /app — отдаём наш Mini App
        if self.path == '/app':
            try:
                # Пытаемся открыть файл mini_app/index.html
                with open('mini_app/index.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404: Mini App not found")
        else:
            # Для всех остальных запросов (проверки Render) отвечаем как раньше
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("I am alive!".encode('utf-8'))

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", config.PORT), Handler)
    print(f"✅ Пищалка на порту {config.PORT}, Mini App доступен по /app")
    server.serve_forever()

def start_pinger():
    threading.Thread(target=run_server, daemon=True).start()
