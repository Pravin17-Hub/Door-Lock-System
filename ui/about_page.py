"""
FaceSecure - About Page
Displays product information, developer credits, technology stack, and future extensibility roadmap.
"""

import customtkinter as ctk
from styles import COLORS, FONTS, RADIUS


class AboutPage(ctk.CTkFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        self.app = app_controller
        self._build_page()

    def _build_page(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Title
        title_lbl = ctk.CTkLabel(self, text="ℹ️ About FaceSecure", font=FONTS["title_large"], text_color=COLORS["text_primary"])
        title_lbl.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        # Scrollable Content Box
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")

        # Project Info Banner Card
        card = ctk.CTkFrame(content, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=6)

        ctk.CTkLabel(card, text="🛡️ DoorCam - Access Control System", font=FONTS["title_medium"], text_color=COLORS["accent_glow"]).pack(anchor="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(card, text="Portable Face Recognition Access Control System using Arduino & OpenCV", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(0, 10))

        # Metadata Grid
        meta_box = ctk.CTkFrame(card, fg_color=COLORS["bg_card"], corner_radius=RADIUS["button"])
        meta_box.pack(fill="x", padx=16, pady=(0, 16))

        info_items = [
            ("Application Title:", "FaceSecure"),
            ("Version:", "v1.0.0 (Production Release)"),
            ("Developer:", "Pravin Kumar / Antigravity Engineering"),
            ("License:", "Proprietary Commercial Security Suite"),
            ("Target OS:", "Windows 10 / 11 Desktop (Executable Ready)")
        ]

        for k, v in info_items:
            row = ctk.CTkFrame(meta_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=k, font=FONTS["small"], text_color=COLORS["text_secondary"], width=160, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=v, font=FONTS["body_bold"], text_color=COLORS["text_primary"], anchor="w").pack(side="left")

        # Technology Stack Card
        tech_card = ctk.CTkFrame(content, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        tech_card.pack(fill="x", pady=8)

        ctk.CTkLabel(tech_card, text="🛠️ Built With Modern Technology Stack", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 6))

        techs = [
            "🐍 Python 3.12 - Core Execution Language",
            "🎨 CustomTkinter v6.0 - Modern Dark Blue Desktop GUI",
            "📷 OpenCV (cv2) - High Performance Camera Stream & Video Processing",
            "👤 face_recognition & dlib / LBPH Engine - Facial Landmark Feature Matcher",
            "🔌 PySerial - Real-Time Microcontroller USB Serial Communication",
            "🗄️ SQLite3 - Embedded Local Relational Database Storage"
        ]

        for t in techs:
            ctk.CTkLabel(tech_card, text=f"•  {t}", font=FONTS["body"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(tech_card, text="", font=FONTS["small"]).pack(pady=4)

        # Future Expansion Roadmap Card
        future_card = ctk.CTkFrame(content, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        future_card.pack(fill="x", pady=8)

        ctk.CTkLabel(future_card, text="🚀 Future Extensibility Architecture Roadmap", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 6))

        features = [
            "☝️ Fingerprint Biometric Hardware Subsystem",
            "🔑 Two-Factor OTP Verification Interlock",
            "☁️ Cloud Synchronization & Remote Audit Logging",
            "📱 Mobile Application Remote Lock / Unlock Gateway",
            "✉️ Instant Email Security Breach Alerts",
            "💬 SMS Instant Notification Webhooks",
            "📹 Multi-Camera RTSP Stream Network Support"
        ]

        for f in features:
            ctk.CTkLabel(future_card, text=f"✔️  {f}", font=FONTS["body"], text_color=COLORS["status_success"]).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(future_card, text="", font=FONTS["small"]).pack(pady=4)
