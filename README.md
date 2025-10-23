# PLC TCP/IP Bridge

A Python library for communicating with PLCs (Programmable Logic Controllers) over TCP/IP with a simple, intuitive API that can be scaled for multiple applications  e.g. for PC HMIs, ROS and ROS2 applications.

## Features

- **Dynamic Data Structures**: Define PLC data layouts with named fields
- **IEC 61131-3 data types**: Full support for PLC data types (BOOL, BYTE, WORD, DWORD, INT, DINT, REAL, LREAL, etc.)
- **Client & Server**: Both TCP/IP client and server implementations
- **Auto-Reconnection**: Built-in retry logic for robust industrial applications
- **Performance Monitoring**: Loop frequency tracking, timing statistics, and connection health monitoring

## Installation

### From PyPI (coming soon)
```bash
pip install plc-tcpip-bridge
```

### From Source
```bash
git clone https://github.com/kkats-mech/plc-tcpip-bridge.git
cd plc-tcpip-bridge
pip install -e .
```

## Quick Start

### Define PLC Data Structure
```python
from plc_tcpip_bridge.dataframe import PLCData

# Define your PLC memory layout
plc_data = (PLCData()
    .add_field('motor_speed', 'I', 0)      # DWORD (32-bit)
    .add_field('temperature', 'f', 0.0)    # REAL (32-bit float)
    .add_field('status', 'H', 0)           # WORD (16-bit)
    .add_field('enabled', '?', False))     # BOOL
```

### Client Example
```python
from plc_tcpip_bridge.client import PLCClient

client = PLCClient("192.168.1.100", 502, plc_data)

if client.connect():
    # Send data
    send_data = plc_data.clone()
    send_data.set('motor_speed', 1500)
    send_data.set('temperature', 25.5)
    client.send(send_data)
    
    # Receive data
    recv_data = client.receive()
    if recv_data:
        print(f"Speed: {recv_data.get('motor_speed')}")
    
    client.close()
```

### Server Example
```python
from plc_tcpip_bridge.server import PLCServer

server = PLCServer(host='0.0.0.0', port=502, data_template=plc_data)
server.run()
```

### Using Utilities
```python
from plc_tcpip_bridge.utils import FrequencyMonitor, RateLimiter

freq_mon = FrequencyMonitor(print_interval=1.0)
rate_limiter = RateLimiter(target_hz=50)

while running:
    # Your PLC communication
    client.send(data)
    recv_data = client.receive()
    
    freq_mon.print_if_ready("Loop")  # Prints: "Loop: 50.23 Hz"
    rate_limiter.sleep()  # Maintains 50 Hz
```


## Supported Data Types

| PLC Type | Format | Python Type | Size | Range |
|----------|--------|-------------|------|-------|
| BOOL | `?` | bool | 1 byte | True/False |
| BYTE/USINT | `B` | int | 1 byte | 0-255 |
| SINT | `b` | int | 1 byte | -128 to 127 |
| WORD/UINT | `H` | int | 2 bytes | 0-65535 |
| INT | `h` | int | 2 bytes | -32768 to 32767 |
| DWORD/UDINT | `I` | int | 4 bytes | 0-4294967295 |
| DINT | `i` | int | 4 bytes | -2147483648 to 2147483647 |
| LWORD/ULINT | `Q` | int | 8 bytes | 0-2^64-1 |
| LINT | `q` | int | 8 bytes | -2^63 to 2^63-1 |
| REAL | `f` | float | 4 bytes | IEEE 754 |
| LREAL | `d` | float | 8 bytes | IEEE 754 |
| CHAR | `c` | str | 1 byte | Single character |
| STRING | `Ns` | str | N bytes | Fixed length (e.g., `10s`) |

## Utilities

### FrequencyMonitor
Track and display loop execution frequency.

```python
freq_mon = FrequencyMonitor(print_interval=1.0)
freq_mon.print_if_ready("Client loop")
```

### RateLimiter
Maintain consistent loop timing.

```python
limiter = RateLimiter(target_hz=100)
limiter.sleep()  # Enforces 100 Hz rate
```

### ConnectionMonitor
Track connection health and statistics.

```python
conn_mon = ConnectionMonitor(alert_threshold=5)
conn_mon.record_success()  # or record_failure()
conn_mon.print_stats()
```

### DataLogger
Log PLC data with timestamps.

```python
logger = DataLogger(max_entries=1000)
logger.log({'speed': 1500, 'temp': 25.5})
logger.save_to_file('plc_log.json')
```

### Watchdog
Detect stalled communication loops.

```python
watchdog = Watchdog(timeout=5.0)
while running:
    watchdog.kick()  # Reset timer
    # ... communication ...
    if watchdog.check():  # Returns True if timeout
        break
```

## Project Structure

```
plc-tcpip-bridge/
├── plc_tcpip_bridge/          # Main package
│   ├── __init__.py
│   ├── dataframe.py           # PLCData class
│   ├── client.py              # TCP/IP client
│   ├── server.py              # TCP/IP server
│   └── utils.py               # Utilities (monitoring, logging, etc.)
├── examples/                  # Example scripts
│   ├── example_client.py      # Basic client example
│   └── example_server.py      # Basic server example
├── test/                      # Test suite
│   ├── __init__.py            # Makes test a package
│   ├── test_dataframe.py      # PLCData tests
│   ├── test_client.py         # Client tests
│   ├── test_server.py         # Server tests
│   └── test_utils.py          # Utils tests
├── .gitignore                 # Git ignore rules
├── CITATION.cff               # Citation metadata
├── LICENSE                    # MIT License
├── MANIFEST.in                # Package manifest
├── README.md                  # Documentation
├── requirements.txt           # Dependencies
└── setup.py                   # Package setup
```

## Requirements

- Python 3.7+
- No external dependencies for core library
- Optional: `tkinter` for HMI (usually included with Python)

## Examples

See the `examples/` directory for complete working examples:
- `example_client.py` - Simple client with monitoring
- `example_server.py` - Echo server implementation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation
If you use this software in your research, please cite it as:
```bibtex
@software{katsampiris_salgado_2025_plc_tcpip_bridge,
  author       = {Katsampiris Salgado, Konstantinos},
  title        = {PLC TCP/IP Bridge},
  year         = 2025,
  url          = {https://github.com/kkats-mech/plc-tcpip-bridge},
  version      = {0.1.0}
}
```

Or in text format:

> Katsampiris Salgado, K. (2025). PLC TCP/IP Bridge (Version 0.1.0) [Computer software]. https://github.com/kkats-mech/plc-tcpip-bridge

You may also refer to the CITATION.cff file too.

## Acknowledgments
Inspired by industrial automation needs based on my experience in robotics research projects.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Roadmap

- [ ] TBD
---

**Handle with care. Use wisely. Do not drink and drive. Be responsible.**
