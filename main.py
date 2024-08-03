from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse
import mimetypes
import pathlib
import socket
import threading
import json


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message.html":
            self.send_html_file("./message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        # send data to socket server
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            server = UDP_IP, UDP_PORT
            sock.sendto(json.dumps(data_dict).encode(), server)
            print(f"Send data: {data} to: {server}")

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


# SOCKET
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5000


def save_data(data):
    try:
        # Read existing data
        with open("storage\data.json", "r", encoding="utf-8") as f:
            data_from_file = json.load(f)
    except FileNotFoundError:
        # If the file does not exist, start with an empty dictionary
        data_from_file = {}

    # Update the data with the new entry
    data_from_file[str(datetime.now())] = data

    # Write the updated data back to the file
    with open("storage\data.json", "w", encoding="utf-8") as f:
        json.dump(data_from_file, f, ensure_ascii=False, indent=4)

    print(f"Data saved: {data}")


def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            decoded_data = json.loads(data.decode())
            print(f"Received data: {decoded_data} from: {address}")
            save_data(decoded_data)

    except KeyboardInterrupt:
        print(f"Destroy server")
    finally:
        sock.close()


if __name__ == "__main__":
    web_application = threading.Thread(target=run)
    socket_server = threading.Thread(target=run_server, args=(UDP_IP, UDP_PORT))
    web_application.start()
    socket_server.start()
    web_application.join()
    socket_server.join()
