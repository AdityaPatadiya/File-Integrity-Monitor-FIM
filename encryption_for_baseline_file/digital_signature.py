from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
import json, os
import sys

# Add the path of the FIM file to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import FIM

# Generate a key pair (do this only once)
def generate_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Save private key
    with open("private_key.pem", "wb") as priv_file:
        priv_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Save public key
    with open("public_key.pem", "wb") as pub_file:
        pub_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

# Sign data
def sign_data(data, private_key_path="private_key.pem"):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)

    signature = private_key.sign(
        data.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return signature

# Verify signature
def verify_signature(data, signature, public_key_path="public_key.pem"):
    with open(public_key_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read())

    try:
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# Save baseline with signature
def save_baseline_with_signature(baseline):
    data = json.dumps(baseline)
    signature = sign_data(data)
    with open(FIM.BASELINE_FILE, "w") as f:
        f.write(data)
    with open(FIM.BASELINE_FILE + ".sig", "wb") as sig_file:
        sig_file.write(signature)

# Load baseline and verify signature
def load_baseline_with_signature():
    if os.path.exists(FIM.BASELINE_FILE) and os.path.exists(FIM.BASELINE_FILE + ".sig"):
        with open(FIM.BASELINE_FILE, "r") as f:
            data = f.read()
        with open(FIM.BASELINE_FILE + ".sig", "rb") as sig_file:
            signature = sig_file.read()

        if verify_signature(data, signature):
            return json.loads(data)
        else:
            raise ValueError("Baseline file signature verification failed.")
    return {}
