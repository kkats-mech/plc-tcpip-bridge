"""
PLC TCP/IP Bridge - Test Suite for PLCClient
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
from plc_tcpip_bridge.client import PLCClient


class MockServer:
    """Mock PLC server for testing"""

    def __init__(self, port=8085):
        self.port = port
        self.running = False
        self.server_socket = None
        self.client_socket = None
        self.received_data = []
        self.response_data = None

    def start(self):
        """Start mock server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.port))
        self.server_socket.listen(1)
        self.running = True

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        time.sleep(0.1)  # Give server time to start

    def _run(self):
        """Server run loop"""
        self.client_socket, _ = self.server_socket.accept()
        self.client_socket.settimeout(1.0)

        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break

                self.received_data.append(data)

                if self.response_data:
                    self.client_socket.sendall(self.response_data)
            except socket.timeout:
                continue
            except Exception:
                break

    def stop(self):
        """Stop mock server"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


class TestPLCClient:
    """Test suite for PLCClient class"""

    @pytest.fixture
    def plc_struct(self):
        """Fixture for test PLC structure"""
        return (PLCData()
                .add_field('speed', 'I', 0)
                .add_field('temp', 'f', 0.0)
                .add_field('status', 'H', 0))

    @pytest.fixture
    def mock_server(self):
        """Fixture for mock server"""
        server = MockServer(port=8086)
        server.start()
        yield server
        server.stop()

    def test_client_initialization(self, plc_struct):
        """Test client initialization"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)

        assert client.host == "127.0.0.1"
        assert client.port == 8086
        assert client.connected == False
        assert client.max_retries == 5

    def test_client_connect(self, mock_server, plc_struct):
        """Test successful connection"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)

        assert client.connect() == True
        assert client.connected == True

        client.close()

    def test_client_connect_failure(self, plc_struct):
        """Test connection failure to non-existent server"""
        client = PLCClient("127.0.0.1", 9999, plc_struct, max_retries=1)

        assert client.connect() == False
        assert client.connected == False

    def test_client_send(self, mock_server, plc_struct):
        """Test sending data"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)
        client.connect()

        send_data = plc_struct.clone()
        send_data.set('speed', 1500)
        send_data.set('temp', 25.5)
        send_data.set('status', 1)

        result = client.send(send_data)
        time.sleep(0.1)  # Allow time for server to receive

        assert result == True
        assert len(mock_server.received_data) > 0

        client.close()

    def test_client_receive(self, mock_server, plc_struct):
        """Test receiving data"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)
        client.connect()

        # Prepare response data
        response = plc_struct.clone()
        response.set('speed', 2000)
        response.set('temp', 30.0)
        response.set('status', 2)
        mock_server.response_data = response.pack()

        # Send dummy data to trigger response
        send_data = plc_struct.clone()
        client.send(send_data)

        # Receive response
        recv_data = client.receive()

        assert recv_data is not None
        assert recv_data.get('speed') == 2000
        assert abs(recv_data.get('temp') - 30.0) < 0.1
        assert recv_data.get('status') == 2

        client.close()

    def test_client_send_without_connection(self, plc_struct):
        """Test sending without connection fails"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)

        send_data = plc_struct.clone()
        result = client.send(send_data)

        assert result == False

    def test_client_receive_without_connection(self, plc_struct):
        """Test receiving without connection returns None"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)

        recv_data = client.receive()

        assert recv_data is None

    def test_client_close(self, mock_server, plc_struct):
        """Test closing connection"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)
        client.connect()

        assert client.connected == True

        client.close()

        assert client.connected == False
        assert client.sock is None

    def test_client_close_without_connection(self, plc_struct):
        """Test closing without connection doesn't error"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)

        # Should not raise exception
        client.close()

        assert client.connected == False

    def test_client_retry_parameters(self, plc_struct):
        """Test custom retry parameters"""
        client = PLCClient("127.0.0.1", 8086, plc_struct,
                           max_retries=3, retry_delay=0.5)

        assert client.max_retries == 3
        assert client.retry_delay == 0.5

    def test_data_roundtrip(self, mock_server, plc_struct):
        """Test full send/receive roundtrip"""
        client = PLCClient("127.0.0.1", 8086, plc_struct)
        client.connect()

        # Prepare send data
        send_data = plc_struct.clone()
        send_data.set('speed', 1234)
        send_data.set('temp', 56.78)
        send_data.set('status', 9)

        # Server echoes back the received data
        mock_server.response_data = send_data.pack()

        # Send and receive
        client.send(send_data)
        recv_data = client.receive()

        assert recv_data is not None
        assert recv_data.get('speed') == 1234
        assert abs(recv_data.get('temp') - 56.78) < 0.1
        assert recv_data.get('status') == 9

        client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])