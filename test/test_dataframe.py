"""
PLC TCP/IP Bridge - Test Suite for PLCData
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT
"""

import pytest
import struct
from plc_tcpip_bridge.dataframe import PLCData


class TestPLCData:
    """Test suite for PLCData class"""

    def test_add_field(self):
        """Test adding fields to PLCData"""
        data = PLCData()
        data.add_field('speed', 'I', 100)
        data.add_field('temp', 'f', 25.5)

        assert len(data._fields) == 2
        assert data._fields[0][0] == 'speed'
        assert data._fields[1][0] == 'temp'

    def test_chain_add_field(self):
        """Test chaining add_field calls"""
        data = (PLCData()
                .add_field('speed', 'I', 100)
                .add_field('temp', 'f', 25.5)
                .add_field('status', 'H', 1))

        assert len(data._fields) == 3

    def test_set_get_field(self):
        """Test setting and getting field values"""
        data = PLCData().add_field('speed', 'I', 0)

        data.set('speed', 1500)
        assert data.get('speed') == 1500

    def test_set_nonexistent_field(self):
        """Test setting non-existent field raises error"""
        data = PLCData().add_field('speed', 'I', 0)

        with pytest.raises(KeyError):
            data.set('temperature', 25.5)

    def test_get_nonexistent_field(self):
        """Test getting non-existent field raises error"""
        data = PLCData().add_field('speed', 'I', 0)

        with pytest.raises(KeyError):
            data.get('temperature')

    def test_pack_unpack_integers(self):
        """Test packing and unpacking integer values"""
        original = (PLCData()
                    .add_field('byte_val', 'B', 255)
                    .add_field('word_val', 'H', 65535)
                    .add_field('dword_val', 'I', 4294967295))

        packed = original.pack()

        unpacked = PLCData()
        unpacked.add_field('byte_val', 'B', 0)
        unpacked.add_field('word_val', 'H', 0)
        unpacked.add_field('dword_val', 'I', 0)
        unpacked.unpack(packed)

        assert unpacked.get('byte_val') == 255
        assert unpacked.get('word_val') == 65535
        assert unpacked.get('dword_val') == 4294967295

    def test_pack_unpack_floats(self):
        """Test packing and unpacking float values"""
        original = (PLCData()
                    .add_field('real_val', 'f', 123.456)
                    .add_field('lreal_val', 'd', 987.654321))

        packed = original.pack()

        unpacked = PLCData()
        unpacked.add_field('real_val', 'f', 0.0)
        unpacked.add_field('lreal_val', 'd', 0.0)
        unpacked.unpack(packed)

        assert abs(unpacked.get('real_val') - 123.456) < 0.001
        assert abs(unpacked.get('lreal_val') - 987.654321) < 0.000001

    def test_pack_unpack_bool(self):
        """Test packing and unpacking boolean values"""
        original = (PLCData()
                    .add_field('enabled', '?', True)
                    .add_field('disabled', '?', False))

        packed = original.pack()

        unpacked = PLCData()
        unpacked.add_field('enabled', '?', False)
        unpacked.add_field('disabled', '?', True)
        unpacked.unpack(packed)

        assert unpacked.get('enabled') == True
        assert unpacked.get('disabled') == False

    def test_size_calculation(self):
        """Test byte size calculation"""
        data = (PLCData()
                .add_field('byte_val', 'B', 0)  # 1 byte
                .add_field('word_val', 'H', 0)  # 2 bytes
                .add_field('dword_val', 'I', 0))  # 4 bytes

        assert data.size() == 7  # 1 + 2 + 4

    def test_clone(self):
        """Test cloning PLCData structure"""
        original = (PLCData()
                    .add_field('speed', 'I', 1500)
                    .add_field('temp', 'f', 25.5))

        cloned = original.clone()

        # Check structure is same
        assert len(cloned._fields) == len(original._fields)
        assert cloned._fields[0][0] == 'speed'
        assert cloned._fields[1][0] == 'temp'

        # Check values are reset
        assert cloned.get('speed') == 0
        assert cloned.get('temp') == 0

    def test_clone_independence(self):
        """Test that cloned data is independent"""
        original = PLCData().add_field('speed', 'I', 1500)
        cloned = original.clone()

        cloned.set('speed', 2000)

        assert original.get('speed') == 1500
        assert cloned.get('speed') == 2000

    def test_repr(self):
        """Test string representation"""
        data = (PLCData()
                .add_field('speed', 'I', 1500)
                .add_field('temp', 'f', 25.5))

        repr_str = repr(data)
        assert 'PLCData' in repr_str
        assert 'speed=1500' in repr_str
        assert 'temp=25.5' in repr_str

    def test_mixed_types(self):
        """Test packing/unpacking mixed data types"""
        original = (PLCData()
                    .add_field('byte_val', 'B', 100)
                    .add_field('int_val', 'h', -500)
                    .add_field('float_val', 'f', 3.14)
                    .add_field('bool_val', '?', True)
                    .add_field('dword_val', 'I', 1000000))

        packed = original.pack()

        unpacked = (PLCData()
                    .add_field('byte_val', 'B', 0)
                    .add_field('int_val', 'h', 0)
                    .add_field('float_val', 'f', 0.0)
                    .add_field('bool_val', '?', False)
                    .add_field('dword_val', 'I', 0))
        unpacked.unpack(packed)

        assert unpacked.get('byte_val') == 100
        assert unpacked.get('int_val') == -500
        assert abs(unpacked.get('float_val') - 3.14) < 0.01
        assert unpacked.get('bool_val') == True
        assert unpacked.get('dword_val') == 1000000

    def test_big_endian_format(self):
        """Test that data uses big-endian format"""
        data = PLCData().add_field('value', 'H', 0x1234)
        packed = data.pack()

        # Big-endian: most significant byte first
        assert packed[0] == 0x12
        assert packed[1] == 0x34

    def test_empty_plcdata(self):
        """Test empty PLCData"""
        data = PLCData()
        assert len(data._fields) == 0
        assert data.size() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])