"""
FaceSecure - Face Recognition & Encoding Engine
Handles face detection, feature encoding generation, exponential bounding box smoothing, and real-time face matching.
"""

import os
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger("FaceEngine")

# Check if dlib/face_recognition module is present
try:
    import face_recognition
    HAS_FACE_RECOGNITION_LIB = True
    logger.info("dlib / face_recognition library detected and enabled.")
except ImportError:
    HAS_FACE_RECOGNITION_LIB = False
    logger.info("face_recognition library not present; using OpenCV Feature Engine.")


class FaceEngine:
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        
        # Safely attempt loading CascadeClassifier if exported by cv2
        cascade_cls = getattr(cv2, "CascadeClassifier", None)
        if cascade_cls is not None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cascade_cls(cascade_path)
            if self.face_cascade.empty():
                self.face_cascade = None
        else:
            self.face_cascade = None

        # Bounding box smoothing state (Exponential Moving Average filter)
        self.smoothed_box: Optional[Tuple[float, float, float, float]] = None
        self.alpha = 0.35 # Smoothing factor (0.0 to 1.0)
        self.missing_frames_count = 0

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detects faces in an OpenCV frame with temporal bounding box smoothing.
        Returns list of bounding boxes (x, y, w, h). Returns [] if no face is detected.
        """
        if frame is None or frame.size == 0:
            self.smoothed_box = None
            return []

        raw_boxes = []

        # 1. Primary Haar Cascade if available
        if self.face_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
                )
                if len(faces) > 0:
                    raw_boxes = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
            except Exception as e:
                logger.error(f"Error in Haar Cascade detection: {e}")

        # 2. face_recognition library detection fallback
        if not raw_boxes and HAS_FACE_RECOGNITION_LIB:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locations = face_recognition.face_locations(rgb)
                if locations:
                    raw_boxes = [(left, top, right - left, bottom - top) for (top, right, bottom, left) in locations]
            except Exception as e:
                logger.error(f"Error in face_recognition detection: {e}")

        # 3. Contour / skin-tone detector for faces
        if not raw_boxes:
            try:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower_skin = np.array([0, 30, 60], dtype=np.uint8)
                upper_skin = np.array([20, 150, 255], dtype=np.uint8)
                mask = cv2.inRange(hsv, lower_skin, upper_skin)
                mask = cv2.GaussianBlur(mask, (5, 5), 0)
                
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                h, w = frame.shape[:2]
                min_area = (h * w) * 0.08
                
                detected = []
                for c in contours:
                    area = cv2.contourArea(c)
                    if area > min_area:
                        bx, by, bw, bh = cv2.boundingRect(c)
                        aspect_ratio = float(bh) / float(bw)
                        if 0.9 <= aspect_ratio <= 1.9:
                            detected.append((bx, by, bw, bh))
                
                if detected:
                    raw_boxes = detected[:1]
            except Exception as e:
                logger.error(f"Error in skin-tone face detection: {e}")

        # Apply Bounding Box Smoothing Filter
        if not raw_boxes:
            self.missing_frames_count += 1
            if self.missing_frames_count > 3:
                self.smoothed_box = None
            return []

        self.missing_frames_count = 0
        rx, ry, rw, rh = raw_boxes[0]

        if self.smoothed_box is None:
            self.smoothed_box = (float(rx), float(ry), float(rw), float(rh))
        else:
            sx, sy, sw, sh = self.smoothed_box
            sx = self.alpha * rx + (1.0 - self.alpha) * sx
            sy = self.alpha * ry + (1.0 - self.alpha) * sy
            sw = self.alpha * rw + (1.0 - self.alpha) * sw
            sh = self.alpha * rh + (1.0 - self.alpha) * sh
            self.smoothed_box = (sx, sy, sw, sh)

        final_x, final_y, final_w, final_h = (
            int(self.smoothed_box[0]),
            int(self.smoothed_box[1]),
            int(self.smoothed_box[2]),
            int(self.smoothed_box[3]),
        )
        return [(final_x, final_y, final_w, final_h)]

    def generate_encoding(self, frame: np.ndarray, face_rect: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Generates face encoding vector for a face region or frame.
        """
        if frame is None or frame.size == 0:
            return None

        if HAS_FACE_RECOGNITION_LIB:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if face_rect:
                    x, y, w, h = face_rect
                    boxes = [(y, x + w, y + h, x)]
                else:
                    boxes = face_recognition.face_locations(rgb_frame)
                
                if boxes:
                    encodings = face_recognition.face_encodings(rgb_frame, boxes)
                    if encodings:
                        return encodings[0]
            except Exception as e:
                logger.error(f"Error generating encoding via face_recognition: {e}")

        try:
            if face_rect:
                x, y, w, h = face_rect
                fh, fw = frame.shape[:2]
                x1, y1 = max(0, x), max(0, y)
                x2, y2 = min(fw, x + w), min(fh, y + h)
                face_roi = frame[y1:y2, x1:x2]
            else:
                faces = self.detect_faces(frame)
                if not faces:
                    return None
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]

            if face_roi is None or face_roi.size == 0:
                return None

            resized = cv2.resize(face_roi, (128, 128))
            gray_roi = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

            hist = cv2.calcHist([gray_roi], [0], None, [128], [0, 256])
            cv2.normalize(hist, hist)
            
            small_img = cv2.resize(gray_roi, (8, 8)).flatten().astype(np.float32)
            cv2.normalize(small_img, small_img)
            
            combined = np.concatenate((hist.flatten()[:64], small_img[:64]))
            return combined
        except Exception as e:
            logger.error(f"Error generating fallback face encoding: {e}")
            return None

    def compare_encodings(
        self, candidate_encoding: np.ndarray, known_encodings: List[Tuple[str, np.ndarray]], threshold: Optional[float] = None
    ) -> Tuple[str, float]:
        """
        Compares candidate encoding against list of (user_name, encoding_array).
        Returns (user_name if confidence >= threshold else 'Unknown', confidence_percentage).
        """
        if candidate_encoding is None or not known_encodings:
            return ("Unknown", 0.0)

        eff_threshold = threshold if threshold is not None else self.confidence_threshold

        best_name = "Unknown"
        best_confidence = 0.0

        if HAS_FACE_RECOGNITION_LIB and len(candidate_encoding) == 128 and len(known_encodings[0][1]) == 128:
            known_vecs = [enc for name, enc in known_encodings]
            names = [name for name, enc in known_encodings]
            
            distances = face_recognition.face_distance(known_vecs, candidate_encoding)
            min_idx = int(np.argmin(distances))
            min_dist = float(distances[min_idx])
            
            confidence = max(0.0, min(100.0, (1.0 - min_dist) * 100))
            match_threshold = (1.0 - eff_threshold)

            if min_dist <= match_threshold and confidence >= (eff_threshold * 100):
                best_name = names[min_idx]
                best_confidence = confidence
            else:
                best_name = "Unknown"
                best_confidence = confidence
        else:
            c_norm = np.linalg.norm(candidate_encoding)
            if c_norm == 0:
                return ("Unknown", 0.0)

            highest_sim = -1.0
            matched_user = "Unknown"

            for name, k_enc in known_encodings:
                k_norm = np.linalg.norm(k_enc)
                if k_norm == 0:
                    continue
                similarity = np.dot(candidate_encoding, k_enc) / (c_norm * k_norm)
                if similarity > highest_sim:
                    highest_sim = similarity
                    matched_user = name

            confidence = max(0.0, min(100.0, float(highest_sim * 100)))

            if highest_sim >= eff_threshold and confidence >= (eff_threshold * 100):
                best_name = matched_user
                best_confidence = confidence
            else:
                best_name = "Unknown"
                best_confidence = confidence

        return (best_name, round(best_confidence, 1))

    def annotate_frame(
        self,
        frame: np.ndarray,
        face_rect: Tuple[int, int, int, int],
        name: str,
        confidence: float,
        is_authorized: bool
    ) -> np.ndarray:
        """
        Draws smoothed bounding box, label banner, and confidence score on OpenCV frame.
        """
        x, y, w, h = face_rect
        color = (5, 150, 105) if is_authorized else (38, 38, 220) # BGR: Emerald Green vs Crimson Red

        # Outer smooth bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        
        # Corner reticle accents
        line_len = max(10, int(w * 0.18))
        cv2.line(frame, (x, y), (x + line_len, y), color, 4)
        cv2.line(frame, (x, y), (x, y + line_len), color, 4)
        
        cv2.line(frame, (x + w, y), (x + w - line_len, y), color, 4)
        cv2.line(frame, (x + w, y), (x + w, y + line_len), color, 4)

        cv2.line(frame, (x, y + h), (x + line_len, y + h), color, 4)
        cv2.line(frame, (x, y + h), (x, y + h - line_len), color, 4)

        cv2.line(frame, (x + w, y + h), (x + w - line_len, y + h), color, 4)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - line_len), color, 4)

        # Label Header Banner
        label_str = f"{name} ({confidence:.1f}%)" if is_authorized else f"UNKNOWN ({confidence:.1f}%)"
        
        (text_w, text_h), baseline = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        
        banner_y1 = max(0, y - text_h - 12)
        banner_y2 = y
        cv2.rectangle(frame, (x, banner_y1), (x + max(w, text_w + 14), banner_y2), color, -1)
        
        cv2.putText(
            frame,
            label_str,
            (x + 6, banner_y2 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )
        return frame
