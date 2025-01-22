import sqlite3
import logging

class database_operation:
    def __init__(self):
        self.conn = sqlite3.connect('FIM.db')
        self.cursor = self.conn.cursor()

        logging.basicConfig(
            filename="FIM_Logging.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def database_table_creation(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS baseline(
                    path TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    last_modified TEXT NOT NULL
                    )
            ''')
            self.conn.commit()  # save changes to the database.
        except sqlite3.Error as e:
            logging.error(f"Database table creation failed: {e}")

    def store_information(self, baseline_data):
        try:
            for entry_path, entry_data in baseline_data.items():
                if entry_data:
                    file_hash = entry_data.get("hash", "")
                    modified_time = entry_data.get("last_modified", "")
                self.cursor.execute('INSERT OR REPLACE INTO baseline (path, hash, last_modified) VALUES (?, ?, ?)', (entry_path, file_hash, modified_time))
            self.conn.commit()
            # logging.info("Information successfuly stored in the database.")
        except sqlite3.Error as e:
            logging.error(f"Error storing information in the database: {e}")

    def fetch_data(self, file_path):
        try:
            self.cursor.execute('SELECT hash FROM baseline WHERE path=?', (file_path,))
            result = self.cursor.fetchone()
            if result == None:
                return None
            else:
                return result[0]
        except sqlite3.Error as e:
            logging.error(f"Error while fetching the data: {e}")

    def close_connection(self):
        try:
            self.conn.close()
            print("connection is closed.")
        except sqlite3.Error as e:
            logging.error(f"Error closing database connection: {e}")
