import sqlite3
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class database_operation:
    def __init__(self):
        self.db_path = Path('db/FIM.db')
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._thread_local = threading.local()
        self.lock = threading.Lock()  # For thread safety
        self._initialize_schema()

    def _get_connection(self):
        """Get or create a thread-local database connection."""
        if not hasattr(self._thread_local, 'conn'):
            self._thread_local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._thread_local.conn.execute('PRAGMA journal_mode=WAL')
            self._thread_local.conn.execute('PRAGMA synchronous=NORMAL')
        return self._thread_local.conn

    def _initialize_schema(self):
        """Initialize database schema with proper normalization"""
        print("database initialized.\n")
        with self.transaction():
            print("_initialize_schema with loop is called.\n")
            self._get_connection().cursor().execute('''
                CREATE TABLE IF NOT EXISTS directories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("cursor is executed.\n")
            self._get_connection().cursor().execute('''
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directory_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    status TEXT CHECK(status IN ('added', 'modified', 'deleted', 'current')),
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(directory_id) REFERENCES directories(id),
                    UNIQUE(directory_id, file_path)
                )
            ''')

            # Create indexes for faster queries
            self._get_connection().cursor().execute('''
                CREATE INDEX IF NOT EXISTS idx_file_path 
                ON file_metadata(file_path)
            ''')
            
            self._get_connection().cursor().execute('''
                CREATE INDEX IF NOT EXISTS idx_status 
                ON file_metadata(status)
            ''')

    @contextmanager
    def transaction(self):
        print("TRANSACTION STARTED")
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            with self.lock:
                print("LOCK ACQUIRED")
                yield cursor
                conn.commit()
                print("TRANSACTION COMMITTED")
        except Exception as e:
            print(f"TRANSACTION ERROR: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()

    def get_or_create_directory(self, directory_path: str) -> int:
        """Get or create directory entry, returns directory ID"""
        print("get_or_create_directory method called.\n")
        with self.transaction() as cursor:
            print("with loop of get_or_create_directory in database is called.\n")
            print(f"1st directory_path: {directory_path}\n")
            cursor.execute(
                'INSERT OR IGNORE INTO directories (path) VALUES (?)',
                (directory_path,)
            )
            print(f"2nd directory_path: {directory_path}\n")
            cursor.execute(
                'SELECT id FROM directories WHERE path = ?',
                (directory_path,)
            )
            print(f"3rd directory_path: {directory_path}\n")
            result = cursor.fetchone()
            print(f"self.cursor.fetchone(): {result[0]}")
            return result[0]

    def record_file_event(self, directory_path: str, file_path: str, 
                        file_hash: str, last_modified: str, status: str):
        """Record file event with proper transaction handling"""
        print("record_file_event method called.\n")
        with self.transaction() as cursor:
            dir_id = self.get_or_create_directory(directory_path)
            print(f"dir_id: {dir_id}")
            
            cursor.execute('''
                INSERT INTO file_metadata 
                (directory_id, file_path, hash, last_modified, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(directory_id, file_path) DO UPDATE SET
                    hash = excluded.hash,
                    last_modified = excluded.last_modified,
                    status = excluded.status,
                    detected_at = CURRENT_TIMESTAMP
            ''', (dir_id, file_path, file_hash, last_modified, status))

    def get_current_baseline(self, directory_path: str) -> Dict[str, dict]:
        """Get current baseline for a directory"""
        with self.transaction() as cursor:
            cursor.execute('''
                SELECT f.file_path, f.hash, f.last_modified
                FROM file_metadata f
                JOIN directories d ON f.directory_id = d.id
                WHERE d.path = ? AND f.status = 'current'
            ''', (directory_path,))

            return {
                row[0]: {'hash': row[1], 'last_modified': row[2]}
                for row in cursor.fetchall()
            }

    def get_file_history(self, file_path: str, limit: int = 10) -> List[Tuple]:
        """Get historical changes for a specific file"""
        with self.transaction() as cursor:
            cursor.execute('''
                SELECT d.path, f.hash, f.last_modified, f.status, f.detected_at
                FROM file_metadata f
                JOIN directories d ON f.directory_id = d.id
                WHERE f.file_path = ?
                ORDER BY f.detected_at DESC
                LIMIT ?
            ''', (file_path, limit))
            return cursor.fetchall()

    def update_file_hash(self, file_path: str, new_hash: str, 
                       last_modified: str, status: str = 'modified'):
        """Update existing file entry"""
        with self.transaction() as cursor:
            cursor.execute('''
                UPDATE file_metadata
                SET hash = ?, last_modified = ?, status = ?
                WHERE file_path = ?
            ''', (new_hash, last_modified, status, file_path))

    def delete_file_record(self, file_path: str):
        """Mark file as deleted in database"""
        with self.transaction() as cursor:
            cursor.execute('''
                UPDATE file_metadata
                SET status = 'deleted', detected_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            ''', (file_path,))
    
    def delete_directory_records(self, directory_path: str):
        """Delete all records for a directory"""
        with self.transaction() as cursor:
            cursor.execute('''
                DELETE FROM file_metadata
                WHERE directory_id IN (
                    SELECT id FROM directories WHERE path = ?
                )
            ''', (directory_path,))
            cursor.execute('''
                DELETE FROM directories WHERE path = ?
            ''', (directory_path,))

    def get_recent_changes(self, hours: int = 24) -> List[Tuple]:
        """Get recent changes across all directories"""
        with self.transaction() as cursor:
            cursor.execute('''
                SELECT d.path, f.file_path, f.status, f.detected_at
                FROM file_metadata f
                JOIN directories d ON f.directory_id = d.id
                WHERE f.detected_at >= datetime('now', ?)
                ORDER BY f.detected_at DESC
            ''', (f'-{hours} hours',))
            return cursor.fetchall()

    def close_connection(self):
        """Close database connection safely"""
        try:
            if hasattr(self._thread_local, 'conn'):
                self._thread_local.conn.close()
                logging.info("Database connection closed")
        except sqlite3.Error as e:
            logging.error(f"Error closing connection: {str(e)}")

    def __del__(self):
        """Destructor to ensure connection closure"""
        self.close_connection()
