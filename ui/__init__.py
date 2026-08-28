"""
FaceSecure UI Package
Exposes all page views and components for the application.
"""

from ui.header import HeaderFrame
from ui.sidebar import SidebarFrame
from ui.status_bar import StatusBarFrame
from ui.dashboard_page import DashboardPage
from ui.camera_page import CameraPage
from ui.registration_page import RegistrationPage
from ui.recognition_page import RecognitionPage
from ui.logs_page import LogsPage
from ui.settings_page import SettingsPage
from ui.about_page import AboutPage

__all__ = [
    "HeaderFrame",
    "SidebarFrame",
    "StatusBarFrame",
    "DashboardPage",
    "CameraPage",
    "RegistrationPage",
    "RecognitionPage",
    "LogsPage",
    "SettingsPage",
    "AboutPage",
]
