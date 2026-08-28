"""
FaceSecure - Full-Stack Web Application Server
Powered by Flask, OpenCV LBPH High-Accuracy AI Engine, SQLite Auth with WAL mode, & ESP32 Motor Controller

Features:
- High-Accuracy LBPH (Local Binary Patterns Histograms) & HOG Texture AI Engine
- Automated AI Model Training on 20 face samples per registered person
- Reset camera status on /camera page view to prevent retained test states
- Test Motor Rotation API (/api/test_unlock) for instant servo motor debugging
- Clean ASCII Console Logging (Fixes Windows CP1252 UnicodeEncodeError)
- Direct Physical Webcam Engine (Index 1 CAP_ANY)
- Client Heartbeat Camera Watchdog (/api/camera_heartbeat)
- 10-Second Camera Enrollment (Saves 20 valid face images into face_data/<Name>/)
- Real-time Video Stream Generator with Bounding Box Annotations
- USB Serial ESP32 Hardware Integration with Manual COM Port Overrides
"""

import os
import time
import shutil
import csv
import io
import threading
import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, Response, jsonify, send_file
)
from werkzeug.utils import secure_filename

from config import Config
from database_manager.web_db import WebDatabaseManager
from recognition.web_face_engine import WebFaceEngine
from hardware.esp32_manager import ESP32Manager

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload & face_data directories exist
FACE_DATA_ROOT = os.path.abspath("face_data")
os.makedirs(FACE_DATA_ROOT, exist_ok=True)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize Core Services
db = WebDatabaseManager(app.config["DATABASE_PATH"])
face_engine = WebFaceEngine(confidence_threshold=55.0) # High-accuracy LBPH threshold
esp32 = ESP32Manager(port=app.config["COM_PORT"], baud_rate=app.config["BAUD_RATE"])

# Auto-train LBPH AI model on startup if face_data exists
threading.Thread(target=lambda: face_engine.train_model_from_face_data(), daemon=True).start()

# Global App State Tracking
app_state = {
    "camera_active": False,
    "door_is_open": False,
    "scan_paused": False,
    "seconds_remaining": 0,
    "status_type": "SCANNING", # "GRANTED", "DENIED", "SCANNING"
    "person_name": "",
    "confidence": 0.0,
    "last_trigger_time": 0.0,
    
    # Enrollment State
    "is_enrolling": False,
    "enroll_name": "",
    "enroll_captured": 0,
    "enroll_total": 20,
    "enroll_time_left": 10,
    "enroll_status": "Idle"
}


class DemandCameraManager:
    """Manages OpenCV VideoCapture on demand using direct Physical Webcam Index 1 and 2.5s Client Heartbeat Watchdog."""
    def __init__(self):
        self.cap = None
        self.active_index = -1
        self.lock = threading.Lock()
        self.last_heartbeat = 0.0
        self.watchdog_running = False

    def receive_heartbeat(self):
        """Called whenever active browser tab sends heartbeat ping."""
        self.last_heartbeat = time.time()

    def start_camera(self) -> bool:
        """Opens physical webcam device (Index 1) directly without probing index 0."""
        with self.lock:
            self.last_heartbeat = time.time()
            if self.cap is not None and self.cap.isOpened():
                return True

            for idx in [1, 0]:
                for backend in [cv2.CAP_ANY, cv2.CAP_DSHOW]:
                    c = cv2.VideoCapture(idx, backend)
                    if c.isOpened():
                        ret, frame = c.read()
                        if ret and frame is not None and np.mean(frame) > 1.0:
                            c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            self.cap = c
                            self.active_index = idx
                            app_state["camera_active"] = True
                            print(f"[DemandCameraManager] Physical Webcam Index {idx} OPENED [OK] (mean intensity={np.mean(frame):.1f})")
                            self._start_watchdog_if_needed()
                            return True
                        c.release()

            self.cap = None
            app_state["camera_active"] = False
            print("[DemandCameraManager] Could not open active webcam.")
            return False

    def _start_watchdog_if_needed(self):
        if not self.watchdog_running:
            self.watchdog_running = True
            threading.Thread(target=self._watchdog_loop, daemon=True).start()

    def _watchdog_loop(self):
        while self.watchdog_running:
            time.sleep(1.0)
            with self.lock:
                if self.cap is None:
                    self.watchdog_running = False
                    break

                # If no browser heartbeat ping received for > 2.5 seconds -> Auto release camera hardware & turn off LED!
                if not app_state["is_enrolling"] and (time.time() - self.last_heartbeat > 2.5):
                    print("[DemandCameraManager] Client heartbeat stopped! Auto-releasing camera LED [CLOSED]")
                    self._stop_internal()
                    self.watchdog_running = False
                    break

    def read_frame(self) -> Optional[np.ndarray]:
        """Reads frame from active webcam."""
        with self.lock:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None and np.mean(frame) > 1.0:
                    return cv2.flip(frame, 1)
        return None

    def stop_camera(self):
        """Releases webcam hardware completely and turns off webcam LED light."""
        with self.lock:
            self._stop_internal()

    def _stop_internal(self):
        if self.cap is not None:
            try:
                if self.cap.isOpened():
                    self.cap.release()
            except Exception:
                pass
            self.cap = None
            self.active_index = -1
            app_state["camera_active"] = False
            print("[DemandCameraManager] Webcam Hardware RELEASED & CLOSED [OFF]")


