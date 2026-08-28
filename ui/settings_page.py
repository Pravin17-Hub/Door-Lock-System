"""
FaceSecure - Settings Page
Configures system parameters: Camera selection, COM Port, match threshold, door lock duration, theme, and database backup.
"""

import os
import datetime
import customtkinter as ctk
from tkinter import filedialog
from styles import COLORS, FONTS, RADIUS


class SettingsPage(ctk.CTkFrame):
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
        title_lbl = ctk.CTkLabel(self, text="⚙️ System Settings & Preferences", font=FONTS["title_large"], text_color=COLORS["text_primary"])
        title_lbl.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        # Scrollable Settings Container
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")

        # --- Setting 1: Camera Index Selection ---
        self._add_section_header(container, "📹 Camera Settings")

        cam_box = self._create_setting_card(container)
        ctk.CTkLabel(cam_box, text="Active Video Capture Device:", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(side="left", padx=16)

        self.cam_opt = ctk.CTkOptionMenu(
            cam_box,
            values=["Camera 0 (Default)", "Camera 1", "Camera 2"],
            width=180,
            command=self._save_camera
        )
        current_cam = self.app.config.get("camera_index", 0)
        self.cam_opt.set(f"Camera {current_cam}")
        self.cam_opt.pack(side="right", padx=16, pady=10)

        # --- Setting 2: Arduino COM Port Selection ---
        self._add_section_header(container, "🔌 Arduino Hardware Settings")

        com_box = self._create_setting_card(container)
        ctk.CTkLabel(com_box, text="Arduino Serial Port (COM):", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(side="left", padx=16)

        self.btn_refresh_ports = ctk.CTkButton(com_box, text="🔄 Refresh Ports", font=FONTS["small"], width=100, command=self._refresh_ports)
        self.btn_refresh_ports.pack(side="right", padx=(6, 16), pady=10)

        ports = self.app.arduino.get_available_ports()
        port_values = ["AUTO"] + ports if ports else ["AUTO", "No COM Ports Found"]
        self.com_opt = ctk.CTkOptionMenu(com_box, values=port_values, width=160, command=self._save_com_port)
        current_port = self.app.config.get("com_port", "AUTO")
        self.com_opt.set(current_port if current_port in port_values else "AUTO")
        self.com_opt.pack(side="right", padx=6, pady=10)

        # --- Setting 3: Recognition Confidence Threshold ---
        self._add_section_header(container, "🔍 Recognition Engine Parameters")

        thresh_box = self._create_setting_card(container)
        ctk.CTkLabel(thresh_box, text="Match Confidence Threshold:", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(side="left", padx=16)

        self.lbl_thresh_val = ctk.CTkLabel(thresh_box, text=f"{int(self.app.config.get('confidence_threshold', 0.65)*100)}%", font=FONTS["body_bold"], text_color=COLORS["primary"])
        self.lbl_thresh_val.pack(side="right", padx=16)

        self.slider_thresh = ctk.CTkSlider(
            thresh_box,
            from_=0.40,
            to=0.95,
            number_of_steps=55,
            width=220,
            command=self._on_thresh_change
        )
        self.slider_thresh.set(self.app.config.get("confidence_threshold", 0.65))
        self.slider_thresh.pack(side="right", padx=10)

        # --- Setting 4: Door Unlock Duration ---
        duration_box = self._create_setting_card(container)
        ctk.CTkLabel(duration_box, text="Door Auto-Lock Delay (Seconds):", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(side="left", padx=16)

        self.lbl_dur_val = ctk.CTkLabel(duration_box, text=f"{self.app.config.get('door_unlock_duration', 5)} sec", font=FONTS["body_bold"], text_color=COLORS["secondary"])
        self.lbl_dur_val.pack(side="right", padx=16)

        self.slider_dur = ctk.CTkSlider(
            duration_box,
            from_=1,
            to=15,
            number_of_steps=14,
            width=220,
            command=self._on_dur_change
        )
        self.slider_dur.set(self.app.config.get("door_unlock_duration", 5))
        self.slider_dur.pack(side="right", padx=10)

        # --- Setting 5: Appearance Theme Switcher ---
        self._add_section_header(container, "🎨 Appearance & Maintenance")

        theme_box = self._create_setting_card(container)
        ctk.CTkLabel(theme_box, text="Application Color Theme:", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(side="left", padx=16)

        self.theme_opt = ctk.CTkOptionMenu(theme_box, values=["Dark", "Light"], width=140, command=self._save_theme)
        self.theme_opt.set(self.app.config.get("theme", "Dark"))
        self.theme_opt.pack(side="right", padx=16, pady=10)

        # --- Setting 6: Database Backup Trigger ---
        backup_box = self._create_setting_card(container)
        ctk.CTkLabel(backup_box, text="Database Backup & Archival:", font=FONTS["body_bold"], text_color=COLORS["text_primary"]).pack(side="left", padx=16)

        self.btn_backup = ctk.CTkButton(
            backup_box,
            text="💾 Backup Database",
            font=FONTS["action_button"],
            fg_color=COLORS["status_success"],
            hover_color="#05B386",
            command=self.backup_database
        )
        self.btn_backup.pack(side="right", padx=16, pady=10)

    def _add_section_header(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, font=FONTS["small"], text_color=COLORS["text_secondary"], anchor="w")
        lbl.pack(fill="x", padx=4, pady=(14, 4))

    def _create_setting_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["button"], border_width=1, border_color=COLORS["border"], height=52)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)
        return card

    def _save_camera(self, choice):
        idx = int(choice.split()[1])
        self.app.config.set("camera_index", idx)
        self.app.status_bar.set_status(f"Camera index set to {idx}")

    def _refresh_ports(self):
        ports = self.app.arduino.get_available_ports()
        values = ["AUTO"] + ports if ports else ["AUTO", "No COM Ports Found"]
        self.com_opt.configure(values=values)
        self.app.status_bar.set_status("COM ports refreshed.")

    def _save_com_port(self, choice):
        self.app.config.set("com_port", choice)
        self.app.status_bar.set_status(f"Arduino COM port set to {choice}")

    def _on_thresh_change(self, val):
        pct = int(val * 100)
        self.lbl_thresh_val.configure(text=f"{pct}%")
        self.app.config.set("confidence_threshold", float(val))
        self.app.face_engine.confidence_threshold = float(val)

    def _on_dur_change(self, val):
        sec = int(val)
        self.lbl_dur_val.configure(text=f"{sec} sec")
        self.app.config.set("door_unlock_duration", sec)

    def _save_theme(self, choice):
        self.app.config.set("theme", choice)
        ctk.set_appearance_mode(choice)
        self.app.status_bar.set_status(f"Theme updated to {choice}")

    def backup_database(self):
        default_file = f"facesecure_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
            initialfile=default_file
        )
        if dest_path:
            success = self.app.db.backup_database(dest_path)
            if success:
                self.app.status_bar.set_status(f"Database backed up to: {dest_path}", is_success=True)
            else:
                self.app.status_bar.set_status("Failed to back up database.", is_error=True)
