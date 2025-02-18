from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging
import threading

class R_Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, directory="web")

class R_HTTPServer:
    def __init__(self):
        self.httpd = HTTPServer(("0.0.0.0", 1025), R_Handler)
        self.logger = logging.getLogger("HTTPServer")
        
    def run(self):
        self.logger.info("Started HTTP server on :1025")
        self.t = threading.Thread(target=self.httpd.serve_forever)
        return self.t