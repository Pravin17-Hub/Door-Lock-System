"""
FaceSecure - Camera Page
Dedicated OpenCV camera feed display with resolution controls, camera index selection, and start/stop controls.
"""

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from styles import COLORS, FONTS, RADIUS


class CameraPage(ctk.CTkFrame):
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
        self.cap = None
        self.is_streaming = False
        self._build_page()

    def _build_page(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Control Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        title_lbl = ctk.CTkLabel(top_bar, text="🎥 Live Camera Stream", font=FONTS["title_large"], text_color=COLORS["text_primary"])
        title_lbl.pack(side="left")

        # Camera selection dropdown
        self.cam_select = ctk.CTkOptionMenu(
            top_bar,
            values=["Camera 0 (Default)", "Camera 1 (Secondary)", "Camera 2"],
            width=160,
            command=self._on_cam_selected
        )
        self.cam_select.pack(side="right", padx=(10, 0))

        # Start / Stop Button
        self.btn_toggle = ctk.CTkButton(
            top_bar,
            text="🎥 Start Camera",
            font=FONTS["action_button"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.toggle_camera
        )
        self.btn_toggle.pack(side="right", padx=10)

        # Video Display Canvas / Label Box
        self.video_box = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_status"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=COLORS["border"]
        )
        self.video_box.grid(row=1, column=0, padx=20, pady=(4, 16), sticky="nsew")
        self.video_box.grid_rowconfigure(0, weight=1)
        self.video_box.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.video_box, text="Camera Offline\nClick 'Start Camera' to initiate stream", font=FONTS["title_medium"], text_color=COLORS["text_secondary"])
        self.video_label.grid(row=0, column=0, sticky="nsew")

    def _on_cam_selected(self, choice):
        idx = int(choice.split()[1])
        self.app.config.set("camera_index", idx)
        if self.is_streaming:
            self.stop_camera()
            self.start_camera()

    def toggle_camera(self):
        if self.is_streaming:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        cam_idx = self.app.config.get("camera_index", 0)
        try:
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(cam_idx) # Fallback without DSHOW

            if not self.cap.isOpened():
                self.video_label.configure(
                    text="❌ Selected Camera Unavailable\nPlease verify camera connection or select a different device index.",
                    text_color=COLORS["status_danger"]
                )
                self.app.status_bar.set_status("Camera capture device failed to open", is_error=True)
                return

            self.is_streaming = True
            self.app.camera_running = True
            self.btn_toggle.configure(text="⏹️ Stop Camera", fg_color=COLORS["status_danger"])
            self.app.status_bar.set_status(f"Camera stream active (Index: {cam_idx})", is_success=True)
            self._update_stream()
        except Exception as e:
            self.video_label.configure(text=f"Camera Error: {e}", text_color=COLORS["status_danger"])
            self.app.status_bar.set_status(f"Camera Error: {e}", is_error=True)

    def stop_camera(self):
        self.is_streaming = False
        self.app.camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_toggle.configure(text="🎥 Start Camera", fg_color=COLORS["primary"])
        self.video_label.configure(image="", text="Camera Offline\nClick 'Start Camera' to initiate stream", text_color=COLORS["text_secondary"])
        self.app.status_bar.set_status("Camera stream stopped.")

    def _update_stream(self):
        if not self.is_streaming or not self.cap:
            return

        ret, frame = self.cap.read()
        if ret and frame is not None:
            # Flip horizontally for natural mirror preview
            frame = cv2.flip(frame, 1)
            
            # Detect faces for preview overlay
            faces = self.app.face_engine.detect_faces(frame)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 180, 216), 2)
                cv2.putText(frame, "DETECTED FACE", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 180, 216), 2)

            # Resize frame to fit canvas box
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(640, 420))
            
            self.video_label.configure(image=ctk_img, text="")

        # Loop at ~30 FPS (33 ms)
        if self.is_streaming:
            self.after(33, self._update_stream)
