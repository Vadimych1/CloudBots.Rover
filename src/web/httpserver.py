from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import threading

class R_Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory = "./web/", **kwargs)

class R_HTTPServer:
    def __init__(self):
        self.httpd = HTTPServer(("0.0.0.0", 80), R_Handler)
        self.logger = logging.getLogger("HTTPServer")
        
    def run(self):
        self.logger.info("Started HTTP server on :80")
        self.t = threading.Thread(target=self.httpd.serve_forever)
        return self.t