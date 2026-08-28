"""
FaceSecure - Face Registration Page
Allows enrolling new users by capturing multiple facial frames, saving encodings, and managing existing users.
"""

import os
import shutil
import cv2
import customtkinter as ctk
from PIL import Image
from styles import COLORS, FONTS, RADIUS


class RegistrationPage(ctk.CTkFrame):
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
        self.is_capturing = False
        self.captured_samples = []
        self._build_page()

    def _build_page(self):
        self.grid_columnconfigure(0, weight=1) # Left Registration Form
        self.grid_columnconfigure(1, weight=1) # Right Registered Users List
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL: Face Capture & Enrollment Form ---
        form_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        form_frame.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")

        title_lbl = ctk.CTkLabel(form_frame, text="👤 Register New Face", font=FONTS["title_medium"], text_color=COLORS["text_primary"])
        title_lbl.pack(anchor="w", padx=16, pady=(16, 10))

        # Person Name Input
        name_lbl = ctk.CTkLabel(form_frame, text="Person Full Name:", font=FONTS["small"], text_color=COLORS["text_secondary"])
        name_lbl.pack(anchor="w", padx=16, pady=(4, 2))

        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. Pravin Kumar", height=38, font=FONTS["body"])
        self.name_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Camera Viewport for Enrollment
        self.video_box = ctk.CTkFrame(form_frame, fg_color=COLORS["bg_status"], height=220, corner_radius=RADIUS["input"])
        self.video_box.pack(fill="x", padx=16, pady=6)
        self.video_box.pack_propagate(False)

        self.video_label = ctk.CTkLabel(self.video_box, text="Click 'Start Capture Camera' to begin", font=FONTS["body"], text_color=COLORS["text_secondary"])
        self.video_label.pack(expand=True)

        # Progress Bar for 5 samples
        self.progress_lbl = ctk.CTkLabel(form_frame, text="Enrollment Progress: 0 / 5 samples captured", font=FONTS["small"], text_color=COLORS["text_secondary"])
        self.progress_lbl.pack(anchor="w", padx=16, pady=(8, 2))

        self.progress_bar = ctk.CTkProgressBar(form_frame, height=10, progress_color=COLORS["primary"])
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 12))

        # Action Buttons Row
        btn_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        self.btn_cam = ctk.CTkButton(btn_box, text="📷 Start Camera", font=FONTS["action_button"], width=130, command=self.toggle_capture_cam)
        self.btn_cam.pack(side="left", padx=(0, 6))

        self.btn_snap = ctk.CTkButton(btn_box, text="📸 Capture Sample", font=FONTS["action_button"], width=130, fg_color=COLORS["secondary"], command=self.capture_sample)
        self.btn_snap.pack(side="left", padx=6)

        self.btn_save = ctk.CTkButton(btn_box, text="💾 Save User", font=FONTS["action_button"], fg_color=COLORS["status_success"], hover_color="#05B386", command=self.save_user_enrollment)
        self.btn_save.pack(side="right")

        # --- RIGHT PANEL: Registered Users List ---
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=COLORS["border"])
        list_frame.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")

        list_title = ctk.CTkLabel(list_frame, text="👥 Registered Users Directory", font=FONTS["title_medium"], text_color=COLORS["text_primary"])
        list_title.pack(anchor="w", padx=16, pady=(16, 10))

        self.users_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.users_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.refresh_users_list()

    def toggle_capture_cam(self):
        if self.is_capturing:
            self.stop_cam()
        else:
            self.start_cam()

    def start_cam(self):
        cam_idx = self.app.config.get("camera_index", 0)
        self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(cam_idx)

        if not self.cap.isOpened():
            self.app.status_bar.set_status("Registration camera failed to open.", is_error=True)
            return

        self.is_capturing = True
        self.btn_cam.configure(text="⏹️ Stop Camera", fg_color=COLORS["status_danger"])
        self._update_cam_feed()

    def stop_cam(self):
        self.is_capturing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_cam.configure(text="📷 Start Camera", fg_color=COLORS["primary"])
        self.video_label.configure(image="", text="Camera Offline")

    def _update_cam_feed(self):
        if not self.is_capturing or not self.cap:
            return

        ret, frame = self.cap.read()
        if ret and frame is not None:
            frame = cv2.flip(frame, 1)
            faces = self.app.face_engine.detect_faces(frame)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 180, 216), 2)
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(320, 200))
            self.video_label.configure(image=ctk_img, text="")
            self.current_frame = frame

        if self.is_capturing:
            self.after(33, self._update_cam_feed)

    def capture_sample(self):
        if not self.is_capturing or not hasattr(self, "current_frame") or self.current_frame is None:
            self.app.status_bar.set_status("Please start camera before capturing samples.", is_error=True)
            return

        faces = self.app.face_engine.detect_faces(self.current_frame)
        if not faces:
            self.app.status_bar.set_status("No face detected in current frame! Please position face clearly.", is_error=True)
            return

        if len(self.captured_samples) >= 5:
            self.app.status_bar.set_status("Maximum 5 face samples captured. Ready to save!", is_success=True)
            return

        self.captured_samples.append(self.current_frame.copy())
        count = len(self.captured_samples)
        self.progress_bar.set(count / 5.0)
        self.progress_lbl.configure(text=f"Enrollment Progress: {count} / 5 samples captured")
        self.app.status_bar.set_status(f"Captured face sample {count}/5", is_success=True)

    def save_user_enrollment(self):
        name = self.name_entry.get().strip()
        if not name:
            self.app.status_bar.set_status("Please enter a valid person name.", is_error=True)
            return

        if not self.captured_samples:
            self.app.status_bar.set_status("Please capture at least 1 face sample before saving.", is_error=True)
            return

        # Check duplicate user
        existing = self.app.db.get_user_by_name(name)
        if existing:
            self.app.status_bar.set_status(f"User '{name}' already exists! Prevented duplicate registration.", is_error=True)
            return

        user_id = self.app.db.add_user(name)
        if not user_id:
            self.app.status_bar.set_status("Failed to create user record.", is_error=True)
            return

        # Create user face image folder data/faces/PersonName/
        user_dir = os.path.join("data", "faces", name)
        os.makedirs(user_dir, exist_ok=True)

        encodings_count = 0
        for idx, sample_frame in enumerate(self.captured_samples, start=1):
            img_path = os.path.join(user_dir, f"face_{idx}.jpg")
            cv2.imwrite(img_path, sample_frame)

            # Generate encoding
            encoding = self.app.face_engine.generate_encoding(sample_frame)
            if encoding is not None:
                self.app.db.add_face_encoding(user_id, encoding, img_path)
                encodings_count += 1

        self.stop_cam()
        self.name_entry.delete(0, "end")
        self.captured_samples.clear()
        self.progress_bar.set(0.0)
        self.progress_lbl.configure(text="Enrollment Progress: 0 / 5 samples captured")

        self.app.status_bar.set_status(f"Successfully registered '{name}' with {encodings_count} face encodings!", is_success=True)
        self.refresh_users_list()
        self.app.refresh_all_pages()

    def refresh_users_list(self):
        for w in self.users_scroll.winfo_children():
            w.destroy()

        users = self.app.db.get_all_users()
        if not users:
            empty = ctk.CTkLabel(self.users_scroll, text="No registered users found.", font=FONTS["body"], text_color=COLORS["text_secondary"])
            empty.pack(pady=20)
            return

        for u in users:
            row = ctk.CTkFrame(self.users_scroll, fg_color=COLORS["bg_card"], corner_radius=RADIUS["input"])
            row.pack(fill="x", pady=4, padx=4)

            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", padx=10, pady=8)

            lbl_name = ctk.CTkLabel(info_box, text=f"👤 {u['name']}", font=FONTS["body_bold"], text_color=COLORS["text_primary"], anchor="w")
            lbl_name.pack(anchor="w")

            lbl_meta = ctk.CTkLabel(info_box, text=f"Samples: {u['photo_count']} encodings", font=FONTS["small"], text_color=COLORS["text_secondary"], anchor="w")
            lbl_meta.pack(anchor="w")

            btn_del = ctk.CTkButton(
                row,
                text="🗑️ Delete",
                font=FONTS["small"],
                width=75,
                height=28,
                fg_color=COLORS["status_danger"],
                command=lambda uid=u['id'], uname=u['name']: self.delete_user_record(uid, uname)
            )
            btn_del.pack(side="right", padx=10, pady=8)

    def delete_user_record(self, user_id: int, name: str):
        success = self.app.db.delete_user(user_id)
        if success:
            user_dir = os.path.join("data", "faces", name)
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir, ignore_errors=True)
            self.app.status_bar.set_status(f"Deleted user '{name}'", is_success=True)
            self.refresh_users_list()
            self.app.refresh_all_pages()
        else:
            self.app.status_bar.set_status(f"Failed to delete user ID {user_id}", is_error=True)
