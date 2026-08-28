"""
FaceSecure - Database Manager
Handles SQLite database connections, table initialization, user encodings, and access logs.
"""

import os
import sqlite3
import datetime
import shutil
import pickle
from typing import List, Tuple, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger("DatabaseManager")

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "facesecure.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Creates tables if they do not exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Table 1: Users
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    photo_count INTEGER DEFAULT 0
                );
                """)

                # Table 2: FaceEncodings
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS FaceEncodings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    encoding_blob BLOB NOT NULL,
                    image_path TEXT,
                    FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE
                );
                """)

                # Table 3: AccessLogs
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
                logger.info("SQLite database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            raise e

    # --- User Management ---

    def add_user(self, name: str) -> Optional[int]:
        """Adds a new user if name does not already exist."""
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("User name cannot be empty.")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Users (name, photo_count) VALUES (?, 0);", (clean_name,))
                user_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Added new user: {clean_name} (ID: {user_id})")
                return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"User registration failed: User '{clean_name}' already exists.")
            return None
        except Exception as e:
            logger.error(f"Error adding user '{clean_name}': {e}")
            return None

    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at, photo_count FROM Users WHERE name = ?;", (name.strip(),))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "created_at": row[2], "photo_count": row[3]}
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at, photo_count FROM Users ORDER BY name ASC;")
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "created_at": r[2], "photo_count": r[3]} for r in rows]

    def delete_user(self, user_id: int) -> bool:
        """Deletes user and associated face encodings."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Users WHERE id = ?;", (user_id,))
                conn.commit()
                logger.info(f"Deleted user ID: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete user ID {user_id}: {e}")
            return False

    # --- Face Encodings Management ---

    def add_face_encoding(self, user_id: int, encoding_data: Any, image_path: str = "") -> bool:
        """Serializes encoding array and stores it in database, incrementing user photo_count."""
        try:
            blob = pickle.dumps(encoding_data)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO FaceEncodings (user_id, encoding_blob, image_path) VALUES (?, ?, ?);",
                    (user_id, blob, image_path)
                )
                cursor.execute(
                    "UPDATE Users SET photo_count = photo_count + 1 WHERE id = ?;",
                    (user_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save face encoding for user ID {user_id}: {e}")
            return False

    def get_all_encodings(self) -> List[Tuple[str, Any]]:
        """Returns list of (user_name, numpy_encoding_array)."""
        encodings = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.name, e.encoding_blob 
                    FROM FaceEncodings e
                    JOIN Users u ON e.user_id = u.id;
                """)
                rows = cursor.fetchall()
                for name, blob in rows:
                    array = pickle.loads(blob)
                    encodings.append((name, array))
        except Exception as e:
            logger.error(f"Error fetching face encodings: {e}")
        return encodings

    # --- Access Logs Management ---

    def log_access(self, user_name: str, status: str, confidence: float, notes: str = "") -> bool:
        """Records an access log entry in SQLite."""
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
            logger.error(f"Failed to log access attempt: {e}")
            return False

    def get_filtered_logs(self, search_query: str = "", status_filter: str = "All", date_filter: str = "") -> List[Dict[str, Any]]:
        """Retrieves access logs matching search and filter conditions."""
        query = "SELECT id, user_name, date, time, status, confidence, notes FROM AccessLogs WHERE 1=1"
        params = []

        if search_query:
            query += " AND (user_name LIKE ? OR notes LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if status_filter and status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)

        if date_filter:
            query += " AND date = ?"
            params.append(date_filter)

        query += " ORDER BY id DESC LIMIT 500;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
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
            logger.error(f"Error fetching logs: {e}")
            return []

    def delete_logs(self, log_ids: Optional[List[int]] = None) -> bool:
        """Deletes specified log IDs or clears all logs if log_ids is None."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if log_ids:
                    placeholders = ",".join("?" * len(log_ids))
                    cursor.execute(f"DELETE FROM AccessLogs WHERE id IN ({placeholders});", log_ids)
                else:
                    cursor.execute("DELETE FROM AccessLogs;")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete logs: {e}")
            return False

    def get_dashboard_counts(self) -> Dict[str, int]:
        """Returns summary metrics for Dashboard display."""
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        counts = {"users": 0, "today_access": 0, "unknown_attempts": 0}

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Registered Users Count
                cursor.execute("SELECT COUNT(*) FROM Users;")
                counts["users"] = cursor.fetchone()[0]

                # 2. Today's Total Access Count
                cursor.execute("SELECT COUNT(*) FROM AccessLogs WHERE date = ?;", (today_str,))
                counts["today_access"] = cursor.fetchone()[0]

                # 3. Today's Unknown / Denied Attempts
                cursor.execute("""
                    SELECT COUNT(*) FROM AccessLogs 
                    WHERE date = ? AND (status LIKE '%Denied%' OR user_name = 'Unknown');
                """, (today_str,))
                counts["unknown_attempts"] = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error fetching dashboard metrics: {e}")

        return counts

    def backup_database(self, destination_path: str) -> bool:
        """Creates a backup copy of the database."""
        try:
            shutil.copy2(self.db_path, destination_path)
            logger.info(f"Database backed up successfully to: {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
