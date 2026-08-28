"""
FaceSecure - Styling & Design System (Light Theme)
Defines the clean, professional light mode palette, typography, and widget styling rules.
"""

import customtkinter as ctk

# Color Palette - Professional Light Theme
COLORS = {
    "bg_dark": "#F8FAFC",        # Crisp light slate background
    "bg_card": "#FFFFFF",        # Pure white card background
    "bg_card_alt": "#F1F5F9",    # Secondary light container
    "bg_header": "#FFFFFF",      # Header bar white background
    "bg_status": "#E2E8F0",      # Video / canvas background
    
    # Primary & Accent Colors
    "primary": "#2563EB",        # Royal sapphire blue
    "primary_hover": "#1D4ED8",  # Darker sapphire blue hover
    "primary_active": "#1E40AF", # Active state
    
    "secondary": "#0284C7",      # Sky cyan secondary
    "secondary_hover": "#0369A1",
    
    "accent_glow": "#2563EB",    # Primary highlight
    
    # Text Colors
    "text_primary": "#0F172A",   # Deep charcoal slate text
    "text_secondary": "#64748B", # Muted cool grey text
    "text_dark": "#FFFFFF",      # Light text inside dark primary buttons
    
    # Border & Divider Colors
    "border": "#CBD5E1",         # Clean light border
    "border_light": "#E2E8F0",   # Soft card border
    
    # Status Indicator Colors
    "status_success": "#059669", # Emerald green (Door Opened / Active)
    "status_danger": "#DC2626",  # Crimson red (Offline / Alarm)
    "status_warning": "#D97706", # Amber (Door Closed / Locked)
    "status_info": "#2563EB",    # Royal blue
}

# Typography Configurations
FONTS = {
    "title_large": ("Segoe UI", 22, "bold"),
    "title_medium": ("Segoe UI", 16, "bold"),
    "header_sub": ("Segoe UI", 11, "normal"),
    "menu_button": ("Segoe UI", 13, "bold"),
    "action_button": ("Segoe UI", 12, "bold"),
    "body_bold": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 11, "normal"),
    "small": ("Segoe UI", 10, "normal"),
    "badge": ("Segoe UI", 10, "bold"),
}

# Radii and Spacing Constants
RADIUS = {
    "card": 12,
    "button": 10,
    "pill": 16,
    "input": 8,
}

def apply_global_theme(mode: str = "Light"):
    """Configures CustomTkinter appearance mode and theme."""
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")
