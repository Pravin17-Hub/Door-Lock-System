"""
FaceSecure - Face Recognition Page (Light Theme)
Real-time webcam recognition engine. Matches detected faces against SQLite encodings,
actuates Arduino serial UNLOCK/LOCK/ALARM signals, holds detected user details on screen,
and pauses new face scanning for 5 seconds while the door is open.
"""

import time
import cv2
import customtkinter as ctk
from PIL import Image
from styles import COLORS, FONTS, RADIUS


class RecognitionPage(ctk.CTkFrame):
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
        self.is_running = False
        
        # Door Open State, Scanning Pause, & Countdown Tracker
        self.door_is_open = False
        self.scan_paused = False # True during the 5-second door open period
        self.door_seconds_remaining = 0
        self.auto_lock_after_id = None
        
        self.known_encodings = []
        self._build_page()

    def _build_page(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Title & Controls Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        title_lbl = ctk.CTkLabel(top_bar, text="🔍 Live Face Recognition Access Control", font=FONTS["title_large"], text_color=COLORS["text_primary"])
        title_lbl.pack(side="left")

        self.btn_toggle = ctk.CTkButton(
            top_bar,
            text="🔍 Start Recognition Engine",
            font=FONTS["action_button"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_dark"],
            command=self.toggle_recognition
        )
        self.btn_toggle.pack(side="right")

        # Main Layout Container
        content_box = ctk.CTkFrame(self, fg_color="transparent")
        content_box.grid(row=1, column=0, padx=20, pady=(4, 16), sticky="nsew")

        content_box.grid_columnconfigure(0, weight=3) # Video Feed
        content_box.grid_columnconfigure(1, weight=2) # Right Status Panel
        content_box.grid_rowconfigure(0, weight=1)

        # Video Viewport
        self.video_box = ctk.CTkFrame(content_box, fg_color=COLORS["bg_status"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        self.video_box.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.video_box.grid_rowconfigure(0, weight=1)
        self.video_box.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.video_box, text="Recognition Engine Standby\nClick 'Start Recognition Engine' to activate", font=FONTS["title_medium"], text_color=COLORS["text_secondary"])
        self.video_label.grid(row=0, column=0, sticky="nsew")

        # Right Panel: Verification Banner & Live Door Status
        self.status_box = ctk.CTkFrame(content_box, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        self.status_box.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        lbl_hdr = ctk.CTkLabel(self.status_box, text="VERIFICATION BANNER", font=FONTS["small"], text_color=COLORS["text_secondary"])
        lbl_hdr.pack(anchor="w", padx=16, pady=(16, 6))

        # Access Banner Card
        self.banner_card = ctk.CTkFrame(self.status_box, fg_color=COLORS["bg_card"], corner_radius=RADIUS["card"], border_width=2, border_color=COLORS["border"])
        self.banner_card.pack(fill="x", padx=16, pady=6)

        self.banner_status_lbl = ctk.CTkLabel(self.banner_card, text="SCANNING...", font=FONTS["title_large"], text_color=COLORS["text_secondary"])
        self.banner_status_lbl.pack(pady=(16, 4))

        self.banner_name_lbl = ctk.CTkLabel(self.banner_card, text="No Face Detected", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        self.banner_name_lbl.pack(pady=(0, 4))

        self.banner_conf_lbl = ctk.CTkLabel(self.banner_card, text="Confidence: --", font=FONTS["small"], text_color=COLORS["text_secondary"])
        self.banner_conf_lbl.pack(pady=(0, 16))

        # Door Lock Real-time State Card
        door_card = ctk.CTkFrame(self.status_box, fg_color=COLORS["bg_card"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        door_card.pack(fill="x", padx=16, pady=10)

        lbl_door_hdr = ctk.CTkLabel(door_card, text="🚪 Door Mechanism Status:", font=FONTS["small"], text_color=COLORS["text_secondary"])
        lbl_door_hdr.pack(anchor="w", padx=12, pady=(10, 2))

        self.lbl_door_state = ctk.CTkLabel(door_card, text="Door Closed 🔒", font=FONTS["title_medium"], text_color=COLORS["status_warning"])
        self.lbl_door_state.pack(anchor="w", padx=12, pady=(0, 10))

        # Arduino Serial Command Card
        serial_card = ctk.CTkFrame(self.status_box, fg_color=COLORS["bg_card"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        serial_card.pack(fill="x", padx=16, pady=10)

        lbl_cmd_title = ctk.CTkLabel(serial_card, text="🔌 Arduino Serial Activity:", font=FONTS["small"], text_color=COLORS["text_secondary"])
        lbl_cmd_title.pack(anchor="w", padx=12, pady=(10, 2))

        self.lbl_cmd_log = ctk.CTkLabel(serial_card, text="Ready (Door Locked)", font=FONTS["body_bold"], text_color=COLORS["text_primary"])
        self.lbl_cmd_log.pack(anchor="w", padx=12, pady=(0, 10))

    def reload_encodings(self):
        """Loads stored face encodings from SQLite database."""
        self.known_encodings = self.app.db.get_all_encodings()

    def toggle_recognition(self):
        if self.is_running:
            self.stop_recognition()
        else:
            self.start_recognition()

    def start_recognition(self):
        self.reload_encodings()
        if not self.known_encodings:
            self.app.status_bar.set_status("No registered face encodings found in database! Please register a face first.", is_error=True)

        cam_idx = self.app.config.get("camera_index", 0)
        self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(cam_idx)

        if not self.cap.isOpened():
            self.app.status_bar.set_status("Recognition camera capture failed to start.", is_error=True)
            return

        self.is_running = True
        self.app.camera_running = True
        self.btn_toggle.configure(text="⏹️ Stop Recognition", fg_color=COLORS["status_danger"])
        self.app.status_bar.set_status("Face Recognition Engine ACTIVE", is_success=True)
        self._update_loop()

    def stop_recognition(self):
        self.is_running = False
        self.app.camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_toggle.configure(text="🔍 Start Recognition Engine", fg_color=COLORS["primary"])
        self.video_label.configure(image="", text="Recognition Engine Standby\nClick 'Start Recognition Engine' to activate")
        self._set_door_closed_state()
        self.app.status_bar.set_status("Face Recognition Engine stopped.")

    def _reset_banner_standby(self):
        """Resets verification banner when scanning is active and no face is present."""
        if not self.door_is_open and not self.scan_paused:
            self.banner_card.configure(border_color=COLORS["border"])
            self.banner_status_lbl.configure(text="SCANNING...", text_color=COLORS["text_secondary"])
            self.banner_name_lbl.configure(text="No Face Detected")
            self.banner_conf_lbl.configure(text="Confidence: --")

    def _open_door_and_freeze(self, name: str, confidence: float, duration: int = 5):
        """Opens door, holds detected user's details on screen, and pauses new scanning for 5 seconds."""
        self.door_is_open = True
        self.scan_paused = True # PAUSE NEW SCANNING FOR 5 SECONDS!
        self.door_seconds_remaining = duration

        # Freeze Access Granted Banner on screen with user details
        self.banner_card.configure(border_color=COLORS["status_success"])
        self.banner_status_lbl.configure(text="ACCESS GRANTED 🔓", text_color=COLORS["status_success"])
        self.banner_name_lbl.configure(text=f"Welcome, {name}!")
        self.banner_conf_lbl.configure(text=f"Match Confidence: {confidence}%")

        # Send UNLOCK serial command to Arduino
        self.app.arduino.send_command("UNLOCK")

        if self.auto_lock_after_id:
            self.after_cancel(self.auto_lock_after_id)
            self.auto_lock_after_id = None

        # Start 5-second countdown ticker
        self._tick_door_countdown()

    def _tick_door_countdown(self):
        """1-second interval countdown ticker."""
        if not self.is_running and not self.door_is_open:
            return

        if self.door_seconds_remaining > 0:
            msg = f"Door Opened 🔓 (Closing in {self.door_seconds_remaining}s)"
            self.lbl_door_state.configure(text=msg, text_color=COLORS["status_success"])
            self.lbl_cmd_log.configure(
                text=f"SENT 'UNLOCK' -> Scanning Paused ({self.door_seconds_remaining}s left)",
                text_color=COLORS["status_success"]
            )

            self.app.header.update_header_statuses(self.is_running, self.app.arduino.is_connected, door_unlocked=True)
            if hasattr(self.app, "status_panel"):
                self.app.status_panel.set_door_status(opened=True)

            self.door_seconds_remaining -= 1
            self.auto_lock_after_id = self.after(1000, self._tick_door_countdown)
        else:
            self._set_door_closed_state()

    def _set_door_closed_state(self):
        """Locks the door, transmits LOCK to Arduino, and RESUMES NEW SCANNING."""
        self.door_is_open = False
        self.scan_paused = False # RESUME NEW SCANNING!
        self.door_seconds_remaining = 0

        # Send LOCK serial command to Arduino
        self.app.arduino.send_command("LOCK")

        self.lbl_door_state.configure(text="Door Closed 🔒", text_color=COLORS["status_warning"])
        self.lbl_cmd_log.configure(text="SENT 'LOCK' -> Resuming Face Scanning...", text_color=COLORS["text_secondary"])

        self._reset_banner_standby()

        self.app.header.update_header_statuses(self.is_running, self.app.arduino.is_connected, door_unlocked=False)
        if hasattr(self.app, "status_panel"):
            self.app.status_panel.set_door_status(opened=False)

        if self.auto_lock_after_id:
            self.after_cancel(self.auto_lock_after_id)
            self.auto_lock_after_id = None

    def _update_loop(self):
        if not self.is_running or not self.cap:
            return

        ret, frame = self.cap.read()
        if ret and frame is not None:
            frame = cv2.flip(frame, 1)

            # IF SCANNING IS PAUSED (during the 5 seconds door is open), skip new face scanning!
            if self.scan_paused:
                # Video feed keeps streaming smoothly, but new scanning is paused and user details remain frozen on screen!
                pass
            else:
                # Perform active face detection & recognition matching
                faces = self.app.face_engine.detect_faces(frame)

                if not faces:
                    self._reset_banner_standby()
                else:
                    for (x, y, w, h) in faces:
                        candidate_enc = self.app.face_engine.generate_encoding(frame, (x, y, w, h))
                        name, confidence = self.app.face_engine.compare_encodings(
                            candidate_enc,
                            self.known_encodings,
                            threshold=self.app.config.get("confidence_threshold", 0.65)
                        )

                        is_authorized = (name != "Unknown")

                        # Draw bounding box
                        frame = self.app.face_engine.annotate_frame(frame, (x, y, w, h), name, confidence, is_authorized)

                        if is_authorized:
                            # Access Granted -> Open door, freeze user details on screen, & pause scanning for 5s!
                            duration = self.app.config.get("door_unlock_duration", 5)
                            self._open_door_and_freeze(name, confidence, duration=duration)

                            # Log access attempt
                            self.app.db.log_access(name, "ACCESS GRANTED", confidence, f"Door Opened for {duration}s")
                            self.app.status_bar.set_status(f"ACCESS GRANTED for {name} ({confidence}%) - Scanning Paused 5s", is_success=True)
                            break
                        else:
                            # Access Denied -> Show warning & keep door locked
                            self.banner_card.configure(border_color=COLORS["status_danger"])
                            self.banner_status_lbl.configure(text="ACCESS DENIED 🔒", text_color=COLORS["status_danger"])
                            self.banner_name_lbl.configure(text="Unknown / Unauthorized Face")
                            self.banner_conf_lbl.configure(text=f"Match Confidence: {confidence}%")

                            # Send serial ALARM
                            self.app.arduino.send_command("ALARM")
                            self.lbl_cmd_log.configure(text="SENT 'ALARM' -> Door Kept Closed", text_color=COLORS["status_danger"])

                            # Log access attempt
                            self.app.db.log_access("Unknown", "ACCESS DENIED", confidence, "Unauthorized face attempt")
                            self.app.status_bar.set_status("SECURITY ALERT: Unknown Person Detected!", is_error=True)

            # Render live camera frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(480, 360))
            self.video_label.configure(image=ctk_img, text="")

        if self.is_running:
            self.after(33, self._update_loop)
