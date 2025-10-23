"""
PLC TCP/IP Bridge
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""
import struct
from typing import List, Tuple, Any


class PLCData:
    """Dynamic PLC data structure"""

    def __init__(self):
        self._fields: List[Tuple[str, str, Any]] = []  # (name, format, value)
        self._format = '>'  # big-endian

    def add_field(self, name: str, fmt: str, value: Any = 0):
        """
        Add field with Siemens S7 data type format:
        BOOL: '?' (1 bit, stored as byte)
        BYTE: 'B' (8-bit unsigned)
        WORD: 'H' (16-bit unsigned)
        DWORD: 'I' (32-bit unsigned)
        LWORD: 'Q' (64-bit unsigned)
        SINT: 'b' (8-bit signed)
        INT: 'h' (16-bit signed)
        DINT: 'i' (32-bit signed)
        LINT: 'q' (64-bit signed)
        USINT: 'B' (8-bit unsigned)
        UINT: 'H' (16-bit unsigned)
        UDINT: 'I' (32-bit unsigned)
        ULINT: 'Q' (64-bit unsigned)
        REAL: 'f' (32-bit float)
        LREAL: 'd' (64-bit double)
        CHAR: 'c' (1 byte character)
        STRING: 'Ns' (N=length, e.g., '10s' for 10 chars)
        """
        self._fields.append((name, fmt, value))
        return self

    def set(self, name: str, value: Any):
        """Set field value by name"""
        for i, (n, fmt, _) in enumerate(self._fields):
            if n == name:
                self._fields[i] = (n, fmt, value)
                return
        raise KeyError(f"Field '{name}' not found")

    def get(self, name: str) -> Any:
        """Get field value by name"""
        for n, _, v in self._fields:
            if n == name:
                return v
        raise KeyError(f"Field '{name}' not found")

    def pack(self) -> bytes:
        """Convert to bytes"""
        fmt = self._format + ''.join(f for _, f, _ in self._fields)
        values = [v for _, _, v in self._fields]
        return struct.pack(fmt, *values)

    def unpack(self, data: bytes):
        """Convert from bytes"""
        fmt = self._format + ''.join(f for _, f, _ in self._fields)
        values = struct.unpack(fmt, data)
        for i, (n, f, _) in enumerate(self._fields):
            self._fields[i] = (n, f, values[i])
        return self

    def size(self) -> int:
        """Get byte size"""
        fmt = self._format + ''.join(f for _, f, _ in self._fields)
        return struct.calcsize(fmt)

    def clone(self) -> 'PLCData':
        """Create empty clone with same structure"""
        new = PLCData()
        new._fields = [(n, f, 0) for n, f, _ in self._fields]
        return new

    def __repr__(self):
        return f"PLCData({', '.join(f'{n}={v}' for n, _, v in self._fields)})"