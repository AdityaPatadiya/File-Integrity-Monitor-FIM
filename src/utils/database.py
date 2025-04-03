import mysql.connector
from mysql.connector import pooling, Error as MySQLerror
import logging
import os
from contextlib import contextmanager
from typing import Dict, List, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class database_operation:
    _instance = None
    _pool = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_pool()
            cls._instance._initialize_schema()
        return cls._instance

    def _initialize_pool(self):
        """Initialize MySQL connection pool with environment variables"""
        try:
            self._pool = pooling.MySQLConnectionPool(
                pool_name="fim_pool",
                pool_size=int(os.getenv('DB_POOL_SIZE', '32')),
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                autocommit=False,
                sql_mode='TRADITIONAL',
                charset='utf8mb4',
                collation='utf8mb4_bin',
            )
            # Test connection
            test_conn = self._pool.get_connection()
            try:
                cursor = test_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()  # Consume results
            finally:
                cursor.close()
                test_conn.close()

        except MySQLerror as e:
            logging.error(f"Database connection failed: {e}")
            raise

    def _initialize_schema(self):
        """Initialize database schema with proper error handling"""
        conn = self._pool.get_connection()
        cursor = conn.cursor()
        try:
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS directories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    path VARCHAR(512) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    directory_id INT NOT NULL,
                    file_path VARCHAR(512) NOT NULL,
                    hash VARCHAR(64) NOT NULL,
                    last_modified DATETIME NOT NULL,
                    status ENUM('added', 'modified', 'deleted', 'current') NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (directory_id) REFERENCES directories(id),
                    UNIQUE KEY (directory_id, file_path(255))
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
            ''')

            # Create indexes with error handling
            try:
                cursor.execute('''
                    CREATE INDEX idx_file_path 
                    ON file_metadata(file_path(255))
                ''')
            except MySQLerror as err:
                if err.errno != 1061:  # Duplicate key error
                    raise

            try:
                cursor.execute('''
                    CREATE INDEX idx_status 
                    ON file_metadata(status)
                ''')
            except MySQLerror as err:
                if err.errno != 1061:
                    raise

            conn.commit()
        except MySQLerror as e:
            conn.rollback()
            logging.error(f"Schema initialization failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @contextmanager
    def transaction(self):
        """Provide transactional scope with connection pooling"""
        conn = self._pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Transaction failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_or_create_directory(self, directory_path: str) -> int:
        """Get or create directory entry, returns directory ID"""
        with self.transaction() as cursor:
            cursor.execute(
                'INSERT IGNORE INTO directories (path) VALUES (%s)',
                (directory_path,)
            )
            cursor.execute(
                'SELECT id FROM directories WHERE path = %s',
                (directory_path,)
            )
            return cursor.fetchone()[0]

    def record_file_event(self, directory_path: str, file_path: str, 
                        file_hash: str, last_modified: str, status: str):
        """Record file event with proper transaction handling"""
        with self.transaction() as cursor:
            dir_id = self.get_or_create_directory(directory_path)
            cursor.execute('''
                INSERT INTO file_metadata 
                (directory_id, file_path, hash, last_modified, status)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    hash = VALUES(hash),
                    last_modified = VALUES(last_modified),
                    status = VALUES(status)
            ''', (dir_id, file_path, file_hash, last_modified, status))

    def get_current_baseline(self, directory_path: str) -> Dict[str, dict]:
        """Get current baseline for a directory"""
        with self.transaction() as cursor:
            cursor.execute('''
                SELECT f.file_path, f.hash, f.last_modified
                FROM file_metadata f
                JOIN directories d ON f.directory_id = d.id
                WHERE d.path = %s AND f.status = 'current'
            ''', (directory_path,))
            return {
                row[0]: {'hash': row[1], 'last_modified': row[2]}
                for row in cursor.fetchall()
            }

    def get_all_monitored_directories(self):
        """Get all directories with baseline data"""
        with self.transaction() as cursor:
            cursor.execute("SELECT DISTINCT path FROM directories")
            return [row[0] for row in cursor.fetchall()]

    def get_file_history(self, file_path: str, limit: int = 10) -> List[Tuple]:
        """Get historical changes for a specific file"""
        with self.transaction() as cursor:
            cursor.execute('''
                SELECT d.path, f.hash, f.last_modified, f.status, f.detected_at
                FROM file_metadata f
                JOIN directories d ON f.directory_id = d.id
                WHERE f.file_path = %s
                ORDER BY f.detected_at DESC
                LIMIT %s
            ''', (file_path, limit))
            return cursor.fetchall()

    def update_file_hash(self, file_path: str, new_hash: str, 
                       last_modified: str, status: str = 'modified'):
        """Update existing file entry"""
        with self.transaction() as cursor:
            cursor.execute('''
                UPDATE file_metadata
                SET hash = %s, last_modified = %s, status = %s
                WHERE file_path = %s
            ''', (new_hash, last_modified, status, file_path))

    def delete_file_record(self, file_path: str):
        """Mark file as deleted in database"""
        with self.transaction() as cursor:
            cursor.execute('''
                UPDATE file_metadata
                SET status = 'deleted', detected_at = CURRENT_TIMESTAMP
                WHERE file_path = %s
            ''', (file_path,))
    
    def delete_directory_records(self, directory_path: str):
        """Delete all records for a directory"""
        with self.transaction() as cursor:
            cursor.execute('''
                DELETE FROM file_metadata
                WHERE directory_id IN (
                    SELECT id FROM directories WHERE path = %s
                )
            ''', (directory_path,))
            cursor.execute('''
                DELETE FROM directories WHERE path = %s
            ''', (directory_path,))

    def get_recent_changes(self, hours: int = 24) -> List[Tuple]:
        """Get recent changes across all directories"""
        with self.transaction() as cursor:
            cursor.execute('''
                SELECT d.path, f.file_path, f.status, f.detected_at
                FROM file_metadata f
                JOIN directories d ON f.directory_id = d.id
                WHERE f.detected_at >= NOW() - INTERVAL %s HOUR
                ORDER BY f.detected_at DESC
            ''', (hours,))
            return cursor.fetchall()
