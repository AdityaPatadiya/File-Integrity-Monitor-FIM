from cryptography.fernet import Fernet
import json
import os
import sys

# Add the path of the FIM file to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import FIM

# Generate a key (do this only once and save it securely)
def generate_key():
    key = Fernet.generate_key()
    with open("baseline.key", "wb") as key_file:
        key_file.write(key)

# Load the encryption key
def load_key():
    with open("baseline.key", "rb") as key_file:
        return key_file.read()

# Encrypt data
def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode())

# Decrypt data
def decrypt_data(data, key):
    f = Fernet(key)
    return f.decrypt(data).decode()

# Save encrypted baseline
def save_baseline_encrypted(baseline):
    key = load_key()
    encrypted_data = encrypt_data(json.dumps(baseline), key)
    with open(FIM.BASELINE_FILE, "wb") as f:
        f.write(encrypted_data)

# Load encrypted baseline
def load_baseline_encrypted():
    if os.path.exists(FIM.BASELINE_FILE):
        key = load_key()
        with open(FIM.BASELINE_FILE, "rb") as f:
            encrypted_data = f.read()
        return json.loads(decrypt_data(encrypted_data, key))
    return {}
