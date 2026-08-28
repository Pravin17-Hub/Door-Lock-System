"""
FaceSecure - Header Component (Light Theme)
Top header bar with logo, application title, and live status badges for Camera, Arduino, and Door.
"""

import os
import customtkinter as ctk
from PIL import Image
from styles import COLORS, FONTS, RADIUS


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, logo_path="assets/logo.png", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_header"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        self.logo_path = logo_path
        self._build_header()

    def _build_header(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Logo Icon
        if os.path.exists(self.logo_path):
            pil_image = Image.open(self.logo_path)
            self.logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(46, 46))
            self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
            self.logo_label.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=10, sticky="w")
        else:
            self.logo_label = ctk.CTkLabel(self, text="🛡️", font=("Segoe UI", 26), text_color=COLORS["primary"])
            self.logo_label.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=10, sticky="w")

        # App Title & Subtitle Container
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=1, padx=0, pady=10, sticky="w")

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="FaceSecure",
            font=FONTS["title_large"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="DoorCam – Portable Face Recognition Access Control System",
            font=FONTS["header_sub"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.subtitle_label.pack(anchor="w")

        # Right Side Live Status Indicators
        self.badge_box = ctk.CTkFrame(self, fg_color="transparent")
        self.badge_box.grid(row=0, column=2, padx=16, pady=10, sticky="e")

        # Badge 1: Camera Status
        self.badge_cam = self._create_badge(self.badge_box, "CAM: OFF", COLORS["status_danger"])
        self.badge_cam.pack(side="left", padx=4)

        # Badge 2: Arduino Status
        self.badge_ard = self._create_badge(self.badge_box, "ARDUINO: OFF", COLORS["status_danger"])
        self.badge_ard.pack(side="left", padx=4)

        # Badge 3: Door Status (DEFAULT: CLOSED / LOCKED)
        self.badge_door = self._create_badge(self.badge_box, "DOOR: CLOSED 🔒", COLORS["status_warning"])
        self.badge_door.pack(side="left", padx=4)

    def _create_badge(self, parent, text, color):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["pill"], border_width=1, border_color=COLORS["border"])
        dot = ctk.CTkLabel(frame, text="●", font=("Segoe UI", 10, "bold"), text_color=color)
        dot.pack(side="left", padx=(8, 3), pady=3)

        lbl = ctk.CTkLabel(frame, text=text, font=FONTS["badge"], text_color=COLORS["text_primary"])
        lbl.pack(side="left", padx=(0, 8), pady=3)
        frame.dot_lbl = dot
        frame.text_lbl = lbl
        return frame

    def update_header_statuses(self, camera_on: bool, arduino_conn: bool, door_unlocked: bool = False):
        if camera_on:
            self.badge_cam.dot_lbl.configure(text_color=COLORS["status_success"])
            self.badge_cam.text_lbl.configure(text="CAM: LIVE 🟢")
        else:
            self.badge_cam.dot_lbl.configure(text_color=COLORS["status_danger"])
            self.badge_cam.text_lbl.configure(text="CAM: OFF 🔴")

        if arduino_conn:
            self.badge_ard.dot_lbl.configure(text_color=COLORS["status_success"])
            self.badge_ard.text_lbl.configure(text="ARDUINO: CONNECTED 🟢")
        else:
            self.badge_ard.dot_lbl.configure(text_color=COLORS["status_danger"])
            self.badge_ard.text_lbl.configure(text="ARDUINO: DISCONNECTED 🔴")

        if door_unlocked:
            self.badge_door.dot_lbl.configure(text_color=COLORS["status_success"])
            self.badge_door.text_lbl.configure(text="DOOR: OPENED 🔓")
        else:
            self.badge_door.dot_lbl.configure(text_color=COLORS["status_warning"])
            self.badge_door.text_lbl.configure(text="DOOR: CLOSED 🔒")
