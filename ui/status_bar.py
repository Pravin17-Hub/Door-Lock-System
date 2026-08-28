"""
FaceSecure - Status Bar Component (Light Theme)
Bottom footer status bar displaying system messages (default: "Ready").
"""

import customtkinter as ctk
from styles import COLORS, FONTS, RADIUS


class StatusBarFrame(ctk.CTkFrame):
    def __init__(self, master, initial_message="Ready", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card_alt"],
            corner_radius=0,
            height=28,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        self.initial_message = initial_message
        self._build_status_bar()

    def _build_status_bar(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Status Icon dot
        self.icon_label = ctk.CTkLabel(
            self,
            text="●",
            font=("Segoe UI", 10, "bold"),
            text_color=COLORS["primary"]
        )
        self.icon_label.grid(row=0, column=0, padx=(12, 6), pady=2, sticky="w")

        # Main Status Text Label
        self.status_label = ctk.CTkLabel(
            self,
            text=self.initial_message,
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, padx=0, pady=2, sticky="ew")

        # Right-side Mode Label
        self.mode_label = ctk.CTkLabel(
            self,
            text="FaceSecure v1.0 | Light Suite",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.mode_label.grid(row=0, column=2, padx=(0, 16), pady=2, sticky="e")

    def set_status(self, message: str, is_error: bool = False, is_success: bool = False):
        """Updates the message shown on the status bar."""
        self.status_label.configure(text=message)
        
        if is_error:
            self.icon_label.configure(text_color=COLORS["status_danger"])
            self.status_label.configure(text_color=COLORS["status_danger"])
        elif is_success:
            self.icon_label.configure(text_color=COLORS["status_success"])
            self.status_label.configure(text_color=COLORS["status_success"])
        else:
            self.icon_label.configure(text_color=COLORS["primary"])
            self.status_label.configure(text_color=COLORS["text_secondary"])
