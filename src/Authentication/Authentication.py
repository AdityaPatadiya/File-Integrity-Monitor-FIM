import getpass
import hashlib
import logging
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)


class Authentication:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.create_database_if_not_exists()
        self.connect_to_db()
        self.create_user_table()

    def create_database_if_not_exists(self):
        try:
            temp_config = {
                "host": os.getenv('DB_HOST'),
                "user": os.getenv('DB_USER'),
                "password": os.getenv('DB_PASSWORD'),
            }

            cnx = mysql.connector.connect(**temp_config)
            cursor = cnx.cursor()
            db_name = os.getenv('AUTH_DB_NAME')

            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin")
            logging.info(f"Database '{db_name}' verified or created.")
            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            logging.error(f"❌ Error checking/creating database '{os.getenv('DB_NAME')}': {err}")
            raise

    def connect_to_db(self):
        """Connect to MySQL database using environment variables"""
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('AUTH_DB_NAME', 'fim_auth_db')
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            exit(1)

    def create_user_table(self):
        """Create users table if not exists"""
        if self.cursor is None or self.conn is None:
            print("Database connection or cursor is not initialized. Table creation aborted.")
            exit(1)
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(255) PRIMARY KEY,
                    password CHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Table creation failed: {err}")
            exit(1)

    def hash_password(self, password):
        """SHA-256 hash with salt"""
        salt = os.getenv('PEPPER', 'default-secret-pepper')
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def register_new_user(self):
        """Register new user with validation"""
        if self.cursor is None or self.conn is None:
            print("Database connection or cursor is not initialized. Table creation aborted.")
            exit(1)
        username = input("Enter new username: ").strip()
        if not username:
            print("Username cannot be empty")
            return

        password = getpass.getpass("Enter new password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters")
            exit(0)

        hashed_password = self.hash_password(password)

        try:
            self.cursor.execute(
                'INSERT INTO users (username, password) VALUES (%s, %s)',
                (username, hashed_password)
            )
            self.conn.commit()
            print("User registered successfully")
            return username
        except mysql.connector.IntegrityError:
            print("Username already exists. Try to Log In!!\n")
            self.login_existing_user()
        except mysql.connector.Error as err:
            print(f"Registration failed: {err}")

    def login_existing_user(self):
        """Authenticate existing user"""
        if self.cursor is None:
            print("Database connection or cursor is not initialized. Table creation aborted.")
            exit(1)
        username = input("Enter username: ").strip()
        password = getpass.getpass("Enter password: ")
        hashed_password = self.hash_password(password)

        try:
            self.cursor.execute(
                'SELECT username FROM users WHERE username = %s AND password = %s',
                (username, hashed_password)
            )
            user = self.cursor.fetchone()
            if user:
                print("Authentication successful")
            else:
                print("Access denied")
                exit(1)
            return username
        except mysql.connector.Error as err:
            print(f"Login error: {err}")
            exit(1)

    def authorised_credentials(self):
        """Main authentication flow"""
        while True:
            choice = input("Are you a new user? (yes/no): ").strip().lower()
            if choice == 'yes':
                return self.register_new_user()
            elif choice == 'no':
                return self.login_existing_user()
            print(f"Invalid choice. Please enter 'yes' or 'no'.\nYou've entred: {choice}")

    def close_connection(self):
        """Clean up database resources"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
