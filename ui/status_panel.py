"""
FaceSecure - System Status Panel Component (Light Theme)
Right-side status panel displaying Camera Status, Arduino Status, Door Status, Registered Users count, and Today's Access Count.
"""

import customtkinter as ctk
from styles import COLORS, FONTS, RADIUS


class StatusPanelFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"],
            width=240,
            **kwargs
        )
        
        self.widgets = {}
        self._build_panel()

    def _build_panel(self):
        # Header title
        self.panel_header = ctk.CTkLabel(
            self,
            text="SYSTEM STATUS",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.panel_header.pack(fill="x", padx=16, pady=(16, 12))

        # Default Door status is CLOSED 🔒 (Locked)
        status_items = [
            ("camera", "Camera Status", "Offline 🔴", True, "status_danger", "📹"),
            ("arduino", "Arduino Status", "Disconnected 🔴", True, "status_danger", "🔌"),
            ("door", "Door Lock Status", "Door Closed 🔒", True, "status_warning", "🚪"),
            ("users", "Registered Users", "0 Users", False, "text_primary", "👥"),
            ("logs", "Today's Access", "0 Verification Logs", False, "text_primary", "📋"),
        ]

        for key, label_text, default_val, is_badge, color_key, icon in status_items:
            card = ctk.CTkFrame(
                self,
                fg_color=COLORS["bg_card_alt"],
                corner_radius=RADIUS["button"],
                border_width=1,
                border_color=COLORS["border"]
            )
            card.pack(fill="x", padx=12, pady=5)

            title_row = ctk.CTkFrame(card, fg_color="transparent")
            title_row.pack(fill="x", padx=10, pady=(8, 2))

            icon_lbl = ctk.CTkLabel(title_row, text=icon, font=("Segoe UI", 12))
            icon_lbl.pack(side="left", padx=(0, 6))

            title_lbl = ctk.CTkLabel(title_row, text=label_text, font=FONTS["small"], text_color=COLORS["text_secondary"], anchor="w")
            title_lbl.pack(side="left")

            val_lbl = ctk.CTkLabel(card, text=default_val, font=FONTS["body_bold"], text_color=COLORS[color_key], anchor="w")
            val_lbl.pack(fill="x", padx=10, pady=(0, 8))

            self.widgets[key] = val_lbl

    def update_status(self, key, text, color=None):
        if key in self.widgets:
            self.widgets[key].configure(text=text)
            if color:
                self.widgets[key].configure(text_color=color)

    def set_camera_status(self, active: bool):
        if active:
            self.update_status("camera", "Live / Active 🟢", COLORS["status_success"])
        else:
            self.update_status("camera", "Offline 🔴", COLORS["status_danger"])

    def set_arduino_status(self, connected: bool):
        if connected:
            self.update_status("arduino", "Connected 🟢", COLORS["status_success"])
        else:
            self.update_status("arduino", "Disconnected 🔴", COLORS["status_danger"])

    def set_door_status(self, opened: bool):
        if opened:
            self.update_status("door", "Door Opened 🔓", COLORS["status_success"])
        else:
            self.update_status("door", "Door Closed 🔒", COLORS["status_warning"])
