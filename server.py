import socket
import threading
import select
import sqlite3 as sl

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

    def __str__(self):
        return str(self.id) + " " + str(self.address)

    def run(self):
        while self.signal:
            try:
                ready_to_read, ready_to_write, in_error = \
                    select.select(
                        [self.sock],
                        [],
                        [],
                        60  # timeout
                    )

            except select.error:
                print(f"Client ID {str(self)} has disconnected")
                self.signal = False
                connections.remove(self)
                break
            if len(ready_to_read) > 0:
                data = self.sock.recv(32)
                if data.decode("utf-8", errors="ignore") == "":
                    print(f"Client ID {str(self)} has disconnected")
                    self.signal = False
                    connections.remove(self)
                    break
                else:
                    print(f"ID {str(self.id)}: {str(data.decode('utf-8', errors='ignore'))}")
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

    # with db_conn:
    #     db_conn.execute("""
    #             CREATE TABLE USER (
    #                 id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    #                 name TEXT
    #             );
    #         """)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)

    newConnectionsThread = threading.Thread(target=connections_daemon, args=(sock,))
    newConnectionsThread.start()


main()
