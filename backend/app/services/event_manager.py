"""SQLite Event Manager for storing and querying violence detection events."""
import os
import sqlite3
import datetime
from typing import List, Optional, Dict, Any
from app.config import DB_PATH

class EventManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    camera_id TEXT NOT NULL,
                    start_timestamp TEXT NOT NULL,
                    detection_timestamp TEXT NOT NULL,
                    end_timestamp TEXT,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    image_path TEXT,
                    clip_path TEXT,
                    twilio_alert_sent INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            # Check if twilio_alert_sent column exists in existing DB tables
            cursor.execute("PRAGMA table_info(events)")
            columns = [col["name"] for col in cursor.fetchall()]
            if "twilio_alert_sent" not in columns:
                try:
                    cursor.execute("ALTER TABLE events ADD COLUMN twilio_alert_sent INTEGER DEFAULT 0")
                except Exception:
                    pass

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC)")
            conn.commit()

    def save_event(self, event_data: Dict[str, Any]) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO events (
                    id, camera_id, start_timestamp, detection_timestamp,
                    end_timestamp, confidence, status, image_path, clip_path,
                    twilio_alert_sent, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data["id"],
                event_data["camera_id"],
                event_data["start_timestamp"],
                event_data["detection_timestamp"],
                event_data.get("end_timestamp"),
                event_data["confidence"],
                event_data["status"],
                event_data.get("image_path"),
                event_data.get("clip_path"),
                1 if event_data.get("twilio_alert_sent") else 0,
                event_data.get("created_at", datetime.datetime.now().isoformat())
            ))
            conn.commit()
            return event_data["id"]

    def mark_alert_sent(self, event_id: str):
        """Records in the local database that a Twilio alert has been dispatched for this incident."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE events SET twilio_alert_sent = 1 WHERE id = ?", (event_id,))
            conn.commit()

    def is_alert_sent(self, event_id: str) -> bool:
        """Checks if a Twilio alert was already sent for this specific incident."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT twilio_alert_sent FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            if row and row["twilio_alert_sent"]:
                return bool(row["twilio_alert_sent"])
            return False

    def update_event_end(self, event_id: str, end_timestamp: str, clip_path: Optional[str] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if clip_path:
                cursor.execute("""
                    UPDATE events SET end_timestamp = ?, clip_path = ? WHERE id = ?
                """, (end_timestamp, clip_path, event_id))
            else:
                cursor.execute("""
                    UPDATE events SET end_timestamp = ? WHERE id = ?
                """, (end_timestamp, event_id))
            conn.commit()

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["twilio_alert_sent"] = bool(d.get("twilio_alert_sent", 0))
                results.append(d)
            return results

    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["twilio_alert_sent"] = bool(d.get("twilio_alert_sent", 0))
                return d
            return None

    def get_latest_event_for_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE camera_id = ? ORDER BY created_at DESC LIMIT 1", (camera_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["twilio_alert_sent"] = bool(d.get("twilio_alert_sent", 0))
                return d
            return None

    def get_total_events_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            return cursor.fetchone()[0]

event_manager = EventManager()
