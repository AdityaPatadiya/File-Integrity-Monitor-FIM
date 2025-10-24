# src/api/routes/fim_routes.py
from flask import Blueprint, jsonify, request
from src.api.services.fim_service import get_events
from src.api.utils.jwt_utils import role_required, auth_required

fim_bp = Blueprint("fim_bp", __name__)

@fim_bp.route("/events", methods=["GET"])
@role_required("Admin", "Analyst")
def list_events():
    directory = request.args.get("dir")
    limit = int(request.args.get("limit", 200))
    events = get_events(directory=directory, limit=limit)
    return jsonify(events)

# Agent posts events (no auth for now or use client certs in future)
@fim_bp.route("/events", methods=["POST"])
def post_event():
    payload = request.json or {}
    # For now, simply acknowledge; in production validate agent auth
    # You can call an internal function to persist events, e.g., src.utils.database.save_event(...)
    return jsonify({"ok": True, "received": True, "payload_summary": {"keys": list(payload.keys())}}), 201
