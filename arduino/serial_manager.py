"""
FaceSecure - Arduino Serial Communication Manager
Handles serial port discovery, connection, command transmission (UNLOCK, LOCK, ALARM), and auto-reconnection.
"""

import time
import threading
from typing import List, Optional, Callable
import serial
import serial.tools.list_ports
from utils.logger import setup_logger

logger = setup_logger("ArduinoManager")


class ArduinoManager:
    def __init__(self, port: str = "AUTO", baud_rate: int = 9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.connected_port = ""
        self.on_status_change: Optional[Callable[[bool, str], None]] = None

        # Lock for thread safety
        self._lock = threading.Lock()

    @staticmethod
    def get_available_ports() -> List[str]:
        """Scans system for active COM ports."""
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        logger.info(f"Available COM ports detected: {port_list}")
        return port_list

    def connect(self, target_port: str = "") -> bool:
        """Connects to the specified COM port or auto-detects Arduino."""
        with self._lock:
            if self.is_connected:
                self.disconnect()

            selected_port = target_port if target_port else self.port

            if selected_port == "AUTO":
                available = self.get_available_ports()
                if not available:
                    logger.warning("No COM ports available for auto-connect.")
                    self._update_status(False, "No COM ports found")
                    return False
                selected_port = available[0] # Select first active port

            try:
                logger.info(f"Attempting serial connection to {selected_port} at {self.baud_rate} baud...")
                self.serial_conn = serial.Serial(
                    port=selected_port,
                    baudrate=self.baud_rate,
                    timeout=2
                )
                time.sleep(1.5) # Wait for Arduino serial reset
                self.is_connected = True
                self.connected_port = selected_port
                logger.info(f"Arduino successfully connected on {selected_port}")
                self._update_status(True, f"Connected ({selected_port})")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to serial port {selected_port}: {e}")
                self.is_connected = False
                self.connected_port = ""
                self._update_status(False, f"Connection Failed: {e}")
                return False

    def disconnect(self):
        """Disconnects serial connection safely."""
        with self._lock:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except Exception as e:
                    logger.error(f"Error closing serial port: {e}")
            self.is_connected = False
            self.connected_port = ""
            self.serial_conn = None
            logger.info("Arduino serial port disconnected.")
            self._update_status(False, "Disconnected")

    def send_command(self, command: str) -> bool:
        """Transmits serial text command (e.g., UNLOCK, LOCK, ALARM)."""
        cmd_clean = command.strip().upper()
        if cmd_clean not in ["UNLOCK", "LOCK", "ALARM"]:
            logger.warning(f"Unrecognized command: {cmd_clean}")

        with self._lock:
            if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
                logger.warning(f"Cannot send '{cmd_clean}' - Arduino is disconnected.")
                return False

            try:
                msg = f"{cmd_clean}\n".encode("utf-8")
                self.serial_conn.write(msg)
                self.serial_conn.flush()
                logger.info(f"Serial command transmitted: '{cmd_clean}' -> {self.connected_port}")
                return True
            except Exception as e:
                logger.error(f"Serial transmission error sending '{cmd_clean}': {e}")
                self.is_connected = False
                self.connected_port = ""
                self._update_status(False, "Port Transmission Error")
                return False

    def send_unlock_auto_lock(self, duration_seconds: int = 5):
        """Sends UNLOCK, waits duration, then sends LOCK automatically in a background thread."""
        def _worker():
            success = self.send_command("UNLOCK")
            if success:
                logger.info(f"Door UNLOCKED. Auto-lock scheduled in {duration_seconds} seconds.")
                time.sleep(duration_seconds)
                self.send_command("LOCK")
                logger.info("Door auto-locked.")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _update_status(self, connected: bool, message: str):
        if self.on_status_change:
            try:
                self.on_status_change(connected, message)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")
