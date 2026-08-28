"""
FaceSecure Web Database Handler
Manages SQLite database operations for Admin Auth, Face Encodings stored in face_data/, and Access Audit Logs.
"""

import os
import sqlite3
import datetime
import pickle
import traceback
from typing import List, Tuple, Dict, Any, Optional
from werkzeug.security import generate_password_hash, check_password_hash

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "web_facesecure.db")
FACE_DATA_DIR = "face_data"


class WebDatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(FACE_DATA_DIR, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS AdminUsers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("PRAGMA table_info(RegisteredFaces);")
            columns = [col[1] for col in cursor.fetchall()]

            if "encoding_blob" in columns:
                cursor.execute("CREATE TABLE IF NOT EXISTS RegisteredFaces_temp (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, photo_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
                cursor.execute("INSERT OR IGNORE INTO RegisteredFaces_temp (id, name, created_at) SELECT id, name, created_at FROM RegisteredFaces;")
                cursor.execute("DROP TABLE RegisteredFaces;")
                cursor.execute("ALTER TABLE RegisteredFaces_temp RENAME TO RegisteredFaces;")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS RegisteredFaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                photo_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS FaceEncodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                image_path TEXT,
                encoding_blob BLOB NOT NULL,
                FOREIGN KEY (person_id) REFERENCES RegisteredFaces (id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS AccessLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                notes TEXT
            );
            """)

            conn.commit()

    # --- ADMIN AUTHENTICATION ---

    def register_admin(self, email: str, password: str) -> bool:
        email_clean = email.strip().lower()
        if not email_clean or not password:
            return False

        pwd_hash = generate_password_hash(password)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO AdminUsers (email, password_hash) VALUES (?, ?);",
                    (email_clean, pwd_hash)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"[WebDB] Admin registration error: {e}")
            return False

    def authenticate_admin(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        email_clean = email.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, password_hash FROM AdminUsers WHERE email = ?;", (email_clean,))
            row = cursor.fetchone()
            if row and check_password_hash(row[2], password):
                return {"id": row[0], "email": row[1]}
            return None

    # --- REGISTERED PERSON RECORDS & RE-ENROLLMENT ---

    def get_or_create_person(self, name: str) -> Optional[int]:
        clean_name = name.strip()
        if not clean_name:
            return None

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM RegisteredFaces WHERE name = ?;", (clean_name,))
                row = cursor.fetchone()
                if row:
                    person_id = row[0]
                    cursor.execute("DELETE FROM FaceEncodings WHERE person_id = ?;", (person_id,))
                    cursor.execute("UPDATE RegisteredFaces SET photo_count = 0 WHERE id = ?;", (person_id,))
                    conn.commit()
                    return person_id

                cursor.execute("INSERT INTO RegisteredFaces (name, photo_count) VALUES (?, 0);", (clean_name,))
                person_id = cursor.lastrowid
                conn.commit()
                return person_id
        except Exception as e:
            print(f"[WebDB] get_or_create_person error for '{clean_name}': {e}")
            traceback.print_exc()
            return None

    def add_face_encoding(self, person_id: int, image_path: str, encoding_data: Any) -> bool:
        if encoding_data is None:
            return False

        blob = pickle.dumps(encoding_data)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO FaceEncodings (person_id, image_path, encoding_blob) VALUES (?, ?, ?);",
                    (person_id, image_path, blob)
                )
                cursor.execute(
                    "UPDATE RegisteredFaces SET photo_count = photo_count + 1 WHERE id = ?;",
                    (person_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"[WebDB] add_face_encoding error for person_id {person_id}: {e}")
            return False

    def delete_person_record(self, person_id: int) -> List[str]:
        image_paths = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image_path FROM FaceEncodings WHERE person_id = ?;", (person_id,))
                rows = cursor.fetchall()
                image_paths = [r[0] for r in rows if r[0]]

                cursor.execute("DELETE FROM RegisteredFaces WHERE id = ?;", (person_id,))
                conn.commit()
        except Exception as e:
            print(f"[WebDB] delete_person_record error: {e}")
        return image_paths

    def purge_all_persons(self) -> List[str]:
        image_paths = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image_path FROM FaceEncodings;")
                rows = cursor.fetchall()
                image_paths = [r[0] for r in rows if r[0]]

                cursor.execute("DELETE FROM FaceEncodings;")
                cursor.execute("DELETE FROM RegisteredFaces;")
                conn.commit()
        except Exception as e:
            print(f"[WebDB] purge_all_persons error: {e}")
        return image_paths

    def get_all_persons(self) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, photo_count, created_at FROM RegisteredFaces ORDER BY name ASC;")
                rows = cursor.fetchall()

                result = []
                for r in rows:
                    person_id, name, count, created_at = r[0], r[1], r[2], r[3]
                    cursor.execute("SELECT image_path FROM FaceEncodings WHERE person_id = ? LIMIT 1;", (person_id,))
                    img_row = cursor.fetchone()
                    avatar_path = img_row[0] if img_row else ""
                    result.append({
                        "id": person_id,
                        "name": name,
                        "photo_count": count,
                        "photo_path": avatar_path,
                        "created_at": created_at
                    })
                return result
        except Exception as e:
            print(f"[WebDB] get_all_persons error: {e}")
            return []

    def get_all_encodings(self) -> List[Tuple[str, Any]]:
        encodings = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, e.encoding_blob 
                    FROM FaceEncodings e
                    JOIN RegisteredFaces p ON e.person_id = p.id;
                """)
                rows = cursor.fetchall()
                for name, blob in rows:
                    array = pickle.loads(blob)
                    encodings.append((name, array))
        except Exception as e:
            print(f"[WebDB] get_all_encodings error: {e}")
        return encodings

    # --- ACCESS LOGS ---

    def log_access(self, user_name: str, status: str, confidence: float, notes: str = "") -> bool:
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO AccessLogs (user_name, date, time, status, confidence, notes)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (user_name, date_str, time_str, status, round(confidence, 1), notes))
                conn.commit()
                return True
        except Exception as e:
            print(f"[WebDB] log_access error: {e}")
            return False

    def get_filtered_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, user_name, date, time, status, confidence, notes
                    FROM AccessLogs ORDER BY id DESC LIMIT ?;
                """, (limit,))
                rows = cursor.fetchall()
                return [
                    {
                        "id": r[0],
                        "user_name": r[1],
                        "date": r[2],
                        "time": r[3],
                        "status": r[4],
                        "confidence": r[5],
                        "notes": r[6]
                    } for r in rows
                ]
        except Exception as e:
            print(f"[WebDB] get_filtered_logs error: {e}")
            return []

    def delete_all_logs(self) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM AccessLogs;")
                conn.commit()
                return True
        except Exception as e:
            print(f"[WebDB] delete_all_logs error: {e}")
            return False
