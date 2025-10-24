import os
import time
import json
import hmac
import hashlib
import base64
from functools import wraps
from flask import request, jsonify

SECRET = os.getenv("API_SECRET_KEY", "replace_this_secret")
ALGORITHM = "HS256"
TOKEN_EXP_SECONDS = 60 * 60 * 24  # 24h, change if needed

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _b64url_decode(data: str) -> bytes:
    padding = '=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _sign(message: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode('utf-8'), message, hashlib.sha256).digest()

def create_token(payload: dict):
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload_copy = dict(payload)
    payload_copy.setdefault("iat", now)
    payload_copy.setdefault("exp", now + TOKEN_EXP_SECONDS)
    header_b64 = _b64url_encode(json.dumps(header, separators=(',',':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(payload_copy, separators=(',',':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
    signature = _b64url_encode(_sign(signing_input, SECRET))
    return f"{header_b64}.{payload_b64}.{signature}"

def decode_token(token: str):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b, payload_b, signature_b = parts
        signing_input = f"{header_b}.{payload_b}".encode('ascii')
        expected_sig = _b64url_encode(_sign(signing_input, SECRET))
        if not hmac.compare_digest(expected_sig, signature_b):
            return None
        payload_json = _b64url_decode(payload_b).decode('utf-8')
        payload = json.loads(payload_json)
        exp = payload.get("exp")
        if exp is not None and int(time.time()) > int(exp):
            return None
        return payload
    except Exception:
        return None

def get_auth_header():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return None

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = get_auth_header()
        if not token:
            return jsonify({"error": "Missing auth token"}), 401
        data = decode_token(token)
        if not data:
            return jsonify({"error": "Invalid token"}), 401
        # attach user info to request context
        request.user = data
        return fn(*args, **kwargs)
    return wrapper

def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = get_auth_header()
            if not token:
                return jsonify({"error": "Missing auth token"}), 401
            data = decode_token(token)
            if not data:
                return jsonify({"error": "Invalid token"}), 401
            role = data.get("role", "").lower()
            if role not in [r.lower() for r in allowed_roles]:
                return jsonify({"error": "Forbidden"}), 403
            request.user = data
            return fn(*args, **kwargs)
        return wrapper
    return decorator
