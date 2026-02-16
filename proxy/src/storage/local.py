"""
Local Storage Backend - SQLite

This is the same storage mechanism as the Community Edition.
All your existing database code from printer_monitor.py goes here.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .interface import StorageBackend


class LocalStorage(StorageBackend):
    """Local SQLite storage backend"""
    
    def __init__(self, database_file: str = "printer_monitoring.db"):
        """
        Initialize local storage
        
        Args:
            database_file: Path to SQLite database file
        """
        self.database_file = database_file
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Create printers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS printers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                model TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_pages INTEGER,
                toner_level_pct INTEGER,
                toner_status TEXT,
                drum_level_pct INTEGER,
                device_status INTEGER,
                FOREIGN KEY (printer_id) REFERENCES printers (id)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
            ON metrics(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_printer_id 
            ON metrics(printer_id)
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Local database initialized: {self.database_file}")
    
    def save_metrics(self, printer_id: str, metrics: Dict[str, Any]) -> bool:
        """Save printer metrics to local database"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Get printer database ID from IP
            cursor.execute('SELECT id FROM printers WHERE ip = ?', (printer_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"✗ Printer {printer_id} not found in database")
                conn.close()
                return False
            
            db_printer_id = result[0]
            
            # Insert metrics
            cursor.execute('''
                INSERT INTO metrics (
                    printer_id, timestamp, total_pages, toner_level_pct, 
                    toner_status, drum_level_pct, device_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                db_printer_id,
                datetime.now(),
                metrics.get('total_pages'),
                metrics.get('toner_level_pct'),
                metrics.get('toner_status'),
                metrics.get('drum_level_pct'),
                metrics.get('device_status')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Error saving metrics to local database: {e}")
            return False
    
    def get_or_create_printer(
        self, 
        ip: str, 
        name: str, 
        location: str = None, 
        model: str = None
    ) -> Optional[str]:
        """Get existing printer or create new one"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Check if printer exists
            cursor.execute('SELECT id, ip FROM printers WHERE ip = ?', (ip,))
            result = cursor.fetchone()
            
            if result:
                # Printer exists, return IP
                conn.close()
                return ip
            
            # Printer doesn't exist, create it
            cursor.execute('''
                INSERT INTO printers (ip, name, location, model)
                VALUES (?, ?, ?, ?)
            ''', (ip, name, location, model))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Registered new printer: {name} ({ip})")
            return ip
            
        except Exception as e:
            print(f"✗ Error registering printer: {e}")
            return None
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """Get list of all registered printers"""
        try:
            conn = sqlite3.connect(self.database_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, ip, name, location, model, first_seen
                FROM printers
                ORDER BY location, name
            ''')
            
            printers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return printers
            
        except Exception as e:
            print(f"✗ Error getting printers: {e}")
            return []
    
    def get_printer_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get printer information by IP address"""
        try:
            conn = sqlite3.connect(self.database_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, ip, name, location, model, first_seen
                FROM printers
                WHERE ip = ?
            ''', (ip,))
            
            result = cursor.fetchone()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            print(f"✗ Error getting printer: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if local storage is available"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return True
        except Exception as e:
            print(f"✗ Local storage health check failed: {e}")
            return False
