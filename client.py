import socket


def server(name):

    HOST = '0.0.0.0'
    PORT = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)

    print('server start at: %s:%s' % (HOST, PORT))
    print('wait for connection...')

    while True:
        conn, addr = s.accept()
        print('connected by ' + str(addr))

        while True:
            indata = conn.recv(1024)
            if len(indata) == 0:  # connection closed
                conn.close()
                print('client closed connection.')
                break
            print('recv: ' + indata.decode())

            outdata = 'echo ' + indata.decode()
            conn.send(outdata.encode())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    server('PyCharm')
