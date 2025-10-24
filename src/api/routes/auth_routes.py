from flask import Blueprint, request, jsonify, current_app
from src.api.utils.jwt_utils import create_token, auth_required
import importlib

auth_bp = Blueprint("auth_bp", __name__)

# Try to import your existing Authentication class
Auth = None
try:
    auth_mod = importlib.import_module("src.Authentication.Authentication")
    # common names: Authentication, Auth, auth
    Auth = getattr(auth_mod, "Authentication", None) or getattr(auth_mod, "Auth", None) or getattr(auth_mod, "auth", None)
except Exception:
    Auth = None

_auth_instance = Auth() if Auth else None

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    # If your Authentication class has a register/create_user method, call it
    if _auth_instance:
        for fn_name in ("register", "create_user", "add_user"):
            fn = getattr(_auth_instance, fn_name, None)
            if callable(fn):
                result = fn(username, password)
                return jsonify({"ok": True, "result": result}), 201
    # fallback: echo
    return jsonify({"error": "Registration not implemented in Authentication module"}), 501

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    user_obj = None

    if _auth_instance:
        # try common login functions
        for fn_name in ("login", "authenticate", "verify"):
            fn = getattr(_auth_instance, fn_name, None)
            if callable(fn):
                try:
                    user_obj = fn(username, password)
                    break
                except TypeError:
                    # maybe function signature differs; try other fn
                    continue

    if not user_obj:
        # fallback: simple check (for demo only)
        if username == "admin" and password == "admin":
            user_obj = {"username": "admin", "role": "Admin"}
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    # user_obj expected to be a dict-like with at least 'username' and 'role'
    role = user_obj.get("role", "Admin")
    payload = {"username": user_obj.get("username"), "role": role}
    token = create_token(payload)
    return jsonify({"token": token, "user": payload})

@auth_bp.route("/me", methods=["GET"])
@auth_required
def me():
    # request.user injected by decorator
    return jsonify({"user": request.user})
