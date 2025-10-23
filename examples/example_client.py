from plc_tcpip_bridge.dataframe import  PLCData
from plc_tcpip_bridge.client import PLCClient
import time

# Usage example
if __name__ == "__main__":
    # Define data structure once
    tprev=time.time()
    plc_struct = (PLCData()
                  .add_field('motor_speed', 'I', 0)  # uint32
                  .add_field('temperature', 'f', 0.0)  # float
                  .add_field('status', 'H', 0)  # uint16
                  .add_field('enabled', '?', False))  # bool

    client = PLCClient("localhost", 502, plc_struct)

    if client.connect():

        while True:
            tprev = time.time()
            # Send data
            send_data = plc_struct.clone()
            send_data.set('motor_speed', 1500)
            send_data.set('temperature', 25.5)
            send_data.set('status', 1)
            send_data.set('enabled', True)

            if client.send(send_data):
                print(f"Sent: {send_data}")

            # Receive data
            recv_data = client.receive()
            if recv_data:
                print(f"Received: {recv_data}")
                print(f"Motor speed: {recv_data.get('motor_speed')}")
                time.sleep(0.001)
            print(f"send/recv: {1/(time.time() - tprev)}")

    client.close()