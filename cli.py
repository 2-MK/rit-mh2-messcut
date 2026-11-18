#!/usr/bin/env python3
"""Command-line interface to generate validated Mess Cut Request PDFs."""

from __future__ import annotations
import argparse
import sys
from datetime import date, timedelta
from date_rules import (
    format_dd_mm_yyyy,
    get_valid_end_date_options,
    parse_iso_date,
    validate_complete_application,
)
from pdf_generator import save_mess_cut_pdf_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate formal Mess Cut Request PDF from terminal with strict academic validation."
    )
    parser.add_argument("--name", help="Student full name")
    parser.add_argument("--admission", help="Admission number")
    parser.add_argument("--semester", default="S5", help="Current semester")
    parser.add_argument("--branch", default="Computer Science & Engineering", help="Engineering branch")
    parser.add_argument("--recipient", default="The Warden,\nMH 2 Hostel,\nRIT Kottayam.", help="Recipient address lines")
    parser.add_argument("--reason", help="Reason for mess cut request")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, choices=[7, 14, 21, 28], help="Duration in days (alternative to --end)")
    parser.add_argument("--output-dir", default="output", help="Directory to save the PDF (default: output)")

    args = parser.parse_args()

    # Interactive prompt if required arguments not provided
    name = args.name or input("Student Name: ").strip()
    admission = args.admission or input("Admission Number: ").strip()
    semester = args.semester or input("Semester: ").strip()
    branch = args.branch or input("Branch: ").strip()
    recipient = args.recipient or "The Warden,\nMH 2 Hostel,\nRIT Kottayam."
    reason = args.reason or input("Reason for Mess Cut: ").strip()
    start_date = args.start or input("Start Date (YYYY-MM-DD): ").strip()

    end_date = args.end
    if not end_date and args.days:
        start_d = parse_iso_date(start_date)
        if start_d:
            end_d = start_d + timedelta(days=args.days - 1)
            end_date = end_d.strftime("%Y-%m-%d")

    if not end_date:
        options = get_valid_end_date_options(start_date)
        if not options["can_accommodate"]:
            print(f"Error: Selected start date leaves fewer than 7 days in the month.")
            sys.exit(1)
        print("\nAvailable valid end dates:")
        for i, s in enumerate(options["suggestions"], 1):
            print(f"  [{i}] {s['days']} Days -> End date: {s['display']} ({s['iso']})")
        choice = input(f"Select choice (1-{len(options['suggestions'])}): ").strip()
        try:
            idx = int(choice) - 1
            end_date = options["suggestions"][idx]["iso"]
        except (ValueError, IndexError):
            print("Invalid choice selected.")
            sys.exit(1)

    profile = {
        "name": name,
        "admissionNumber": admission,
        "semester": semester,
        "branch": branch,
        "recipientAddress": recipient
    }
    request = {
        "reason": reason,
        "startDate": start_date,
        "endDate": end_date
    }

    evaluation = validate_complete_application(profile, request)
    if not evaluation["is_ready_for_export"]:
        print("\n[VALIDATION FAILED]")
        if evaluation["missing_fields"]:
            print("Missing required fields:", ", ".join(evaluation["missing_fields"]))
        if not evaluation["date_validation"]["is_valid"]:
            print("Date rule error:", evaluation["date_validation"]["message"])
        sys.exit(1)

    filepath = save_mess_cut_pdf_file(profile, request, output_dir=args.output_dir)
    print("\n" + "=" * 60)
    print("SUCCESS: Mess Cut Request PDF generated successfully!")
    print(f"File:       {filepath}")
    print(f"Student:    {name} ({admission})")
    print(f"Period:     {format_dd_mm_yyyy(start_date)} to {format_dd_mm_yyyy(end_date)} ({evaluation['date_validation']['total_days']} Days)")
    print("Design:     Minimalist Executive Monochrome & Slate")
    print("=" * 60)


if __name__ == "__main__":
    main()
