"""
PLC TCP/IP Bridge
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""

import socket, time
from typing import Optional
from plc_tcpip_bridge.dataframe import PLCData

class PLCClient:
    """Client that actively establishes connections"""
    def __init__(self, host: str, port: int, data_template: PLCData,
                 max_retries: int = 5, retry_delay: float = 2.0):
        self.host = host
        self.port = port
        self.data_template = data_template
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.sock: Optional[socket.socket] = None
        self.connected = False

    def connect(self) -> bool:
        """Connect with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5.0)
                self.sock.connect((self.host, self.port))
                self.connected = True
                print(f"Connected to {self.host}:{self.port}")
                return True
            except (socket.error, socket.timeout) as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                self._cleanup()
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        return False

    def send(self, data: PLCData) -> bool:
        """Send data to PLC"""
        if not self.connected:
            return False
        try:
            self.sock.sendall(data.pack())
            return True
        except (socket.error, BrokenPipeError) as e:
            print(f"Send error: {e}")
            self._handle_disconnect()
            return False

    def receive(self) -> Optional[PLCData]:
        """Receive data from PLC"""
        if not self.connected:
            return None
        try:
            data = self._recv_exact(self.data_template.size())
            if data:
                return self.data_template.clone().unpack(data)
            self._handle_disconnect()
            return None
        except (socket.error, socket.timeout) as e:
            print(f"Receive error: {e}")
            self._handle_disconnect()
            return None

    def _recv_exact(self, n: int) -> Optional[bytes]:
        """Receive exactly n bytes"""
        data = b''
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _handle_disconnect(self):
        """Handle unexpected disconnection"""
        print("Connection lost, attempting reconnect...")
        self._cleanup()
        self.connect()

    def _cleanup(self):
        """Close socket safely"""
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

    def close(self):
        """Close connection"""
        self._cleanup()