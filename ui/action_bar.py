"""
FaceSecure - Action Bar Component
Bottom bar with four large action buttons: Start Camera, Register Face, Start Recognition, and Connect Arduino.
"""

import customtkinter as ctk
from styles import COLORS, FONTS, RADIUS


class ActionBarFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_start_camera=None,
        on_register_face=None,
        on_start_recognition=None,
        on_connect_arduino=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        self.on_start_camera = on_start_camera
        self.on_register_face = on_register_face
        self.on_start_recognition = on_start_recognition
        self.on_connect_arduino = on_connect_arduino

        self._build_action_bar()

    def _build_action_bar(self):
        # Evenly spread 4 columns
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Start Camera Button
        self.btn_camera = ctk.CTkButton(
            self,
            text="🎥  Start Camera",
            font=FONTS["action_button"],
            height=46,
            corner_radius=RADIUS["button"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_primary"],
            command=self._handle_camera_click
        )
        self.btn_camera.grid(row=0, column=0, padx=(12, 6), pady=10, sticky="ew")

        # 2. Register Face Button
        self.btn_register = ctk.CTkButton(
            self,
            text="👤  Register Face",
            font=FONTS["action_button"],
            height=46,
            corner_radius=RADIUS["button"],
            fg_color=COLORS["bg_card_alt"],
            hover_color=COLORS["border_light"],
            border_width=1,
            border_color=COLORS["border_light"],
            text_color=COLORS["text_primary"],
            command=self._handle_register_click
        )
        self.btn_register.grid(row=0, column=1, padx=6, pady=10, sticky="ew")

        # 3. Start Recognition Button
        self.btn_recognition = ctk.CTkButton(
            self,
            text="🔍  Start Recognition",
            font=FONTS["action_button"],
            height=46,
            corner_radius=RADIUS["button"],
            fg_color=COLORS["bg_card_alt"],
            hover_color=COLORS["border_light"],
            border_width=1,
            border_color=COLORS["border_light"],
            text_color=COLORS["text_primary"],
            command=self._handle_recognition_click
        )
        self.btn_recognition.grid(row=0, column=2, padx=6, pady=10, sticky="ew")

        # 4. Connect Arduino Button
        self.btn_arduino = ctk.CTkButton(
            self,
            text="🔌  Connect Arduino",
            font=FONTS["action_button"],
            height=46,
            corner_radius=RADIUS["button"],
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            text_color=COLORS["text_primary"],
            command=self._handle_arduino_click
        )
        self.btn_arduino.grid(row=0, column=3, padx=(6, 12), pady=10, sticky="ew")

    def _handle_camera_click(self):
        if self.on_start_camera:
            self.on_start_camera()

    def _handle_register_click(self):
        if self.on_register_face:
            self.on_register_face()

    def _handle_recognition_click(self):
        if self.on_start_recognition:
            self.on_start_recognition()

    def _handle_arduino_click(self):
        if self.on_connect_arduino:
            self.on_connect_arduino()

    # Toggle helper for Camera button text & styling
    def set_camera_button_active(self, is_active: bool):
        if is_active:
            self.btn_camera.configure(
                text="⏹️  Stop Camera",
                fg_color=COLORS["status_danger"],
                hover_color="#D63056"
            )
        else:
            self.btn_camera.configure(
                text="🎥  Start Camera",
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"]
            )

    # Toggle helper for Recognition button text & styling
    def set_recognition_button_active(self, is_active: bool):
        if is_active:
            self.btn_recognition.configure(
                text="⏹️  Stop Recognition",
                fg_color=COLORS["status_danger"],
                hover_color="#D63056"
            )
        else:
            self.btn_recognition.configure(
                text="🔍  Start Recognition",
                fg_color=COLORS["bg_card_alt"],
                hover_color=COLORS["border_light"]
            )

    # Toggle helper for Arduino button text & styling
    def set_arduino_button_active(self, is_connected: bool):
        if is_connected:
            self.btn_arduino.configure(
                text="⚡  Disconnect Arduino",
                fg_color=COLORS["status_success"],
                hover_color="#05B386",
                text_color=COLORS["text_dark"]
            )
        else:
            self.btn_arduino.configure(
                text="🔌  Connect Arduino",
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                text_color=COLORS["text_primary"]
            )
