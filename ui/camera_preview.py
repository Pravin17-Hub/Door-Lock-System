"""
FaceSecure - Camera Preview Component
Displays central camera live feed preview or a high-quality camera placeholder graphic when offline.
"""

import os
import customtkinter as ctk
from PIL import Image, ImageDraw
from styles import COLORS, FONTS, RADIUS


class CameraPreviewFrame(ctk.CTkFrame):
    def __init__(self, master, placeholder_path="assets/camera_placeholder.png", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        self.placeholder_path = placeholder_path
        self.is_camera_on = False
        self._build_preview()

    def _build_preview(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Center Container for Image / Canvas
        self.preview_container = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_status"],
            corner_radius=RADIUS["card"] - 2,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.preview_container.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.preview_container.grid_rowconfigure(0, weight=1)
        self.preview_container.grid_columnconfigure(0, weight=1)

        # Image Label for Offline Placeholder / Camera Feed
        self.image_label = ctk.CTkLabel(
            self.preview_container,
            text="",
            corner_radius=RADIUS["card"] - 2
        )
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Load placeholder asset
        self._load_placeholder()

        # Top-left Status Overlay Badge
        self.overlay_badge = ctk.CTkFrame(
            self.preview_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["pill"],
            border_width=1,
            border_color=COLORS["border_light"]
        )
        self.overlay_badge.place(relx=0.03, rely=0.04, anchor="nw")

        self.status_dot = ctk.CTkLabel(
            self.overlay_badge,
            text="●",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["status_danger"]
        )
        self.status_dot.pack(side="left", padx=(10, 4), pady=3)

        self.status_text_label = ctk.CTkLabel(
            self.overlay_badge,
            text="CAMERA OFFLINE",
            font=FONTS["badge"],
            text_color=COLORS["text_primary"]
        )
        self.status_text_label.pack(side="left", padx=(0, 10), pady=3)

        # Center Informational Overlay Box
        self.info_overlay = ctk.CTkFrame(
            self.preview_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border_light"]
        )
        self.info_overlay.place(relx=0.5, rely=0.82, anchor="center")

        self.info_label = ctk.CTkLabel(
            self.info_overlay,
            text="📷 Click 'Start Camera' below to launch live recognition preview",
            font=FONTS["body_bold"],
            text_color=COLORS["text_secondary"]
        )
        self.info_label.pack(padx=20, pady=10)

    def _load_placeholder(self):
        if os.path.exists(self.placeholder_path):
            pil_img = Image.open(self.placeholder_path)
            # CTkImage sized appropriately for 520x370 preview box
            self.placeholder_ctk = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=(520, 350)
            )
            self.image_label.configure(image=self.placeholder_ctk, text="")
        else:
            self.image_label.configure(
                text="[ Camera Preview Unavailable ]",
                font=FONTS["title_medium"],
                text_color=COLORS["text_secondary"]
            )

    def set_camera_state(self, is_on: bool):
        """Updates the camera preview display state."""
        self.is_camera_on = is_on
        if is_on:
            self.status_dot.configure(text_color=COLORS["status_success"])
            self.status_text_label.configure(text="LIVE FEED ACTIVE")
            self.info_label.configure(
                text="🟢 Live Feed Active (UI Demo Mode - OpenCV connection pending)",
                text_color=COLORS["status_success"]
            )
            # Generate simulated active preview background
            active_img = Image.new("RGB", (520, 350), "#0B1D3A")
            draw = ImageDraw.Draw(active_img)
            # Draw facial scanning box graphic
            draw.rectangle([180, 80, 340, 260], outline="#00B4D8", width=3)
            draw.line([(180, 170), (340, 170)], fill="#00E5FF", width=2) # Scan line
            draw.text((215, 270), "FACE MATCH: 98.4%", fill="#06D6A0")

            self.active_ctk = ctk.CTkImage(light_image=active_img, dark_image=active_img, size=(520, 350))
            self.image_label.configure(image=self.active_ctk)
        else:
            self.status_dot.configure(text_color=COLORS["status_danger"])
            self.status_text_label.configure(text="CAMERA OFFLINE")
            self.info_label.configure(
                text="📷 Click 'Start Camera' below to launch live recognition preview",
                text_color=COLORS["text_secondary"]
            )
            self._load_placeholder()