camera_mgr = DemandCameraManager()


def login_required(f):
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in with your email and password to access the system.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# --- AUTHENTICATION ROUTES ---

@app.route("/")
def index():
    if "admin_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not email or not password:
            flash("Please provide a valid email and password.", "danger")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for("register"))

        success = db.register_admin(email, password)
        if success:
            flash("Admin account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = db.authenticate_admin(email, password)
        if user:
            session["admin_id"] = user["id"]
            session["admin_email"] = user["email"]
            flash(f"Welcome back, {user['email']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please check your credentials.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# --- DASHBOARD & PERSON RECORD MANAGEMENT ---

@app.route("/dashboard")
@login_required
def dashboard():
    persons = db.get_all_persons()
    raw_ports = esp32.get_available_ports()

    return render_template(
        "dashboard.html",
        persons=persons,
        available_ports=raw_ports,
        esp32_connected=esp32.check_connection_status(),
        esp32_port=esp32.connected_port,
        esp32_error=esp32.last_error
    )


# --- CAMERA HEARTBEAT API ---

@app.route("/api/camera_heartbeat")
def api_camera_heartbeat():
    """Received every 1000ms from active camera webpage or active enrollment tab."""
    camera_mgr.receive_heartbeat()
    return jsonify({"status": "ok", "camera_active": app_state["camera_active"]})


# --- 10-SECOND LIVE CAMERA ENROLLMENT (20 VALID IMAGES SAVED IN face_data/<Name>/) ---

@app.route("/api/start_enrollment", methods=["POST"])
@login_required
def api_start_enrollment():
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "Please enter a valid person full name."}), 400

    person_id = db.get_or_create_person(name)
    if not person_id:
        return jsonify({"success": False, "error": "Database error preparing enrollment. Please try again."}), 400

    app_state["is_enrolling"] = True
    app_state["enroll_name"] = name
    app_state["enroll_captured"] = 0
    app_state["enroll_total"] = 20
    app_state["enroll_time_left"] = 10
    app_state["enroll_status"] = "Opening camera & capturing 20 face photos..."

    def _enroll_worker():
        cam_ok = camera_mgr.start_camera()
        if not cam_ok:
            app_state["enroll_status"] = "Camera Error: Could not open webcam device."
            app_state["is_enrolling"] = False
            return

        safe_folder_name = name.replace(" ", "_")
        person_dir = os.path.join(FACE_DATA_ROOT, safe_folder_name)
        
        if os.path.exists(person_dir):
            shutil.rmtree(person_dir, ignore_errors=True)
        os.makedirs(person_dir, exist_ok=True)

        samples_captured = 0
        start_time = time.time()
        duration = 10.0

        while time.time() - start_time < duration and samples_captured < 20 and app_state["is_enrolling"]:
            camera_mgr.receive_heartbeat()
            elapsed = time.time() - start_time
            app_state["enroll_time_left"] = max(0, int(duration - elapsed))

            frame = camera_mgr.read_frame()

            if frame is not None and np.mean(frame) > 1.0:
                enc = face_engine.generate_encoding(frame)
                if enc is not None:
                    samples_captured += 1
                    filename = f"img_{samples_captured}.jpg"
                    full_img_path = os.path.join(person_dir, filename)
                    cv2.imwrite(full_img_path, frame)

                    rel_path = os.path.join("face_data", safe_folder_name, filename).replace("\\", "/")
                    db.add_face_encoding(person_id, rel_path, enc)

                    app_state["enroll_captured"] = samples_captured
                    app_state["enroll_status"] = f"Captured {samples_captured}/20 photos into face_data/{safe_folder_name}/ ({app_state['enroll_time_left']}s left)..."

            time.sleep(0.4)

        app_state["is_enrolling"] = False
        app_state["enroll_time_left"] = 0

        if samples_captured >= 1:
            app_state["enroll_status"] = f"Success! Training AI model on {samples_captured} photos..."
            face_engine.train_model_from_face_data() # Auto-train LBPH model on all samples!
            app_state["enroll_status"] = f"Success! AI Model Trained & Saved for {name}."
        else:
            db.delete_person_record(person_id)
            if os.path.exists(person_dir):
                shutil.rmtree(person_dir, ignore_errors=True)
            app_state["enroll_status"] = "Enrollment Failed: No face detected in camera stream."

        camera_mgr.stop_camera()

    threading.Thread(target=_enroll_worker, daemon=True).start()
    return jsonify({"success": True, "message": "10-Second enrollment started."})


