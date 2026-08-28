"""
FaceSecure Web - ESP32 Hardware Serial Manager
Handles USB Serial communication between Flask Web Server and ESP32 / Servo Motor setup.
Includes manual COM port selection (COM1 - COM15) and DTR/RTS reset suppression.
"""

import time
import threading
from typing import List, Optional, Tuple
import serial
import serial.tools.list_ports


class ESP32Manager:
    def __init__(self, port: str = "AUTO", baud_rate: int = 9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.connected_port = ""
        self.last_error = ""
        self._lock = threading.Lock()

    @staticmethod
    def get_available_ports() -> List[Tuple[str, str]]:
        """Scans system COM ports and appends standard COM1-COM15 options."""
        ports = serial.tools.list_ports.comports()
        detected_devices = {p.device for p in ports}

        result = []
        for p in ports:
            result.append((p.device, f"{p.device} - {p.description}"))

        # Append standard COM ports if not already detected
        for i in range(1, 16):
            cname = f"COM{i}"
            if cname not in detected_devices:
                result.append((cname, f"{cname} (Manual USB Selection)"))

        return result

    def connect(self, target_port: str = "") -> Tuple[bool, str]:
        """Establishes real USB Serial connection to ESP32 board on target COM port."""
        with self._lock:
            if self.is_connected:
                self._disconnect_internal()

            selected_port = target_port.strip() if target_port else self.port

            if selected_port in ["AUTO", ""]:
                available = serial.tools.list_ports.comports()
                if not available:
                    self.is_connected = False
                    self.connected_port = ""
                    self.last_error = "No active COM ports detected. Select a specific COM port (e.g. COM3) from the dropdown."
                    return False, self.last_error
                selected_port = available[0].device

            try:
                # Open serial port with DTR/RTS disabled to prevent ESP32 continuous reset loop
                ser = serial.Serial()
                ser.port = selected_port
                ser.baudrate = self.baud_rate
                ser.timeout = 1.0
                ser.write_timeout = 1.0
                ser.dtr = False
                ser.rts = False
                ser.open()

                time.sleep(0.5)
                self.serial_conn = ser
                self.is_connected = ser.is_open
                self.connected_port = selected_port if self.is_connected else ""
                self.last_error = ""
                return True, f"Connected successfully to ESP32 on {selected_port} 🟢"

            except serial.SerialException as se:
                err_str = str(se)
                if "PermissionError" in err_str or "Access denied" in err_str:
                    msg = f"Port {selected_port} is busy! Close Arduino IDE Serial Monitor and try again."
                elif "FileNotFoundError" in err_str or "cannot find" in err_str.lower():
                    msg = f"Port {selected_port} not found. Check USB cable connection."
                else:
                    msg = f"Serial error on {selected_port}: {err_str}"
                
                self.is_connected = False
                self.connected_port = ""
                self.serial_conn = None
                self.last_error = msg
                return False, msg

            except Exception as e:
                msg = f"Could not open {selected_port}: {e}"
                self.is_connected = False
                self.connected_port = ""
                self.serial_conn = None
                self.last_error = msg
                return False, msg

    def disconnect(self):
        with self._lock:
            self._disconnect_internal()

    def _disconnect_internal(self):
        if self.serial_conn:
            try:
                if self.serial_conn.is_open:
                    self.serial_conn.close()
            except Exception:
                pass
        self.is_connected = False
        self.connected_port = ""
        self.serial_conn = None

    def check_connection_status(self) -> bool:
        with self._lock:
            if not self.is_connected or not self.serial_conn:
                return False
            if not self.serial_conn.is_open:
                self._disconnect_internal()
                return False
            return True

    def send_command(self, command: str) -> bool:
        cmd_clean = command.strip().upper()
        with self._lock:
            if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
                return False

            try:
                msg = f"{cmd_clean}\n".encode("utf-8")
                self.serial_conn.write(msg)
                self.serial_conn.flush()
                return True
            except Exception as e:
                print(f"[ESP32Manager] Serial write error: {e}")
                self._disconnect_internal()
                return False

    def send_unlock_auto_lock(self, duration_seconds: int = 5):
        def _worker():
            success = self.send_command("UNLOCK")
            if success:
                time.sleep(duration_seconds)
                self.send_command("LOCK")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
