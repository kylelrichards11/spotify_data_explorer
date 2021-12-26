from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

if __name__ == "__main__":
    # server_address = ('', 41849)
    server_address = ('', 8888)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Running Server")
    httpd.serve_forever()