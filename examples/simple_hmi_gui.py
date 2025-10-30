"""
PLC TCP/IP Bridge - Simple GUI HMI
Author: Konstantinos Katsampiris Salgado
Email: katsampiris.konst@gmail.com
GitHub: https://github.com/kkats-mech/plc-tcpip-bridge
License: MIT

A simple tkinter-based graphical HMI for controlling a PLC.
This is a minimal example demonstrating the basics of GUI control.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from plc_tcpip_bridge.dataframe import PLCData
from plc_tcpip_bridge.client import PLCClient
from plc_tcpip_bridge.utils import RateLimiter

class SimpleGUIHMI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple PLC HMI")
        self.root.geometry("700x600")

        # Connection state
        self.connected = False
        self.running = False
        self.client = None

        # Control variables
        self.motor_speed = tk.IntVar(value=0)
        self.temperature = tk.DoubleVar(value=20.0)
        self.enable = tk.BooleanVar(value=False)

        # Feedback variables
        self.status_text = tk.StringVar(value="Disconnected")
        self.feedback_speed = tk.StringVar(value="0")
        self.feedback_temp = tk.StringVar(value="0.0")
        self.feedback_status = tk.StringVar(value="0")

        # Data structures
        self.plc_struct_snd = None
        self.plc_struct_rcv = None

        # Build UI
        self.create_widgets()

    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Connection Section
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(conn_frame, text="IP:").grid(row=0, column=0, padx=5)
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "localhost")
        self.ip_entry.grid(row=0, column=1, padx=5)

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5)
        self.port_entry = ttk.Entry(conn_frame, width=8)
        self.port_entry.insert(0, "502")
        self.port_entry.grid(row=0, column=3, padx=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect",
                                      command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=5)

        ttk.Label(conn_frame, text="Status:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(conn_frame, textvariable=self.status_text).grid(row=1, column=1,
                                                                    columnspan=3, sticky=tk.W)

        # Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Control (Send to PLC)", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), padx=5, pady=5)

        # Enable checkbox
        ttk.Checkbutton(control_frame, text="System Enable",
                       variable=self.enable).grid(row=0, column=0, columnspan=2,
                                                  sticky=tk.W, pady=5)

        # Motor speed
        ttk.Label(control_frame, text="Motor Speed (RPM):").grid(row=1, column=0,
                                                                  sticky=tk.W, pady=5)
        speed_scale = ttk.Scale(control_frame, from_=0, to=3000,
                               variable=self.motor_speed, orient=tk.HORIZONTAL)
        speed_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(control_frame, textvariable=self.motor_speed).grid(row=1, column=2,
                                                                      padx=5)

        # Temperature
        ttk.Label(control_frame, text="Temperature (°C):").grid(row=2, column=0,
                                                                 sticky=tk.W, pady=5)
        temp_scale = ttk.Scale(control_frame, from_=0, to=100,
                              variable=self.temperature, orient=tk.HORIZONTAL)
        temp_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        temp_label = ttk.Label(control_frame, text="0.0")
        temp_label.grid(row=2, column=2, padx=5)

        # Update temperature label
        def update_temp_label(*args):
            temp_label.config(text=f"{self.temperature.get():.1f}")
        self.temperature.trace_add('write', update_temp_label)

        # Send button
        self.send_btn = ttk.Button(control_frame, text="Send Data to PLC",
                                   command=self.send_data_manual,
                                   state=tk.DISABLED)
        self.send_btn.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

        # Feedback Section
        feedback_frame = ttk.LabelFrame(main_frame, text="Feedback (From PLC)", padding="10")
        feedback_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), padx=5, pady=5)

        ttk.Label(feedback_frame, text="Actual Speed:").grid(row=0, column=0,
                                                              sticky=tk.W, pady=5)
        ttk.Label(feedback_frame, textvariable=self.feedback_speed).grid(row=0, column=1,
                                                                          sticky=tk.W, padx=5)

        ttk.Label(feedback_frame, text="Actual Temp:").grid(row=1, column=0,
                                                             sticky=tk.W, pady=5)
        ttk.Label(feedback_frame, textvariable=self.feedback_temp).grid(row=1, column=1,
                                                                         sticky=tk.W, padx=5)

        ttk.Label(feedback_frame, text="Status Code:").grid(row=2, column=0,
                                                             sticky=tk.W, pady=5)
        ttk.Label(feedback_frame, textvariable=self.feedback_status).grid(row=2, column=1,
                                                                           sticky=tk.W, padx=5)

        # Communication Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Communication Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Scrolled text widget for log
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70,
                                                   state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Clear log button
        clear_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_btn.grid(row=1, column=0, pady=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        """Clear the communication log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def toggle_connection(self):
        if not self.connected:
            self.connect_to_plc()
        else:
            self.disconnect_from_plc()

    def connect_to_plc(self):
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())

        # Define send structure
        self.plc_struct_snd = (PLCData()
                              .add_field('motor_speed', 'I', 0)
                              .add_field('temperature', 'f', 0.0)
                              .add_field('status', 'H', 0)
                              .add_field('enabled', '?', False))

        # Define receive structure (matches what server sends back)
        self.plc_struct_rcv = (PLCData()
                              .add_field('motor_speed', 'I', 0)
                              .add_field('temperature', 'f', 0.0)
                              .add_field('status', 'H', 0)
                              .add_field('enabled', '?', False))

        self.client = PLCClient(ip, port, self.plc_struct_rcv)

        if self.client.connect():
            self.connected = True
            self.running = True
            self.status_text.set(f"Connected to {ip}:{port}")
            self.connect_btn.config(text="Disconnect")
            self.send_btn.config(state=tk.NORMAL)
            self.log_message(f"✓ Connected to {ip}:{port}")
            self.log_message(f"Data structure size: {self.plc_struct_snd.size()} bytes")

            # Start communication thread
            self.comm_thread = threading.Thread(target=self.communication_loop, daemon=True)
            self.comm_thread.start()
        else:
            self.status_text.set("Connection Failed")
            self.log_message(f"✗ Connection failed to {ip}:{port}")

    def disconnect_from_plc(self):
        self.running = False
        if self.client:
            self.client.close()
        self.connected = False
        self.status_text.set("Disconnected")
        self.connect_btn.config(text="Connect")
        self.send_btn.config(state=tk.DISABLED)
        self.log_message("✓ Disconnected from PLC")

    def send_data_manual(self):
        """Send data to PLC when button is clicked"""
        if not self.connected or not self.client:
            self.log_message("✗ Not connected to PLC")
            return

        try:
            # Prepare send data
            send_data = self.plc_struct_snd.clone()
            send_data.set('motor_speed', self.motor_speed.get())
            send_data.set('temperature', self.temperature.get())
            send_data.set('status', 0)  # Client typically sends 0 for status
            send_data.set('enabled', self.enable.get())

            # Log what we're sending
            self.log_message(f">>> SENDING: Speed={self.motor_speed.get()}, "
                           f"Temp={self.temperature.get():.1f}, "
                           f"Enabled={self.enable.get()}")

            # Send to PLC
            if self.client.send(send_data):
                self.log_message("✓ Data sent successfully")

                # Receive response
                recv_data = self.client.receive()
                if recv_data:
                    # Update feedback displays
                    self.feedback_speed.set(f"{recv_data.get('motor_speed')} RPM")
                    self.feedback_temp.set(f"{recv_data.get('temperature'):.1f} °C")
                    self.feedback_status.set(str(recv_data.get('status')))

                    # Log what we received
                    self.log_message(f"<<< RECEIVED: Speed={recv_data.get('motor_speed')}, "
                                   f"Temp={recv_data.get('temperature'):.1f}, "
                                   f"Status={recv_data.get('status')}, "
                                   f"Enabled={recv_data.get('enabled')}")
                else:
                    self.log_message("✗ No response from PLC")
            else:
                self.log_message("✗ Failed to send data")

        except Exception as e:
            self.log_message(f"✗ Error: {e}")

    def communication_loop(self):
        """Background thread - kept for future use (monitoring, keep-alive, etc.)"""
        # This loop is minimal now since we're using manual send button
        # Could be extended for continuous monitoring or keep-alive pings
        rate_limiter = RateLimiter(target_hz=1)

        while self.running:
            # Just sleep to keep thread alive
            # Data is sent via the Send button
            rate_limiter.sleep()

def main():
    root = tk.Tk()
    app = SimpleGUIHMI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
