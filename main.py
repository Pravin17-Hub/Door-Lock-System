"""
FaceSecure - Main Application Entry Point (Light Theme)
DoorCam - Portable Face Recognition Access Control System using Arduino and OpenCV

Orchestrates UI page routing, database operations, OpenCV face recognition engine,
and PySerial Arduino hardware communication in a 1000x700 non-resizable desktop window.
"""

import os
import sys
import customtkinter as ctk

from styles import COLORS, FONTS, RADIUS, apply_global_theme
from utils import setup_logger, ConfigManager
from database_manager import DatabaseManager
from recognition import FaceEngine
from arduino import ArduinoManager
from ui import (
    HeaderFrame,
    SidebarFrame,
    StatusBarFrame,
    DashboardPage,
    CameraPage,
    RegistrationPage,
    RecognitionPage,
    LogsPage,
    SettingsPage,
    AboutPage
)

logger = setup_logger("FaceSecureApp")


class FaceSecureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Load Configurations & Core Systems
        self.config = ConfigManager()
        
        # Default Theme: Light Mode
        saved_theme = self.config.get("theme", "Light")
        apply_global_theme(mode=saved_theme)

        self.db = DatabaseManager()
        self.face_engine = FaceEngine(
            confidence_threshold=self.config.get("confidence_threshold", 0.65)
        )
        self.arduino = ArduinoManager(
            port=self.config.get("com_port", "AUTO"),
            baud_rate=self.config.get("baud_rate", 9600)
        )
        self.arduino.on_status_change = self._on_arduino_status_change

        # App state tracking
        self.camera_running = False

        # 2. Window Configuration (1000x700 Non-resizable)
        self.title("FaceSecure - Access Control System")
        self.geometry("1000x700")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        # Center window on screen
        self.update_idletasks()
        w, h = 1000, 700
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # 3. Build UI Architecture & Layout
        self._build_layout()

        # Auto-connect Arduino if configured
        target_port = self.config.get("com_port", "AUTO")
        self.arduino.connect(target_port)

        # Handle window close cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Main Pages Viewport
        self.grid_rowconfigure(2, weight=0) # Status Bar

        # --- A. Header Bar ---
        self.header = HeaderFrame(self)
        self.header.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="nsew")

        # --- B. Content Container (Left Sidebar + Right Page Stack) ---
        self.content_box = ctk.CTkFrame(self, fg_color="transparent")
        self.content_box.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")

        self.content_box.grid_rowconfigure(0, weight=1)
        self.content_box.grid_columnconfigure(0, weight=0) # Sidebar
        self.content_box.grid_columnconfigure(1, weight=1) # Active Page

        # B1. Sidebar
        self.sidebar = SidebarFrame(self.content_box, on_menu_select=self.show_page)
        self.sidebar.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # B2. Pages Container (Grid Stack)
        self.page_container = ctk.CTkFrame(self.content_box, fg_color="transparent")
        self.page_container.grid(row=0, column=1, padx=(4, 0), sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        # Instantiate all 7 Pages
        self.pages = {
            "Dashboard": DashboardPage(self.page_container, app_controller=self),
            "Camera": CameraPage(self.page_container, app_controller=self),
            "Face Registration": RegistrationPage(self.page_container, app_controller=self),
            "Face Recognition": RecognitionPage(self.page_container, app_controller=self),
            "Access Logs": LogsPage(self.page_container, app_controller=self),
            "Settings": SettingsPage(self.page_container, app_controller=self),
            "About": AboutPage(self.page_container, app_controller=self),
        }

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # Shortcut reference to Status Panel if present
        if "Dashboard" in self.pages and hasattr(self.pages["Dashboard"], "status_panel"):
            self.status_panel = self.pages["Dashboard"].status_panel

        # --- C. Bottom Status Bar ---
        self.status_bar = StatusBarFrame(self, initial_message="System Ready")
        self.status_bar.grid(row=2, column=0, padx=0, pady=(4, 0), sticky="ew")

        # Default page display
        self.show_page("Dashboard")

    def show_page(self, page_name: str):
        """Switches the active page frame."""
        if page_name in self.pages:
            page = self.pages[page_name]
            page.tkraise()

            if hasattr(page, "refresh_dashboard"):
                page.refresh_dashboard()
            elif hasattr(page, "load_logs"):
                page.load_logs()
            elif hasattr(page, "refresh_users_list"):
                page.refresh_users_list()
            elif hasattr(page, "reload_encodings"):
                page.reload_encodings()

            self.status_bar.set_status(f"Navigated to '{page_name}' page")

    def refresh_all_pages(self):
        """Refreshes data across pages when users/logs are updated."""
        if "Dashboard" in self.pages:
            self.pages["Dashboard"].refresh_dashboard()
        if "Access Logs" in self.pages:
            self.pages["Access Logs"].load_logs()
        if "Face Recognition" in self.pages:
            self.pages["Face Recognition"].reload_encodings()

    def _on_arduino_status_change(self, connected: bool, message: str):
        self.header.update_header_statuses(self.camera_running, connected, door_unlocked=False)
        if connected:
            self.status_bar.set_status(f"Arduino Status: {message}", is_success=True)
        else:
            self.status_bar.set_status(f"Arduino Status: {message}", is_error=False)

    def on_close(self):
        """Cleanup resources on application exit."""
        logger.info("Shutting down FaceSecure Application...")
        try:
            if hasattr(self.pages["Camera"], "stop_camera"):
                self.pages["Camera"].stop_camera()
            if hasattr(self.pages["Face Registration"], "stop_cam"):
                self.pages["Face Registration"].stop_cam()
            if hasattr(self.pages["Face Recognition"], "stop_recognition"):
                self.pages["Face Recognition"].stop_recognition()

            self.arduino.disconnect()
        except Exception as e:
            logger.error(f"Error during shutdown cleanup: {e}")

        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = FaceSecureApp()
    app.mainloop()
