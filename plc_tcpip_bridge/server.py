"""
PLC TCP/IP Bridge
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""
import socket
from typing import Optional
from plc_tcpip_bridge.dataframe import PLCData


class PLCServer:
    """Server that passively establishes connections"""
    def __init__(self, host: str = '0.0.0.0', port: int = 502, data_template: PLCData = None):
        self.host = host
        self.port = port
        self.data_template = data_template
        self.server_sock: Optional[socket.socket] = None
        self.running = False

    def start(self) -> bool:
        """Start server"""
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind((self.host, self.port))
            self.server_sock.listen(5)
            self.running = True
            print(f"Server listening on {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"Server start error: {e}")
            return False

    def accept_connection(self) -> Optional[socket.socket]:
        """Accept client connection"""
        try:
            client_sock, addr = self.server_sock.accept()
            client_sock.settimeout(5.0)
            print(f"Client connected: {addr}")
            return client_sock
        except socket.error as e:
            print(f"Accept error: {e}")
            return None

    def handle_client(self, client_sock: socket.socket):
        """Handle client communication"""
        try:
            while self.running:
                # Receive data
                data = self._recv_exact(client_sock, self.data_template.size())
                if not data:
                    print("Client disconnected")
                    break

                recv_data = self.data_template.clone().unpack(data)
                print(f"Received: {recv_data}")

                # Process and send response
                response = self.data_template.clone()
                for name, _, value in recv_data._fields:
                    # Example processing logic
                    if isinstance(value, int):
                        response.set(name, value + 1)
                    elif isinstance(value, float):
                        response.set(name, value * 2)
                    else:
                        response.set(name, value)

                client_sock.sendall(response.pack())
                print(f"Sent: {response}")

        except (socket.error, socket.timeout) as e:
            print(f"Client handler error: {e}")
        finally:
            client_sock.close()

    def _recv_exact(self, sock: socket.socket, n: int) -> Optional[bytes]:
        """Receive exactly n bytes"""
        data = b''
        while len(data) < n:
            try:
                chunk = sock.recv(n - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.timeout:
                continue
            except socket.error:
                return None
        return data

    def run(self):
        """Main server loop"""
        if not self.start():
            return

        try:
            while self.running:
                client_sock = self.accept_connection()
                if client_sock:
                    self.handle_client(client_sock)
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            self.stop()

    def stop(self):
        """Stop server"""
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
            self.server_sock = None
        print("Server stopped")