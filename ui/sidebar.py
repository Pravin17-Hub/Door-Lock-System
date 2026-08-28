"""
FaceSecure - Sidebar Component
Left vertical navigation menu supporting all 7 application pages.
"""

import customtkinter as ctk
from styles import COLORS, FONTS, RADIUS


class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, on_menu_select=None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"],
            width=200,
            **kwargs
        )
        
        self.on_menu_select = on_menu_select
        self.active_page = "Dashboard"
        self.buttons = {}
        
        self._build_sidebar()

    def _build_sidebar(self):
        # Menu Header Label
        self.menu_label = ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.menu_label.pack(fill="x", padx=16, pady=(16, 10))

        # 7 Pages as specified in requirements
        menu_items = [
            ("Dashboard", "📊"),
            ("Camera", "🎥"),
            ("Face Registration", "👤"),
            ("Face Recognition", "🔍"),
            ("Access Logs", "📋"),
            ("Settings", "⚙️"),
            ("About", "ℹ️")
        ]

        for item_name, icon in menu_items:
            btn = ctk.CTkButton(
                self,
                text=f"{icon}  {item_name}",
                font=FONTS["menu_button"],
                anchor="w",
                height=40,
                corner_radius=RADIUS["button"],
                fg_color="transparent" if item_name != self.active_page else COLORS["primary"],
                text_color=COLORS["text_primary"],
                hover_color=COLORS["primary_hover"],
                command=lambda name=item_name: self._handle_click(name)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.buttons[item_name] = btn

    def _handle_click(self, item_name):
        self.active_page = item_name
        self.update_active_button(item_name)
        if self.on_menu_select:
            self.on_menu_select(item_name)

    def update_active_button(self, active_name):
        for name, btn in self.buttons.items():
            if name == active_name:
                btn.configure(fg_color=COLORS["primary"])
            else:
                btn.configure(fg_color="transparent")
