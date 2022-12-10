import socket
import threading
import select
import ssl
import sqlite3 as sl
import cv2

from api import api

connections = []
total_connections = 0


class Client(threading.Thread):
    def __init__(self, sock, address, id_num, name, signal):
        threading.Thread.__init__(self)
        self.sock = sock
        self.address = address
        self.id = id_num
        self.name = name
        self.signal = signal
        self.cap = None

    def __str__(self):
        return str(self.id) + " " + str(self.address)

    def send_response(self, response):
        if self.signal:
            try:
                self.sock.send(response)
            except ConnectionAbortedError:
                self.kill()

    def kill(self):
        print(f"Client ID {str(self)} has disconnected")
        self.signal = False
        if self.cap is not None:
            self.cap.release()
        connections.remove(self)
        print("■ connections:", [x.id for x in connections])

    def run(self):
        while self.signal:
            try:
                ready_to_read, ready_to_write, in_error = \
                    select.select(
                        [self.sock],
                        [],
                        [],
                        1  # timeout
                    )

            except select.error:
                self.kill()
                break
            if len(ready_to_read) > 0:
                data = self.sock.recv(2000).decode(errors="ignore")
                if data == "":  # client left
                    self.kill()
                    break
                else:
                    try:
                        method, path, *_ = data.split()
                        print(f"ID {str(self.id)}:", method, path)
                        print("■ connections:", [x.id for x in connections])
                    except ValueError:
                        continue
                    api(method, path, self)

            if len(ready_to_write) > 0:
                pass


def connections_daemon(main_socket):
    while True:
        sock, address = main_socket.accept()
        global total_connections
        connections.append(Client(sock, address, total_connections, "Name", True))
        connections[-1].start()
        print("New connection at ID " + str(connections[- 1]))
        total_connections += 1


def main():
    host = "0.0.0.0"
    port = 12345

    # sqlite
    db_conn = sl.connect("data.db")
    c = db_conn.cursor()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # server = ssl.wrap_socket(
    #     server, server_side=True, keyfile="path/to/keyfile", certfile="path/to/certfile"
    # )

    server.bind((host, port))
    server.listen(5)

    newConnectionsThread = threading.Thread(target=connections_daemon, args=(server,))
    newConnectionsThread.start()


main()
