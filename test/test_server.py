"""
PLC TCP/IP Bridge - Test Suite for PLCServer
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""

import pytest
import socket
import threading
import time
from plc_tcpip_bridge.dataframe import PLCData
from plc_tcpip_bridge.server import PLCServer


class MockClient:
    """Mock PLC client for testing"""

    def __init__(self, host='127.0.0.1', port=8087):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

    def connect(self):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(2.0)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Mock client connect error: {e}")
            return False

    def send(self, data: bytes):
        """Send data to server"""
        if not self.connected:
            return False
        try:
            self.socket.sendall(data)
            return True
        except Exception:
            return False

    def receive(self, size: int) -> bytes:
        """Receive data from server"""
        if not self.connected:
            return None
        try:
            data = b''
            while len(data) < size:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            return data
        except Exception:
            return None

    def close(self):
        """Close connection"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None


class TestPLCServer:
    """Test suite for PLCServer class"""

    @pytest.fixture
    def plc_struct(self):
        """Fixture for test PLC structure"""
        return (PLCData()
                .add_field('speed', 'I', 0)
                .add_field('temp', 'f', 0.0)
                .add_field('status', 'H', 0))

    def test_server_initialization(self, plc_struct):
        """Test server initialization"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)

        assert server.host == '127.0.0.1'
        assert server.port == 8087
        assert server.running == False
        assert server.data_template == plc_struct

    def test_server_start(self, plc_struct):
        """Test starting server"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)

        result = server.start()

        assert result == True
        assert server.running == True

        server.stop()

    def test_server_start_on_used_port(self, plc_struct):
        """Test starting server on already used port fails"""
        server1 = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server2 = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)

        server1.start()
        result = server2.start()

        assert result == False

        server1.stop()

    def test_server_accept_connection(self, plc_struct):
        """Test accepting client connection"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server.start()

        # Start server in thread
        server_thread = threading.Thread(target=lambda: server.accept_connection(), daemon=True)
        server_thread.start()

        time.sleep(0.1)

        # Connect with mock client
        client = MockClient(port=8087)
        result = client.connect()

        assert result == True

        time.sleep(0.1)
        client.close()
        server.stop()

    def test_server_receive_data(self, plc_struct):
        """Test server receiving data from client"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server.start()

        received_data = []

        def handle_and_store():
            client_sock = server.accept_connection()
            if client_sock:
                data = server._recv_exact(client_sock, plc_struct.size())
                if data:
                    recv = plc_struct.clone().unpack(data)
                    received_data.append(recv)
                client_sock.close()

        server_thread = threading.Thread(target=handle_and_store, daemon=True)
        server_thread.start()

        time.sleep(0.1)

        # Send data from mock client
        client = MockClient(port=8087)
        client.connect()

        send_data = plc_struct.clone()
        send_data.set('speed', 1500)
        send_data.set('temp', 25.5)
        send_data.set('status', 1)

        client.send(send_data.pack())
        time.sleep(0.2)

        assert len(received_data) > 0
        assert received_data[0].get('speed') == 1500

        client.close()
        server.stop()

    def test_server_send_response(self, plc_struct):
        """Test server sending response to client"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server.start()

        def echo_handler():
            client_sock = server.accept_connection()
            if client_sock:
                # Receive
                data = server._recv_exact(client_sock, plc_struct.size())
                if data:
                    recv = plc_struct.clone().unpack(data)

                    # Process and respond
                    response = plc_struct.clone()
                    response.set('speed', recv.get('speed') + 100)
                    response.set('temp', recv.get('temp') * 2)
                    response.set('status', recv.get('status') + 1)

                    client_sock.sendall(response.pack())
                client_sock.close()

        server_thread = threading.Thread(target=echo_handler, daemon=True)
        server_thread.start()

        time.sleep(0.1)

        # Client send and receive
        client = MockClient(port=8087)
        client.connect()

        send_data = plc_struct.clone()
        send_data.set('speed', 1000)
        send_data.set('temp', 20.0)
        send_data.set('status', 5)

        client.send(send_data.pack())
        recv_bytes = client.receive(plc_struct.size())

        assert recv_bytes is not None

        recv_data = plc_struct.clone().unpack(recv_bytes)
        assert recv_data.get('speed') == 1100  # 1000 + 100
        assert abs(recv_data.get('temp') - 40.0) < 0.1  # 20.0 * 2
        assert recv_data.get('status') == 6  # 5 + 1

        client.close()
        server.stop()

    def test_server_stop(self, plc_struct):
        """Test stopping server"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server.start()

        assert server.running == True

        server.stop()

        assert server.running == False
        assert server.server_sock is None

    def test_server_multiple_clients_sequential(self, plc_struct):
        """Test server handling multiple clients sequentially"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server.start()

        connection_count = [0]

        def accept_multiple():
            for _ in range(2):
                client_sock = server.accept_connection()
                if client_sock:
                    connection_count[0] += 1
                    client_sock.close()

        server_thread = threading.Thread(target=accept_multiple, daemon=True)
        server_thread.start()

        time.sleep(0.1)

        # First client
        client1 = MockClient(port=8087)
        client1.connect()
        time.sleep(0.1)
        client1.close()

        time.sleep(0.1)

        # Second client
        client2 = MockClient(port=8087)
        client2.connect()
        time.sleep(0.1)
        client2.close()

        time.sleep(0.2)

        assert connection_count[0] == 2

        server.stop()

    def test_recv_exact(self, plc_struct):
        """Test _recv_exact method"""
        server = PLCServer(host='127.0.0.1', port=8087, data_template=plc_struct)
        server.start()

        received = []

        def receive_handler():
            client_sock = server.accept_connection()
            if client_sock:
                data = server._recv_exact(client_sock, 10)
                received.append(data)
                client_sock.close()

        server_thread = threading.Thread(target=receive_handler, daemon=True)
        server_thread.start()

        time.sleep(0.1)

        client = MockClient(port=8087)
        client.connect()
        client.send(b'0123456789')

        time.sleep(0.2)

        assert len(received) > 0
        assert received[0] == b'0123456789'
        assert len(received[0]) == 10

        client.close()
        server.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])