import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(__file__), "frontend")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()

def main():
    print("=" * 60)
    print(f"🛡️  PERIMETER Frontend Server (Python)")
    print(f"🔗 Local URL:  http://localhost:{PORT}/")
    print(f"📝 Register:   http://localhost:{PORT}/register.html")
    print("=" * 60)
    
    # Auto open browser
    try:
        webbrowser.open(f"http://localhost:{PORT}/register.html")
    except Exception:
        pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)

if __name__ == "__main__":
    main()
