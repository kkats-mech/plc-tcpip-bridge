"""
PLC TCP/IP Bridge - Server Example
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT

This example demonstrates a simple echo server that receives data from clients,
prints it, and echoes it back.
"""

from plc_tcpip_bridge.dataframe import PLCData
from plc_tcpip_bridge.server import PLCServer

if __name__ == "__main__":

    # Define data structure - must match client structure
    plc_struct = (PLCData()
                  .add_field('motor_speed', 'I', 0)      # uint32
                  .add_field('temperature', 'f', 0.0)    # float
                  .add_field('status', 'H', 0)           # uint16
                  .add_field('enabled', '?', False))     # bool

    print("=" * 60)
    print("PLC TCP/IP Bridge - Echo Server")
    print("=" * 60)
    print(f"Listening on: 0.0.0.0:502")
    print(f"Data structure size: {plc_struct.size()} bytes")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)

    # Create and start server
    server = PLCServer(host='localhost', port=502, data_template=plc_struct)

    print("\nWaiting for client connections...")
    print("Server will process received data as follows:")
    print("  - Integers: add 1")
    print("  - Floats: multiply by 2")
    print("  - Others: echo unchanged")
    print()

    try:
        # Run server - it has built-in processing and echo logic
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Server shutdown complete")