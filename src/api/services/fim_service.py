# src/api/services/fim_service.py
"""
Service wrapper that calls your existing src/FIM/FIM.py logic.
It tries multiple common function/class names to be resilient to your implementation.
Adapt as needed to call exact function names.
"""
import importlib

def _load_fim_module():
    try:
        mod = importlib.import_module("src.FIM.FIM")
        return mod
    except Exception:
        try:
            # fallback module name
            return importlib.import_module("src.FIM.fim")
        except Exception:
            return None

def get_events(directory=None, limit=100):
    mod = _load_fim_module()
    if not mod:
        return {"error": "FIM module not found"}

    # try various functions
    candidates = [
        "get_file_changes", "get_recent_changes", "scan_directory", "list_changes", "get_changes"
    ]
    for name in candidates:
        fn = getattr(mod, name, None)
        if callable(fn):
            try:
                if directory:
                    return fn(directory, limit) if fn.__code__.co_argcount >= 1 else fn()
                return fn(limit) if fn.__code__.co_argcount == 1 else fn()
            except Exception:
                continue

    # try class based API
    for cls_name in ("FIM", "FileIntegrityMonitor", "Monitor"):
        cls = getattr(mod, cls_name, None)
        if cls:
            try:
                instance = cls()
                for method_name in ("get_changes", "get_recent_changes", "scan", "list_changes"):
                    method = getattr(instance, method_name, None)
                    if callable(method):
                        return method(directory) if directory else method()
            except Exception:
                continue

    return {"error": "No compatible FIM function found; adapt fim_service.py to your implementation"}
