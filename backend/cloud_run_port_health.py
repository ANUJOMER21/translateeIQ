"""Listen on $PORT with an empty 200 response — required for Celery on Google Cloud Run."""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class _Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    HTTPServer(("0.0.0.0", port), _Health).serve_forever()


if __name__ == "__main__":
    main()