@app.route("/api/retrain_model", methods=["POST"])
@login_required
def api_retrain_model():
    """Retrains the LBPH Face Recognition AI model on all face_data directories."""
    success = face_engine.train_model_from_face_data()
    if success:
        return jsonify({"success": True, "message": "LBPH AI Face Recognition Model Retrained & Saved Successfully!"})
    else:
        return jsonify({"success": False, "message": "No face samples found in face_data/ directory."}), 400


@app.route("/api/enrollment_status")
def api_enrollment_status():
    camera_mgr.receive_heartbeat()
    return jsonify({
        "is_enrolling": app_state["is_enrolling"],
        "name": app_state["enroll_name"],
        "captured": app_state["enroll_captured"],
        "total": app_state["enroll_total"],
        "time_left": app_state["enroll_time_left"],
        "status": app_state["enroll_status"]
    })


@app.route("/delete_person/<int:person_id>", methods=["POST"])
@login_required
def delete_person(person_id):
    image_paths = db.delete_person_record(person_id)
    for p in image_paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    face_engine.train_model_from_face_data() # Retrain model after record deletion
    flash("Person record and face_data folder deleted. Access revoked.", "success")
    return redirect(url_for("dashboard"))


@app.route("/purge_persons", methods=["POST"])
@login_required
def purge_persons():
    image_paths = db.purge_all_persons()
    for p in image_paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    if os.path.exists(FACE_DATA_ROOT):
        shutil.rmtree(FACE_DATA_ROOT, ignore_errors=True)
        os.makedirs(FACE_DATA_ROOT, exist_ok=True)
    
    face_engine.is_trained = False
    flash("All registered person records and face_data images purged.", "success")
    return redirect(url_for("dashboard"))


# --- ESP32 REAL USB HARDWARE CONTROL APIs ---

@app.route("/api/refresh_ports")
@login_required
def api_refresh_ports():
    ports = esp32.get_available_ports()
    return jsonify({"ports": [{"device": dev, "label": lbl} for dev, lbl in ports]})


@app.route("/api/connect_esp32", methods=["POST"])
@login_required
def api_connect_esp32():
    data = request.json or {}
    port = data.get("com_port", "AUTO")
    success, msg = esp32.connect(port)
    if success:
        return jsonify({"success": True, "port": esp32.connected_port, "message": msg})
    else:
        return jsonify({"success": False, "message": msg}), 400


@app.route("/api/disconnect_esp32", methods=["POST"])
@login_required
def api_disconnect_esp32():
    esp32.disconnect()
    return jsonify({"success": True, "message": "ESP32 disconnected."})


