"""Date validation and calculation rules for Mess Cut Request.

Rules enforced:
1. Duration must be an exact multiple of 7 days (7, 14, 21, or 28 days), counted inclusively.
2. Start and end dates must remain strictly within the same calendar month (no cross-month cuts).
3. At least 7 consecutive days must remain in the month from the chosen start date.
4. End date cannot precede start date.
"""

from __future__ import annotations
import calendar
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def get_days_in_month(year: int, month: int) -> int:
    """Return number of days in month for given year."""
    return calendar.monthrange(year, month)[1]


def parse_iso_date(iso_str: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD into a datetime.date object. Return None if invalid."""
    if not iso_str or not isinstance(iso_str, str):
        return None
    iso_clean = iso_str.strip()
    try:
        parts = [int(p) for p in iso_clean.split("-")]
        if len(parts) != 3:
            return None
        return date(parts[0], parts[1], parts[2])
    except (ValueError, TypeError):
        return None


def format_iso_date(d: date) -> str:
    """Format date to YYYY-MM-DD."""
    return d.strftime("%Y-%m-%d")


def format_dd_mm_yyyy(d: Optional[date | str]) -> str:
    """Format date or YYYY-MM-DD string to DD-MM-YYYY."""
    if d is None:
        return ""
    if isinstance(d, str):
        parsed = parse_iso_date(d)
        if not parsed:
            return ""
        return parsed.strftime("%d-%m-%Y")
    return d.strftime("%d-%m-%Y")


def get_today_dd_mm_yyyy() -> str:
    """Get current system date formatted as DD-MM-YYYY."""
    return date.today().strftime("%d-%m-%Y")


def get_month_label(year: int, month: int) -> str:
    """Return human readable 'Month YYYY' label."""
    if 1 <= month <= 12:
        return f"{MONTH_NAMES[month - 1]} {year}"
    return f"{month}/{year}"


def get_valid_end_date_options(start_date_iso: str) -> Dict[str, Any]:
    """Calculate all valid same-month end dates in multiples of 7 days (inclusive)."""
    start = parse_iso_date(start_date_iso)
    if not start:
        return {
            "has_start": False,
            "can_accommodate": False,
            "remaining_days_in_month": 0,
            "days_in_month": 0,
            "month_label": "",
            "latest_valid_start_iso": None,
            "min_end_date_iso": None,
            "max_end_date_iso": None,
            "suggestions": []
        }

    days_in_month = get_days_in_month(start.year, start.month)
    remaining_days = days_in_month - start.day + 1
    month_label = get_month_label(start.year, start.month)
    latest_valid_start_day = days_in_month - 6
    latest_valid_start = date(start.year, start.month, latest_valid_start_day)
    latest_valid_start_iso = format_iso_date(latest_valid_start)

    if remaining_days < 7:
        return {
            "has_start": True,
            "can_accommodate": False,
            "remaining_days_in_month": remaining_days,
            "days_in_month": days_in_month,
            "month_label": month_label,
            "latest_valid_start_iso": latest_valid_start_iso,
            "min_end_date_iso": None,
            "max_end_date_iso": None,
            "suggestions": []
        }

    suggestions = []
    days = 7
    while days <= remaining_days:
        end_day = start.day + days - 1
        end_d = date(start.year, start.month, end_day)
        suggestions.append({
            "days": days,
            "iso": format_iso_date(end_d),
            "display": format_dd_mm_yyyy(end_d)
        })
        days += 7

    return {
        "has_start": True,
        "can_accommodate": True,
        "remaining_days_in_month": remaining_days,
        "days_in_month": days_in_month,
        "month_label": month_label,
        "latest_valid_start_iso": latest_valid_start_iso,
        "min_end_date_iso": suggestions[0]["iso"] if suggestions else None,
        "max_end_date_iso": suggestions[-1]["iso"] if suggestions else None,
        "suggestions": suggestions
    }


def validate_date_range(start_date_iso: str, end_date_iso: str) -> Dict[str, Any]:
    """Validate start and end dates against all mess cut rules."""
    if not start_date_iso:
        return {
            "is_valid": False,
            "code": "MISSING_START",
            "heading": "Select start and end dates",
            "message": "Choose a start date to view valid same-month end dates in multiples of 7 days.",
            "total_days": None,
            "start_display": "",
            "end_display": "",
            "suggestions": []
        }

    start = parse_iso_date(start_date_iso)
    if not start:
        return {
            "is_valid": False,
            "code": "INVALID_START",
            "heading": "Invalid start date",
            "message": "Please choose a valid start date from the calendar.",
            "total_days": None,
            "start_display": "",
            "end_display": "",
            "suggestions": []
        }

    options = get_valid_end_date_options(start_date_iso)
    start_display = format_dd_mm_yyyy(start)
    month_end_date = date(start.year, start.month, options["days_in_month"])
    month_end_display = format_dd_mm_yyyy(month_end_date)

    if not options["can_accommodate"]:
        latest_valid_display = format_dd_mm_yyyy(options["latest_valid_start_iso"])
        next_m = 1 if start.month == 12 else start.month + 1
        next_y = start.year + 1 if start.month == 12 else start.year
        next_month_start_display = format_dd_mm_yyyy(date(next_y, next_m, 1))

        rem = options["remaining_days_in_month"]
        day_plural = "day" if rem == 1 else "days"

        return {
            "is_valid": False,
            "code": "INSUFFICIENT_MONTH_DAYS",
            "heading": "Insufficient days remaining in month",
            "message": (
                f"Starting {start_display} leaves only {rem} consecutive {day_plural} in {options['month_label']} "
                f"(ending {month_end_display}). At least 7 consecutive days within the same month are required. "
                f"Select {latest_valid_display} or earlier, or start on {next_month_start_display}."
            ),
            "total_days": None,
            "start_display": start_display,
            "end_display": "",
            "suggestions": []
        }

    if not end_date_iso:
        suggestion_preview = ", ".join(f"{s['days']}d: {s['display']}" for s in options["suggestions"])
        return {
            "is_valid": False,
            "code": "MISSING_END",
            "heading": "Select a valid end date",
            "message": f"Choose one of the valid same-month end dates for {options['month_label']} ({suggestion_preview}).",
            "total_days": None,
            "start_display": start_display,
            "end_display": "",
            "suggestions": options["suggestions"]
        }

    end = parse_iso_date(end_date_iso)
    if not end:
        return {
            "is_valid": False,
            "code": "INVALID_END",
            "heading": "Invalid end date",
            "message": "Please choose a valid end date from the calendar or suggested durations.",
            "total_days": None,
            "start_display": start_display,
            "end_display": "",
            "suggestions": options["suggestions"]
        }

    end_display = format_dd_mm_yyyy(end)

    if end < start:
        return {
            "is_valid": False,
            "code": "END_BEFORE_START",
            "heading": "End date precedes start date",
            "message": f"End date ({end_display}) cannot be earlier than start date ({start_display}).",
            "total_days": None,
            "start_display": start_display,
            "end_display": end_display,
            "suggestions": options["suggestions"]
        }

    total_days = (end - start).days + 1

    if start.year != end.year or start.month != end.month:
        end_month_label = get_month_label(end.year, end.month)
        return {
            "is_valid": False,
            "code": "CROSS_MONTH_FORBIDDEN",
            "heading": "Cross-month requests are not permitted",
            "message": (
                f"Start date ({start_display}) is in {options['month_label']} and end date ({end_display}) "
                f"is in {end_month_label}. The entire mess cut must stay within {options['month_label']}."
            ),
            "total_days": total_days,
            "start_display": start_display,
            "end_display": end_display,
            "suggestions": options["suggestions"]
        }

    if total_days < 7 or total_days % 7 != 0:
        valid_list = ", ".join(f"{s['display']} ({s['days']} days)" for s in options["suggestions"])
        plural = "day" if total_days == 1 else "days"
        return {
            "is_valid": False,
            "code": "NOT_MULTIPLE_OF_7",
            "heading": f"Invalid duration ({total_days} {plural})",
            "message": (
                f"Inclusive duration from {start_display} to {end_display} is {total_days} {plural}. "
                f"Mess cut duration must strictly be a multiple of 7 days. "
                f"Valid end dates for {start_display}: {valid_list}."
            ),
            "total_days": total_days,
            "start_display": start_display,
            "end_display": end_display,
            "suggestions": options["suggestions"]
        }

    return {
        "is_valid": True,
        "code": "VALID",
        "heading": f"Valid Mess Cut Period ({total_days} Days)",
        "message": f"{start_display} to {end_display} is {total_days} inclusive days within {options['month_label']}.",
        "total_days": total_days,
        "start_display": start_display,
        "end_display": end_display,
        "suggestions": options["suggestions"]
    }


FIXED_RECIPIENT = "The Warden,\nMH 2 Hostel,\nRIT Kottayam."


def validate_complete_application(profile: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
    """Validate all student fields and dates to determine if PDF export is allowed."""
    missing_fields = []
    recipient = (profile.get("recipientAddress") or FIXED_RECIPIENT).strip()
    if not recipient:
        missing_fields.append("Recipient Address")
    if not (profile.get("name") or "").strip():
        missing_fields.append("Student Name")
    if not (profile.get("admissionNumber") or "").strip():
        missing_fields.append("Admission Number")
    if not (profile.get("semester") or "").strip():
        missing_fields.append("Semester")
    if not (profile.get("branch") or "").strip():
        missing_fields.append("Branch")
    if not (request.get("reason") or "").strip():
        missing_fields.append("Reason for Mess Cut")

    date_validation = validate_date_range(
        request.get("startDate") or "",
        request.get("endDate") or ""
    )

    is_ready_for_export = (len(missing_fields) == 0) and date_validation["is_valid"]

    return {
        "is_ready_for_export": is_ready_for_export,
        "missing_fields": missing_fields,
        "date_validation": date_validation
    }
