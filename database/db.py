"""SQLite diagnostic history persistence.
"""
import os
import sqlite3
import json
import datetime
from typing import List, Dict, Any, Optional


DB_NAME = "diagnostic_history.db"


class DiagnosticDatabase:
    """Manages SQLite storage for all performed OBD scan sessions."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Save in current directory or user appdata
            self.db_path = os.path.abspath(DB_NAME)
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    vehicle_name TEXT,
                    port TEXT,
                    baudrate INTEGER,
                    elm_version TEXT,
                    protocol_name TEXT,
                    battery_voltage TEXT,
                    stored_codes TEXT,
                    pending_codes TEXT,
                    permanent_codes TEXT,
                    total_codes INTEGER,
                    advisor_notes TEXT,
                    raw_log TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id TEXT UNIQUE NOT NULL,
                    folder_path TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_sec REAL DEFAULT 0,
                    port TEXT,
                    elm_version TEXT,
                    protocol_name TEXT,
                    vin TEXT,
                    dtc_count INTEGER DEFAULT 0,
                    events_count INTEGER DEFAULT 0,
                    disconnect_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'EM_ANDAMENTO'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trip_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id TEXT NOT NULL,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    code TEXT,
                    title TEXT,
                    description TEXT,
                    timestamp TEXT NOT NULL,
                    folder_path TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_start ON trips (start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_trip ON trip_events (trip_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON trip_events (event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_code ON trip_events (code)")
            conn.commit()
        finally:
            conn.close()

    def save_session(
        self,
        vehicle_name: str,
        port: str,
        baudrate: int,
        elm_version: str,
        protocol_name: str,
        battery_voltage: str,
        stored_codes: List[str],
        pending_codes: List[str],
        permanent_codes: List[str],
        advisor_notes: str = "",
        raw_log: str = ""
    ) -> int:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = len(set(stored_codes + pending_codes + permanent_codes))

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scan_sessions (
                    created_at, vehicle_name, port, baudrate, elm_version,
                    protocol_name, battery_voltage, stored_codes, pending_codes,
                    permanent_codes, total_codes, advisor_notes, raw_log
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str,
                vehicle_name,
                port,
                baudrate,
                elm_version,
                protocol_name,
                battery_voltage,
                json.dumps(stored_codes),
                json.dumps(pending_codes),
                json.dumps(permanent_codes),
                total,
                advisor_notes,
                raw_log
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_sessions(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scan_sessions ORDER BY id DESC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["stored_codes"] = json.loads(item.get("stored_codes") or "[]")
                item["pending_codes"] = json.loads(item.get("pending_codes") or "[]")
                item["permanent_codes"] = json.loads(item.get("permanent_codes") or "[]")
                results.append(item)
            return results
        finally:
            conn.close()

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scan_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["stored_codes"] = json.loads(item.get("stored_codes") or "[]")
            item["pending_codes"] = json.loads(item.get("pending_codes") or "[]")
            item["permanent_codes"] = json.loads(item.get("permanent_codes") or "[]")
            return item
        finally:
            conn.close()

    def delete_session(self, session_id: int) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scan_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # Blackbox Trip methods
    def save_trip(self, trip_meta) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trips (
                    trip_id, folder_path, start_time, end_time, duration_sec,
                    port, elm_version, protocol_name, vin, dtc_count, events_count,
                    disconnect_count, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip_meta.trip_id,
                trip_meta.folder_path,
                trip_meta.start_time,
                trip_meta.end_time,
                trip_meta.duration_sec,
                trip_meta.port,
                trip_meta.elm_version,
                trip_meta.protocol_name,
                trip_meta.vin,
                trip_meta.dtc_count,
                trip_meta.events_count,
                trip_meta.disconnect_count,
                trip_meta.status
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_trips(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trips ORDER BY id DESC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def save_trip_event(self, ev, trip_id: str) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trip_events (
                    trip_id, event_id, event_type, code, title, description, timestamp, folder_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip_id,
                ev.event_id,
                ev.event_type,
                ev.code,
                ev.title,
                ev.description,
                ev.timestamp,
                ev.folder_path
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_trip_events(self, trip_id: Optional[str] = None, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM trip_events WHERE 1=1"
            params = []
            if trip_id:
                query += " AND trip_id = ?"
                params.append(trip_id)
            if event_type and event_type != "TODOS":
                query += " AND event_type = ?"
                params.append(event_type)
            query += " ORDER BY id DESC"
            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()


# Global database instance
db = DiagnosticDatabase()