@app.route("/api/test_unlock", methods=["POST"])
@login_required
def api_test_unlock():
    """Sends immediate test UNLOCK command over USB serial to rotate servo motor."""
    if not esp32.check_connection_status():
        return jsonify({"success": False, "message": "ESP32 is not connected! Select COM7 on the dashboard and click Connect ESP32 first."}), 400

    app_state["door_is_open"] = True
    app_state["seconds_remaining"] = 5
    app_state["status_type"] = "GRANTED"
    app_state["person_name"] = "Test Motor Command"
    app_state["confidence"] = 100.0

    esp32.send_unlock_auto_lock(5)
    return jsonify({"success": True, "message": f"Sent UNLOCK command to ESP32 on {esp32.connected_port}. Motor rotating for 5 seconds!"})


# --- CAMERA STREAMING & RECOGNITION LOGIC ---

@app.route("/camera")
@login_required
def camera_view():
    # Reset scanning status on page visit
    app_state["door_is_open"] = False
    app_state["scan_paused"] = False
    app_state["status_type"] = "SCANNING"
    app_state["person_name"] = ""
    app_state["confidence"] = 0.0
    return render_template("camera.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "door_is_open": app_state["door_is_open"],
        "seconds_remaining": app_state["seconds_remaining"],
        "status_type": app_state["status_type"],
        "person_name": app_state["person_name"],
        "confidence": app_state["confidence"],
        "esp32_connected": esp32.check_connection_status(),
        "esp32_port": esp32.connected_port,
        "esp32_error": esp32.last_error
    })


