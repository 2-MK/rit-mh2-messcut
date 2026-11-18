"""Persistence layer for Student Details and Mess Cut Draft.
Stores data safely in a local JSON file (data/profiles.json).
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "profiles.json")
FIXED_RECIPIENT = "The Warden,\nMH 2 Hostel,\nRIT Kottayam."


def _ensure_storage_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(STORAGE_FILE):
        default_data = {
            "student": {
                "name": "",
                "admissionNumber": "",
                "semester": "",
                "branch": "",
                "recipientAddress": FIXED_RECIPIENT,
                "updatedAt": datetime.now().isoformat()
            },
            "requestDraft": {
                "reason": "",
                "startDate": "",
                "endDate": ""
            }
        }
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)


def _read_data() -> Dict[str, Any]:
    _ensure_storage_file()
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "student": {
                "name": "",
                "admissionNumber": "",
                "semester": "",
                "branch": "",
                "recipientAddress": FIXED_RECIPIENT
            },
            "requestDraft": {}
        }


def _write_data(data: Dict[str, Any]) -> bool:
    _ensure_storage_file()
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_student_data() -> Dict[str, str]:
    """Load the saved student information."""
    data = _read_data()
    # Migrate legacy format if present
    if "student" in data and isinstance(data["student"], dict):
        s = data["student"]
        return {
            "name": s.get("name", ""),
            "admissionNumber": s.get("admissionNumber", ""),
            "semester": s.get("semester", ""),
            "branch": s.get("branch", ""),
            "recipientAddress": FIXED_RECIPIENT
        }
    elif "profiles" in data and isinstance(data["profiles"], list) and len(data["profiles"]) > 0:
        p = data["profiles"][0]
        return {
            "name": p.get("name", ""),
            "admissionNumber": p.get("admissionNumber", ""),
            "semester": p.get("semester", ""),
            "branch": p.get("branch", ""),
            "recipientAddress": FIXED_RECIPIENT
        }
    return {
        "name": "",
        "admissionNumber": "",
        "semester": "",
        "branch": "",
        "recipientAddress": FIXED_RECIPIENT
    }


def save_student_data(student: Dict[str, Any]) -> bool:
    """Save student information."""
    data = _read_data()
    data["student"] = {
        "name": (student.get("name") or "").strip(),
        "admissionNumber": (student.get("admissionNumber") or "").strip(),
        "semester": (student.get("semester") or "").strip(),
        "branch": (student.get("branch") or "").strip(),
        "recipientAddress": FIXED_RECIPIENT,
        "updatedAt": datetime.now().isoformat()
    }
    return _write_data(data)


def load_request_draft() -> Dict[str, str]:
    """Load current mess cut request draft."""
    data = _read_data()
    draft = data.get("requestDraft", {})
    return {
        "reason": typeof_str(draft.get("reason")),
        "startDate": typeof_str(draft.get("startDate")),
        "endDate": typeof_str(draft.get("endDate")),
    }


def save_request_draft(draft: Dict[str, Any]) -> bool:
    """Save mess cut request draft."""
    data = _read_data()
    data["requestDraft"] = {
        "reason": (draft.get("reason") or "").strip(),
        "startDate": (draft.get("startDate") or "").strip(),
        "endDate": (draft.get("endDate") or "").strip()
    }
    return _write_data(data)


def clear_all_data() -> bool:
    """Clear student details and draft."""
    data = {
        "student": {
            "name": "",
            "admissionNumber": "",
            "semester": "",
            "branch": "",
            "recipientAddress": FIXED_RECIPIENT
        },
        "requestDraft": {"reason": "", "startDate": "", "endDate": ""}
    }
    return _write_data(data)


def typeof_str(val: Any) -> str:
    return str(val).strip() if val else ""
