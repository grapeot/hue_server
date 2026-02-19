import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "smart_home.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type TEXT NOT NULL,
            device_name TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            data JSON NOT NULL
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_history_type_name 
        ON device_history(device_type, device_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_history_timestamp 
        ON device_history(timestamp)
    """)
    conn.commit()
    conn.close()

def save_device_state(device_type: str, device_name: str, data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO device_history (device_type, device_name, data)
        VALUES (?, ?, ?)
    """, (device_type, device_name, json.dumps(data)))
    conn.commit()
    conn.close()

def delete_rinnai_zero_temp_records():
    """Remove Rinnai records where inlet_temp=0 and outlet_temp=0 (invalid/stale data)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM device_history
        WHERE device_type = 'rinnai'
        AND (
            json_extract(data, '$.inlet_temp') = 0
            OR json_extract(data, '$.outlet_temp') = 0
        )
    """)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def get_device_history(device_type: str = None, device_name: str = None, hours: int = 24):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM device_history 
        WHERE timestamp >= datetime('now', ?)
    """
    params = [f"-{hours} hours"]
    
    if device_type:
        query += " AND device_type = ?"
        params.append(device_type)
    
    if device_name:
        query += " AND device_name = ?"
        params.append(device_name)
    
    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
