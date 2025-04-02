import getpass
import sqlite3
import hashlib


class Authentication:
    def __init__(self):
        self.conn = sqlite3.connect(r'db/Authentication.db')
        self.cursor = self.conn.cursor()
        self.create_user_table()

    def create_user_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_new_user(self):
        username = input("Enter new username: ")
        password = getpass.getpass("Enter new password: ")
        hashed_password = self.hash_password(password)
        try:
            self.cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            self.conn.commit()
            print("User registered successfully.")
        except sqlite3.IntegrityError:
            print("Username already exists. Please choose a different username.")

    def login_existing_user(self):
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        hashed_password = self.hash_password(password)
        self.cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_password))
        user = self.cursor.fetchone()
        if user:
            print("Authentication Successful.")
        else:
            print("Access denied! Incorrect username or password.")
            exit(1)

    def authorised_credentials(self):
        choice = input("Are you a new user? (yes/no): ").strip().lower()
        if choice == 'yes':
            self.register_new_user()
        elif choice == 'no':
            self.login_existing_user()
        else:
            print("Invalid choice. Please enter 'yes' or 'no'.")
            exit(1)

    def close_connection(self):
        self.conn.close()

# Example usage
if __name__ == "__main__":
    auth = Authentication()
    auth.authorised_credentials()
    auth.close_connection()