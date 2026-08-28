"""
FaceSecure - Dashboard Page
Overview of system metrics, live status cards, and recent access logs.
"""

import customtkinter as ctk
from styles import COLORS, FONTS, RADIUS


class DashboardPage(ctk.CTkFrame):
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
        self.metric_labels = {}
        self._build_page()

    def _build_page(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Title
        title_lbl = ctk.CTkLabel(
            self,
            text="📊 System Security Dashboard",
            font=FONTS["title_large"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        title_lbl.grid(row=0, column=0, padx=20, pady=(16, 12), sticky="w")

        # --- Section 1: 3 Main Status Cards (Camera, Arduino, Door) ---
        status_container = ctk.CTkFrame(self, fg_color="transparent")
        status_container.grid(row=1, column=0, padx=16, pady=4, sticky="ew")

        for i in range(3):
            status_container.grid_columnconfigure(i, weight=1)

        # Card 1: Camera Status
        self.card_camera = self._create_status_card(
            status_container, 0, "Camera Status", "Offline 🔴", COLORS["status_danger"], "📹"
        )
        # Card 2: Arduino Status
        self.card_arduino = self._create_status_card(
            status_container, 1, "Arduino Serial", "Disconnected 🔴", COLORS["status_danger"], "🔌"
        )
        # Card 3: Door Status
        self.card_door = self._create_status_card(
            status_container, 2, "Door Mechanism", "Locked 🔒", COLORS["status_warning"], "🚪"
        )

        # --- Section 2: 3 Numerical Metric Cards (Users, Today Access, Unknown Attempts) ---
        metrics_container = ctk.CTkFrame(self, fg_color="transparent")
        metrics_container.grid(row=2, column=0, padx=16, pady=6, sticky="ew")

        for i in range(3):
            metrics_container.grid_columnconfigure(i, weight=1)

        self.metric_users = self._create_metric_card(
            metrics_container, 0, "Registered Users", "0 Users", "👥", COLORS["secondary"]
        )
        self.metric_today = self._create_metric_card(
            metrics_container, 1, "Today's Access", "0 Verification Logs", "📋", COLORS["primary"]
        )
        self.metric_unknown = self._create_metric_card(
            metrics_container, 2, "Unknown Attempts", "0 Alerts", "⚠️", COLORS["status_danger"]
        )

        # --- Section 3: Recent Activity Log Overview ---
        recent_container = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card_alt"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"]
        )
        recent_container.grid(row=3, column=0, padx=16, pady=(8, 16), sticky="nsew")

        recent_header = ctk.CTkLabel(
            recent_container,
            text="RECENT ACCESS LOGS",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        recent_header.pack(fill="x", padx=16, pady=(12, 6))

        # Scrollable recent log frame
        self.recent_logs_frame = ctk.CTkScrollableFrame(
            recent_container,
            fg_color="transparent",
            height=130
        )
        self.recent_logs_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.refresh_dashboard()

    def _create_status_card(self, parent, col, title, initial_val, val_color, icon):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card_alt"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"]
        )
        card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 2))

        lbl_icon = ctk.CTkLabel(header, text=icon, font=("Segoe UI", 14))
        lbl_icon.pack(side="left", padx=(0, 6))

        lbl_title = ctk.CTkLabel(header, text=title, font=FONTS["small"], text_color=COLORS["text_secondary"])
        lbl_title.pack(side="left")

        val_lbl = ctk.CTkLabel(card, text=initial_val, font=FONTS["body_bold"], text_color=val_color, anchor="w")
        val_lbl.pack(fill="x", padx=12, pady=(0, 10))
        return val_lbl

    def _create_metric_card(self, parent, col, title, initial_val, icon, accent_color):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card_alt"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"]
        )
        card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")

        lbl_icon = ctk.CTkLabel(card, text=icon, font=("Segoe UI", 20))
        lbl_icon.pack(anchor="w", padx=14, pady=(12, 2))

        lbl_val = ctk.CTkLabel(card, text=initial_val, font=FONTS["title_medium"], text_color=COLORS["text_primary"], anchor="w")
        lbl_val.pack(fill="x", padx=14, pady=0)

        lbl_title = ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color=COLORS["text_secondary"], anchor="w")
        lbl_title.pack(fill="x", padx=14, pady=(0, 12))
        return lbl_val

    def refresh_dashboard(self):
        """Updates counts and metrics from database and app controller state."""
        counts = self.app.db.get_dashboard_counts()
        self.metric_users.configure(text=f"{counts['users']} Users")
        self.metric_today.configure(text=f"{counts['today_access']} Logs")
        self.metric_unknown.configure(text=f"{counts['unknown_attempts']} Alerts")

        # Update status cards
        if self.app.camera_running:
            self.card_camera.configure(text="Live 🟢", text_color=COLORS["status_success"])
        else:
            self.card_camera.configure(text="Offline 🔴", text_color=COLORS["status_danger"])

        if self.app.arduino.is_connected:
            self.card_arduino.configure(text=f"Connected ({self.app.arduino.connected_port}) 🟢", text_color=COLORS["status_success"])
            self.card_door.configure(text="Ready / Unlocked 🔓", text_color=COLORS["status_success"])
        else:
            self.card_arduino.configure(text="Disconnected 🔴", text_color=COLORS["status_danger"])
            self.card_door.configure(text="Locked 🔒", text_color=COLORS["status_warning"])

        # Populate recent access logs feed
        for widget in self.recent_logs_frame.winfo_children():
            widget.destroy()

        logs = self.app.db.get_filtered_logs(status_filter="All")[:5] # Latest 5 logs
        if not logs:
            empty_lbl = ctk.CTkLabel(
                self.recent_logs_frame,
                text="No access logs recorded yet.",
                font=FONTS["body"],
                text_color=COLORS["text_secondary"]
            )
            empty_lbl.pack(pady=20)
        else:
            for log in logs:
                row = ctk.CTkFrame(self.recent_logs_frame, fg_color=COLORS["bg_card"], corner_radius=RADIUS["input"])
                row.pack(fill="x", pady=2, padx=4)

                status_color = COLORS["status_success"] if "GRANTED" in log["status"].upper() else COLORS["status_danger"]
                
                name_lbl = ctk.CTkLabel(row, text=f"{log['user_name']}", font=FONTS["body_bold"], text_color=COLORS["text_primary"], width=120, anchor="w")
                name_lbl.pack(side="left", padx=10, pady=6)

                status_lbl = ctk.CTkLabel(row, text=log["status"], font=FONTS["badge"], text_color=status_color, width=130, anchor="w")
                status_lbl.pack(side="left", padx=10, pady=6)

                conf_lbl = ctk.CTkLabel(row, text=f"{log['confidence']}%", font=FONTS["small"], text_color=COLORS["text_secondary"], width=60)
                conf_lbl.pack(side="left", padx=10, pady=6)

                time_lbl = ctk.CTkLabel(row, text=f"{log['date']} {log['time']}", font=FONTS["small"], text_color=COLORS["text_secondary"])
                time_lbl.pack(side="right", padx=10, pady=6)