def gen_frames():
    """Generates HTTP MJPEG video stream with High-Accuracy LBPH Face Recognition."""
    camera_mgr.start_camera()
    door_timer_start = 0

    try:
        while app_state["camera_active"]:
            frame = camera_mgr.read_frame()

            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.rectangle(frame, (20, 20), (620, 460), (37, 99, 235), 2)
                cv2.putText(
                    frame,
                    "INITIALIZING WEBCAM STREAM...",
                    (140, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )
                time.sleep(0.05)

            now = time.time()

            if app_state["door_is_open"]:
                elapsed = int(now - door_timer_start)
                remaining = max(0, app.config["DOOR_UNLOCK_DURATION"] - elapsed)
                app_state["seconds_remaining"] = remaining

                if remaining == 0:
                    app_state["door_is_open"] = False
                    app_state["scan_paused"] = False
                    app_state["status_type"] = "SCANNING"
                    app_state["person_name"] = ""
                    app_state["confidence"] = 0.0
                    esp32.send_command("LOCK")

            if frame is not None and not app_state["scan_paused"] and not app_state["is_enrolling"]:
                faces = face_engine.detect_faces(frame)

                if not faces:
                    app_state["status_type"] = "SCANNING"
                    app_state["person_name"] = ""
                    app_state["confidence"] = 0.0
                else:
                    for (x, y, w, h) in faces:
                        # Perform High-Accuracy LBPH AI Prediction
                        name, conf = face_engine.predict_face(frame, (x, y, w, h))

                        # Fallback to vector cosine comparison if LBPH model is not trained yet
                        if name == "Unknown" and not face_engine.is_trained:
                            known_encs = db.get_all_encodings()
                            cand_enc = face_engine.generate_encoding(frame, (x, y, w, h))
                            name, conf = face_engine.compare_encodings(cand_enc, known_encs, threshold=0.60)

                        is_auth = (name != "Unknown")
                        frame = face_engine.annotate_frame(frame, (x, y, w, h), name, conf, is_auth)

                        if is_auth:
                            if not app_state["door_is_open"] and (now - app_state["last_trigger_time"] > 6.0):
                                app_state["last_trigger_time"] = now
                                app_state["door_is_open"] = True
                                app_state["scan_paused"] = True
                                app_state["status_type"] = "GRANTED"
                                app_state["person_name"] = name
                                app_state["confidence"] = conf
                                door_timer_start = now

                                esp32.send_command("UNLOCK")
                                db.log_access(name, "ACCESS GRANTED", conf, "Door Opened for 5s")
                                break
                        else:
                            app_state["status_type"] = "DENIED"
                            app_state["person_name"] = "Unknown"
                            app_state["confidence"] = conf

                            if now - app_state["last_trigger_time"] > 6.0:
                                app_state["last_trigger_time"] = now
                                esp32.send_command("ALARM")
                                db.log_access("Unknown", "ACCESS DENIED", conf, "Face Not Matched")

            if app_state["is_enrolling"]:
                cv2.rectangle(frame, (0, 0), (640, 60), (37, 99, 235), -1)
                cv2.putText(
                    frame,
                    f"ENROLLING: {app_state['enroll_name']} ({app_state['enroll_captured']}/20 photos | {app_state['enroll_time_left']}s)",
                    (15, 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2
                )

            ret_enc, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)

    finally:
        camera_mgr.stop_camera()


@app.route("/api/process_frame", methods=["POST"])
def api_process_frame():
    """Receives base64 image frame from client browser webcam, runs LBPH Face AI, and returns annotated frame & access status."""
    data = request.json or {}
    image_b64 = data.get("image", "")
    if not image_b64:
        return jsonify({"success": False, "error": "No image data received"}), 400

    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]

        image_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"success": False, "error": "Failed to decode frame"}), 400

        now = time.time()
        faces = face_engine.detect_faces(frame)

        if not faces:
            if not app_state["door_is_open"]:
                app_state["status_type"] = "SCANNING"
                app_state["person_name"] = ""
                app_state["confidence"] = 0.0
        else:
            for bbox in faces:
                x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                name, conf = face_engine.predict_face(frame, (x, y, w, h))
                conf = float(conf)

                if name == "Unknown" and not face_engine.is_trained:
                    try:
                        known_encs = db.get_all_encodings()
                        cand_enc = face_engine.generate_encoding(frame, (x, y, w, h))
                        name, conf = face_engine.compare_encodings(cand_enc, known_encs, threshold=0.60)
                        conf = float(conf)
                    except Exception:
                        pass

                is_auth = (name != "Unknown")
                frame = face_engine.annotate_frame(frame, (x, y, w, h), name, conf, is_auth)

                if is_auth:
                    if not app_state["door_is_open"] and (now - app_state["last_trigger_time"] > 6.0):
                        app_state["last_trigger_time"] = now
                        app_state["door_is_open"] = True
                        app_state["scan_paused"] = True
                        app_state["status_type"] = "GRANTED"
                        app_state["person_name"] = str(name)
                        app_state["confidence"] = conf
                        app_state["seconds_remaining"] = app.config["DOOR_UNLOCK_DURATION"]
                        try:
                            esp32.send_command("UNLOCK")
                        except Exception:
                            pass
                        try:
                            db.log_access(name, "ACCESS GRANTED", conf, "Door Opened via WebCam")
                        except Exception:
                            pass
                        break
                else:
                    app_state["status_type"] = "DENIED"
                    app_state["person_name"] = "Unknown"
                    app_state["confidence"] = conf
                    if now - app_state["last_trigger_time"] > 6.0:
                        app_state["last_trigger_time"] = now
                        try:
                            esp32.send_command("ALARM")
                        except Exception:
                            pass
                        try:
                            db.log_access("Unknown", "ACCESS DENIED", conf, "Face Not Matched")
                        except Exception:
                            pass

        ret, buf = cv2.imencode('.jpg', frame)
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')

        return jsonify({
            "success": True,
            "status_type": str(app_state["status_type"]),
            "person_name": str(app_state["person_name"]),
            "confidence": float(app_state["confidence"]),
            "door_is_open": bool(app_state["door_is_open"]),
            "seconds_remaining": int(app_state["seconds_remaining"]),
            "annotated_image": annotated_b64
        })

    except Exception as e:
        print(f"[api_process_frame] Uncaught Exception: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 200


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# --- ACCESS LOGS & CSV EXPORTER ---

@app.route("/logs")
@login_required
def logs_view():
    logs = db.get_filtered_logs(limit=100)
    return render_template("logs.html", logs=logs)


@app.route("/export_csv")
@login_required
def export_csv():
    logs = db.get_filtered_logs(limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Person Name", "Date", "Time", "Status", "Confidence (%)", "Notes"])
    for log in logs:
        writer.writerow([log["id"], log["user_name"], log["date"], log["time"], log["status"], log["confidence"], log["notes"]])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"facesecure_logs_{int(time.time())}.csv"
    )


@app.route("/clear_logs", methods=["POST"])
@login_required
def clear_logs():
    db.delete_all_logs()
    flash("Access audit logs cleared successfully.", "success")
    return redirect(url_for("logs_view"))


if __name__ == "__main__":
    print("[FaceSecure] Full-Stack Web Application Server Starting...")
    print("[FaceSecure] Open Browser: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
