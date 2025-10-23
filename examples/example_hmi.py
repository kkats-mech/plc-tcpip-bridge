import tkinter as tk
from tkinter import ttk
import threading
from plc_tcpip_bridge.dataframe import PLCData
from plc_tcpip_bridge.client import PLCClient
from plc_tcpip_bridge.utils import FrequencyMonitor, RateLimiter, ConnectionMonitor


class PLCHMI:
    def __init__(self, root):
        self.root = root
        self.root.title("PLC Control Panel")
        self.root.geometry("800x740")
        self.root.configure(bg='#2b2b2b')

        # PLC connection state
        self.connected = False
        self.running = False
        self.client = None

        # Control variables (send to PLC)
        self.estop_active = tk.BooleanVar(value=False)
        self.reset_radars_active = tk.BooleanVar(value=False)
        self.bypass_radars_active = tk.BooleanVar(value=False)
        self.change_zones_active = tk.BooleanVar(value=False)


        self.estop_pc_bypass = tk.BooleanVar(value=False)
        self.value_1 = tk.BooleanVar(value=False)
        self.value_2 = tk.BooleanVar(value=False)
        self.value_3 = tk.BooleanVar(value=False)
        self.value_4 = tk.BooleanVar(value=False)

        # Feedback variables (receive from PLC)
        self.estop_cart_status = tk.StringVar(value="OFF")
        self.estop_off_status = tk.StringVar(value="OFF")
        self.radar_red_status = tk.StringVar(value="OFF")
        self.radar_yell_status = tk.StringVar(value="OFF")
        self.reset_btn_status = tk.StringVar(value="OFF")

        self.rcv_val_1 = tk.StringVar(value="OFF")
        self.rcv_val_2 = tk.StringVar(value="OFF")
        self.rcv_val_3 = tk.StringVar(value="OFF")
        self.rcv_val_4 = tk.StringVar(value="OFF")
        self.rcv_val_5 = tk.StringVar(value="OFF")

        # Status variables
        self.connection_status = tk.StringVar(value="Disconnected")
        self.loop_frequency = tk.StringVar(value="0.00 Hz")
        self.success_rate = tk.StringVar(value="0.0%")

        # Build UI
        self.create_widgets()

        # Initialize utilities
        self.freq_mon = FrequencyMonitor(print_interval=0.5)
        self.rate_limiter = RateLimiter(target_hz=100)
        self.conn_mon = ConnectionMonitor(alert_threshold=5)

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title = tk.Label(main_frame, text="PLC Control Panel",
                         font=('Arial', 24, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=(0, 10))

        # Connection frame
        conn_frame = tk.LabelFrame(main_frame, text="Connection",
                                   font=('Arial', 12, 'bold'),
                                   bg='#3b3b3b', fg='white', bd=2)
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        # IP and Port entry
        entry_frame = tk.Frame(conn_frame, bg='#3b3b3b')
        entry_frame.pack(pady=10, padx=10)

        tk.Label(entry_frame, text="IP:", bg='#3b3b3b', fg='white').grid(row=0, column=0, padx=5)
        self.ip_entry = tk.Entry(entry_frame, width=15)
        self.ip_entry.insert(0, "192.168.1.47")
        self.ip_entry.grid(row=0, column=1, padx=5)

        tk.Label(entry_frame, text="Port:", bg='#3b3b3b', fg='white').grid(row=0, column=2, padx=5)
        self.port_entry = tk.Entry(entry_frame, width=8)
        self.port_entry.insert(0, "8085")
        self.port_entry.grid(row=0, column=3, padx=5)

        self.connect_btn = tk.Button(entry_frame, text="Connect",
                                     command=self.toggle_connection,
                                     bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                                     width=12, height=1)
        self.connect_btn.grid(row=0, column=4, padx=10)

        # Status labels
        status_frame = tk.Frame(conn_frame, bg='#3b3b3b')
        status_frame.pack(pady=(0, 10))

        tk.Label(status_frame, text="Status:", bg='#3b3b3b', fg='white').grid(row=0, column=0, padx=5)
        tk.Label(status_frame, textvariable=self.connection_status,
                 bg='#3b3b3b', fg='red', font=('Arial', 10, 'bold')).grid(row=0, column=1, padx=5)

        tk.Label(status_frame, text="Frequency:", bg='#3b3b3b', fg='white').grid(row=0, column=2, padx=5)
        tk.Label(status_frame, textvariable=self.loop_frequency,
                 bg='#3b3b3b', fg='cyan').grid(row=0, column=3, padx=5)

        tk.Label(status_frame, text="Success Rate:", bg='#3b3b3b', fg='white').grid(row=0, column=4, padx=5)
        tk.Label(status_frame, textvariable=self.success_rate,
                 bg='#3b3b3b', fg='lime').grid(row=0, column=5, padx=5)

        # Control and Feedback container
        control_feedback_frame = tk.Frame(main_frame, bg='#2b2b2b')
        control_feedback_frame.pack(fill=tk.BOTH, expand=True)

        # Control frame (LEFT)
        control_frame = tk.LabelFrame(control_feedback_frame, text="Control Commands",
                                      font=('Arial', 12, 'bold'),
                                      bg='#3b3b3b', fg='white', bd=2)
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Emergency Stop (Toggle)
        self.estop_btn = tk.Button(control_frame, text="EMERGENCY STOP",
                                   command=self.toggle_estop,
                                   bg='red', fg='white',
                                   font=('Arial', 14, 'bold'),
                                   height=2, relief=tk.RAISED, bd=5)
        self.estop_btn.pack(pady=10, padx=10, fill=tk.X)

        # Reset Button (Momentary)
        self.reset_btn = tk.Button(control_frame, text="RESET",
                                   command=self.press_reset,
                                   bg='blue', fg='white',
                                   font=('Arial', 14, 'bold'),
                                   height=2, relief=tk.RAISED, bd=5)
        self.reset_btn.pack(pady=10, padx=10, fill=tk.X)

        # Toggle buttons frame
        toggle_frame = tk.Frame(control_frame, bg='#3b3b3b')
        toggle_frame.pack(pady=0, padx=20, fill=tk.X)

        self.reset_radars_btn = tk.Checkbutton(toggle_frame, text="Reset Radars",
                                               variable=self.reset_radars_active,
                                               bg='#3b3b3b', fg='white',
                                               selectcolor='#555',
                                               font=('Arial', 11),
                                               activebackground='#3b3b3b',
                                               activeforeground='white')
        self.reset_radars_btn.pack(anchor=tk.W, pady=4)

        self.bypass_radars_btn = tk.Checkbutton(toggle_frame, text="Bypass Radars",
                                                variable=self.bypass_radars_active,
                                                bg='#3b3b3b', fg='white',
                                                selectcolor='#555',
                                                font=('Arial', 11),
                                                activebackground='#3b3b3b',
                                                activeforeground='white')
        self.bypass_radars_btn.pack(anchor=tk.W, pady=4)

        self.change_zones_btn = tk.Checkbutton(toggle_frame, text="Change Zones",
                                               variable=self.change_zones_active,
                                               bg='#3b3b3b', fg='white',
                                               selectcolor='#555',
                                               font=('Arial', 11),
                                               activebackground='#3b3b3b',
                                               activeforeground='white')
        self.change_zones_btn.pack(anchor=tk.W, pady=4)

        self.estop_pc_bypass_btn = tk.Checkbutton(toggle_frame, text="Estop PC bypass",
                                                variable=self.estop_pc_bypass,
                                                bg='#3b3b3b', fg='white',
                                                selectcolor='#555',
                                                font=('Arial', 11),
                                                activebackground='#3b3b3b',
                                                activeforeground='white')
        self.estop_pc_bypass_btn.pack(anchor=tk.W, pady=4)

        self.value_1_btn = tk.Checkbutton(toggle_frame, text="Spare Output 1",
                                                variable=self.value_1,
                                                bg='#3b3b3b', fg='white',
                                                selectcolor='#555',
                                                font=('Arial', 11),
                                                activebackground='#3b3b3b',
                                                activeforeground='white')
        self.value_1_btn.pack(anchor=tk.W, pady=4)


        self.value_2_btn = tk.Checkbutton(toggle_frame, text="Spare Output 2",
                                                variable=self.value_2,
                                                bg='#3b3b3b', fg='white',
                                                selectcolor='#555',
                                                font=('Arial', 11),
                                                activebackground='#3b3b3b',
                                                activeforeground='white')
        self.value_2_btn.pack(anchor=tk.W, pady=4)

        self.value_3_btn = tk.Checkbutton(toggle_frame, text="Spare Output 3",
                                                variable=self.value_3,
                                                bg='#3b3b3b', fg='white',
                                                selectcolor='#555',
                                                font=('Arial', 11),
                                                activebackground='#3b3b3b',
                                                activeforeground='white')
        self.value_3_btn.pack(anchor=tk.W, pady=4)

        self.value_4_btn = tk.Checkbutton(toggle_frame, text="Spare Output 4",
                                                variable=self.value_4,
                                                bg='#3b3b3b', fg='white',
                                                selectcolor='#555',
                                                font=('Arial', 11),
                                                activebackground='#3b3b3b',
                                                activeforeground='white')
        self.value_4_btn.pack(anchor=tk.W, pady=4)




        # Feedback frame (RIGHT)
        self.feedback_frame = tk.LabelFrame(control_feedback_frame, text="PLC Feedback",
                                       font=('Arial', 12, 'bold'),
                                       bg='#3b3b3b', fg='white', bd=2)
        self.feedback_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.feedback_labels = {}
        # Feedback indicators
        self.indicators = [
            ("E-Stop Cart:", self.estop_cart_status, "estop_cart"),
            ("E-Stop Off:", self.estop_off_status, "estop_off"),
            ("Radar Red:", self.radar_red_status, "radar_red"),
            ("Radar Yellow:", self.radar_yell_status, "radar_yell"),
            ("Reset Button:", self.reset_btn_status, "reset_btn"),
            ("Spare Input 1:", self.rcv_val_1, "null1"),
            ("Spare Input 2:", self.rcv_val_2, "null2"),
            ("Spare Input 3:", self.rcv_val_3, "null3"),
            ("Spare Input 4:", self.rcv_val_4, "null4"),
            ("Spare Input 5:", self.rcv_val_5, "null5"),
        ]
        for i, (label, var, key) in enumerate(self.indicators):
            frame = tk.Frame(self.feedback_frame, bg='#3b3b3b')
            frame.pack(pady=7, padx=20, fill=tk.X)

            tk.Label(frame, text=label, bg='#3b3b3b', fg='white',
                     font=('Arial', 11), width=15, anchor=tk.W).pack(side=tk.LEFT)

            status_label = tk.Label(frame, textvariable=var,
                                    bg='#555', fg='red',
                                    font=('Arial', 11, 'bold'),
                                    width=8, relief=tk.SUNKEN, bd=2)
            status_label.pack(side=tk.RIGHT)
            self.feedback_labels[key] = status_label  # ADD THIS LINE at the end

    def toggle_estop(self):
        """Toggle emergency stop button"""
        self.estop_active.set(not self.estop_active.get())
        if self.estop_active.get():
            self.estop_btn.config(relief=tk.SUNKEN, bg='#cc0000')
        else:
            self.estop_btn.config(relief=tk.RAISED, bg='red')

    def press_reset(self):
        """Momentary reset button press"""
        if not self.connected:
            return
        self.reset_btn.config(relief=tk.SUNKEN, bg='#cc8800')
        self.root.after(200, lambda: self.reset_btn.config(relief=tk.RAISED, bg='blue'))
        # Send reset pulse (handled in communication loop)

    def toggle_connection(self):
        """Connect/Disconnect from PLC"""
        if not self.connected:
            self.connect_to_plc()
        else:
            self.disconnect_from_plc()

    def connect_to_plc(self):
        """Establish PLC connection"""
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())

        # Define PLC data structures
        self.plc_struct_rcv = (PLCData()
                               .add_field('estop_cart', 'B', 0)
                               .add_field('estop_off', 'B', 0)
                               .add_field('radar_red', 'B', 0)
                               .add_field('radar_yell', 'B', 0)
                               .add_field('reset_btn', 'B', 0)
                               .add_field('null1', 'B', 0)
                               .add_field('null2', 'B', 0)
                               .add_field('null3', 'B', 0)
                               .add_field('null4', 'B', 0)
                               .add_field('null5', 'B', 0))

        self.client = PLCClient(ip, port, self.plc_struct_rcv)

        if self.client.connect():
            self.connected = True
            self.running = True
            self.connection_status.set("Connected")
            self.connect_btn.config(text="Disconnect", bg='#f44336')

            # Start communication thread
            self.comm_thread = threading.Thread(target=self.communication_loop, daemon=True)
            self.comm_thread.start()
        else:
            self.connection_status.set("Failed")

    def disconnect_from_plc(self):
        """Disconnect from PLC"""
        self.running = False
        if self.client:
            self.client.close()
        self.connected = False
        self.connection_status.set("Disconnected")
        self.connect_btn.config(text="Connect", bg='#4CAF50')

    def communication_loop(self):
        """Main communication loop running in separate thread"""
        plc_struct_snd = (PLCData()
                          .add_field('EstopCMD', 'B', 0)
                          .add_field('ResetCMD', 'B', 0)
                          .add_field('ResetRadarsCMD', 'B', 0)
                          .add_field('BypassRadarsCMD', 'B', 0)
                          .add_field('ChangeZonesCMD', 'B', 0)
                          .add_field('null1', 'B', 0)
                          .add_field('null2', 'B', 0)
                          .add_field('null3', 'B', 0)
                          .add_field('null4', 'B', 0)
                          .add_field('null5', 'B', 0))

        while self.running:
            # Prepare send data
            send_data = plc_struct_snd.clone()
            send_data.set('EstopCMD', 1 if self.estop_active.get() else 0)
            send_data.set('ResetCMD', 0)  # Momentary handled separately
            send_data.set('ResetRadarsCMD', 1 if self.reset_radars_active.get() else 0)
            send_data.set('BypassRadarsCMD', 1 if self.bypass_radars_active.get() else 0)
            send_data.set('ChangeZonesCMD', 1 if self.change_zones_active.get() else 0)

            send_data.set('null1', 1 if self.estop_pc_bypass.get() else 0)
            send_data.set('null2', 1 if self.value_1.get() else 0)
            send_data.set('null3', 1 if self.value_2.get() else 0)
            send_data.set('null4', 1 if self.value_3.get() else 0)
            send_data.set('null5', 1 if self.value_4.get() else 0)


            # Send to PLC
            if self.client.send(send_data):
                self.conn_mon.record_success()
            else:
                self.conn_mon.record_failure("Send failed")

            # Receive from PLC
            recv_data = self.client.receive()

            if recv_data:
                self.conn_mon.record_success()
                self.update_feedback(recv_data)
            else:
                self.conn_mon.record_failure("Receive failed")

            # Update frequency display
            freq = self.freq_mon.tick()
            if freq:
                self.loop_frequency.set(f"{freq:.2f} Hz")

            # Update success rate
            stats = self.conn_mon.get_stats()
            if stats:
                self.success_rate.set(f"{stats['success_rate']:.1f}%")

            self.rate_limiter.sleep()

    def update_feedback(self, recv_data):
        """Update feedback indicators from PLC data"""
        fields = [
            ('estop_cart', self.estop_cart_status),
            ('estop_off', self.estop_off_status),
            ('radar_red', self.radar_red_status),
            ('radar_yell', self.radar_yell_status),
            ('reset_btn', self.reset_btn_status),
            ('null1', self.rcv_val_1),
            ('null2', self.rcv_val_2),
            ('null3', self.rcv_val_3),
            ('null4', self.rcv_val_4),
            ('null5', self.rcv_val_5)
        ]

        for field_name, var in fields:
            value = recv_data.get(field_name)
            is_on = bool(value)
            var.set("ON" if is_on else "OFF")

            # Update color
            label = self.feedback_labels[field_name]
            if is_on:
                label.config(fg='#00ff00', bg='#003300')  # Green
            else:
                label.config(fg='#ff0000', bg='#555')  # Red


def main():
    root = tk.Tk()
    app = PLCHMI(root)
    root.mainloop()


if __name__ == "__main__":
    main()