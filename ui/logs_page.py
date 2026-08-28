"""
FaceSecure - Access Logs Page
Displays SQLite access logs with search, status filtering, date filtering, log deletion, and CSV export.
"""

import os
import csv
import datetime
import customtkinter as ctk
from tkinter import filedialog
from styles import COLORS, FONTS, RADIUS


class LogsPage(ctk.CTkFrame):
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
        self.grid_rowconfigure(2, weight=1)

        # Header Title
        title_lbl = ctk.CTkLabel(self, text="📋 Access Audit Logs & Reports", font=FONTS["title_large"], text_color=COLORS["text_primary"])
        title_lbl.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        # --- Filter & Action Controls Bar ---
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        bar.grid(row=1, column=0, padx=20, pady=4, sticky="ew")

        # Search Entry
        self.search_entry = ctk.CTkEntry(bar, placeholder_text="🔍 Search Name...", width=180, font=FONTS["body"])
        self.search_entry.pack(side="left", padx=(12, 6), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_logs())

        # Status Filter Dropdown
        self.status_filter = ctk.CTkOptionMenu(
            bar,
            values=["All", "ACCESS GRANTED", "ACCESS DENIED"],
            width=150,
            command=lambda v: self.load_logs()
        )
        self.status_filter.pack(side="left", padx=6, pady=10)

        # Date Entry Filter
        self.date_entry = ctk.CTkEntry(bar, placeholder_text="YYYY-MM-DD", width=120, font=FONTS["body"])
        self.date_entry.pack(side="left", padx=6, pady=10)
        self.date_entry.bind("<KeyRelease>", lambda e: self.load_logs())

        # Action Buttons Right
        self.btn_export = ctk.CTkButton(
            bar,
            text="📥 Export CSV",
            font=FONTS["action_button"],
            width=110,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            command=self.export_csv
        )
        self.btn_export.pack(side="right", padx=(6, 12), pady=10)

        self.btn_clear = ctk.CTkButton(
            bar,
            text="🗑️ Clear Logs",
            font=FONTS["action_button"],
            width=110,
            fg_color=COLORS["status_danger"],
            command=self.clear_all_logs
        )
        self.btn_clear.pack(side="right", padx=6, pady=10)

        # --- Data Table Frame ---
        table_card = ctk.CTkFrame(self, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        table_card.grid(row=2, column=0, padx=20, pady=(8, 16), sticky="nsew")

        # Table Column Headers
        header_row = ctk.CTkFrame(table_card, fg_color=COLORS["bg_header"], height=32)
        header_row.pack(fill="x", padx=2, pady=(2, 0))

        headers = [("ID", 50), ("User Name", 140), ("Date", 90), ("Time", 90), ("Status", 140), ("Confidence", 90), ("Notes", 140)]
        for text, width in headers:
            lbl = ctk.CTkLabel(header_row, text=text, font=FONTS["body_bold"], text_color=COLORS["text_primary"], width=width, anchor="w")
            lbl.pack(side="left", padx=6)

        # Scrollable Data Rows Frame
        self.table_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=2, pady=2)

        self.load_logs()

    def load_logs(self):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        search = self.search_entry.get().strip()
        status = self.status_filter.get()
        date_str = self.date_entry.get().strip()

        logs = self.app.db.get_filtered_logs(search_query=search, status_filter=status, date_filter=date_str)

        if not logs:
            empty = ctk.CTkLabel(self.table_scroll, text="No logs matching criteria.", font=FONTS["body"], text_color=COLORS["text_secondary"])
            empty.pack(pady=30)
            return

        for idx, log in enumerate(logs):
            bg = COLORS["bg_card"] if idx % 2 == 0 else COLORS["bg_card_alt"]
            row = ctk.CTkFrame(self.table_scroll, fg_color=bg, corner_radius=4)
            row.pack(fill="x", pady=1, padx=2)

            status_color = COLORS["status_success"] if "GRANTED" in log["status"].upper() else COLORS["status_danger"]

            ctk.CTkLabel(row, text=str(log["id"]), font=FONTS["small"], text_color=COLORS["text_secondary"], width=50, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=log["user_name"], font=FONTS["body_bold"], text_color=COLORS["text_primary"], width=140, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=log["date"], font=FONTS["small"], text_color=COLORS["text_secondary"], width=90, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=log["time"], font=FONTS["small"], text_color=COLORS["text_secondary"], width=90, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=log["status"], font=FONTS["badge"], text_color=status_color, width=140, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=f"{log['confidence']}%", font=FONTS["small"], text_color=COLORS["text_primary"], width=90, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=log["notes"], font=FONTS["small"], text_color=COLORS["text_secondary"], width=140, anchor="w").pack(side="left", padx=6)

    def export_csv(self):
        logs = self.app.db.get_filtered_logs()
        if not logs:
            self.app.status_bar.set_status("No access logs available to export.", is_error=True)
            return

        default_name = f"facesecure_access_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=default_name
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "User Name", "Date", "Time", "Status", "Confidence (%)", "Notes"])
                for log in logs:
                    writer.writerow([log["id"], log["user_name"], log["date"], log["time"], log["status"], log["confidence"], log["notes"]])

            self.app.status_bar.set_status(f"Access logs successfully exported to: {file_path}", is_success=True)
        except Exception as e:
            self.app.status_bar.set_status(f"Failed to export CSV: {e}", is_error=True)

    def clear_all_logs(self):
        success = self.app.db.delete_logs()
        if success:
            self.load_logs()
            self.app.status_bar.set_status("All access logs cleared from database.", is_success=True)
            self.app.refresh_all_pages()
        else:
            self.app.status_bar.set_status("Failed to clear logs.", is_error=True)
