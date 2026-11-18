"""Comprehensive automated test suite for Mess Cut Request Generator."""

import io
import unittest
from datetime import date
from date_rules import (
    format_dd_mm_yyyy,
    get_days_in_month,
    get_valid_end_date_options,
    parse_iso_date,
    validate_complete_application,
    validate_date_range,
)
from pdf_generator import generate_mess_cut_pdf_buffer, build_pdf_filename


class TestDateRules(unittest.TestCase):
    def test_days_in_month(self):
        self.assertEqual(get_days_in_month(2026, 1), 31)
        self.assertEqual(get_days_in_month(2026, 2), 28)
        self.assertEqual(get_days_in_month(2024, 2), 29)  # Leap year
        self.assertEqual(get_days_in_month(2026, 4), 30)

    def test_valid_same_month_7_days(self):
        res = validate_date_range("2026-12-01", "2026-12-07")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["total_days"], 7)
        self.assertEqual(res["code"], "VALID")

    def test_valid_same_month_14_days(self):
        res = validate_date_range("2026-12-01", "2026-12-14")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["total_days"], 14)

    def test_valid_same_month_21_days(self):
        res = validate_date_range("2026-12-01", "2026-12-21")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["total_days"], 21)

    def test_valid_same_month_28_days(self):
        res = validate_date_range("2026-12-01", "2026-12-28")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["total_days"], 28)

    def test_cross_month_forbidden(self):
        res = validate_date_range("2026-11-10", "2026-12-08")
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["code"], "CROSS_MONTH_FORBIDDEN")

    def test_not_multiple_of_7(self):
        res = validate_date_range("2026-12-01", "2026-12-10")  # 10 days
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["code"], "NOT_MULTIPLE_OF_7")
        self.assertEqual(res["total_days"], 10)

    def test_end_before_start(self):
        res = validate_date_range("2026-12-10", "2026-12-05")
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["code"], "END_BEFORE_START")

    def test_insufficient_days_remaining(self):
        # Nov has 30 days. Starting Nov 25 leaves only 6 days (Nov 25..30)
        res = validate_date_range("2026-11-25", "2026-11-30")
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["code"], "INSUFFICIENT_MONTH_DAYS")

    def test_valid_end_date_suggestions(self):
        options = get_valid_end_date_options("2026-12-01")
        self.assertTrue(options["can_accommodate"])
        self.assertEqual(len(options["suggestions"]), 4)  # 7, 14, 21, 28
        self.assertEqual(options["suggestions"][0]["days"], 7)
        self.assertEqual(options["suggestions"][0]["iso"], "2026-12-07")
        self.assertEqual(options["suggestions"][3]["days"], 28)
        self.assertEqual(options["suggestions"][3]["iso"], "2026-12-28")


class TestApplicationValidation(unittest.TestCase):
    def test_complete_valid_application(self):
        profile = {
            "recipientAddress": "The Mess Secretary\nMen's Hostel",
            "name": "Ajay Nath",
            "admissionNumber": "24CS042",
            "semester": "S5",
            "branch": "Computer Science & Engineering"
        }
        request = {
            "reason": "Visiting home",
            "startDate": "2026-12-01",
            "endDate": "2026-12-14"
        }
        eval_result = validate_complete_application(profile, request)
        self.assertTrue(eval_result["is_ready_for_export"])
        self.assertEqual(len(eval_result["missing_fields"]), 0)

    def test_missing_fields_blocks_export(self):
        profile = {
            "name": "",
            "admissionNumber": "24CS042",
            "semester": "S5",
            "branch": "Computer Science & Engineering"
        }
        request = {
            "reason": "",
            "startDate": "2026-12-01",
            "endDate": "2026-12-14"
        }
        eval_result = validate_complete_application(profile, request)
        self.assertFalse(eval_result["is_ready_for_export"])
        self.assertIn("Student Name", eval_result["missing_fields"])
        self.assertIn("Reason for Mess Cut", eval_result["missing_fields"])

    def test_fixed_recipient_default(self):
        profile = {
            "name": "Ajay Nath",
            "admissionNumber": "24CS042",
            "semester": "S5",
            "branch": "Computer Science & Engineering"
        }
        request = {
            "reason": "Visiting home",
            "startDate": "2026-12-01",
            "endDate": "2026-12-14"
        }
        eval_result = validate_complete_application(profile, request)
        self.assertTrue(eval_result["is_ready_for_export"])

    def test_pdf_buffer_generation(self):
        profile = {
            "recipientAddress": "The Warden,\nMH 2 Hostel,\nRIT Kottayam.",
            "name": "Ajay Nath",
            "admissionNumber": "24CS042",
            "semester": "S5",
            "branch": "Computer Science & Engineering"
        }
        request = {
            "reason": "Family function and semester break.",
            "startDate": "2026-12-01",
            "endDate": "2026-12-14"
        }
        buf, filename = generate_mess_cut_pdf_buffer(profile, request)
        pdf_bytes = buf.getvalue()
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertEqual(filename, "Ajay_Nath_01-12-2026-14-12-2026.pdf")
        self.assertNotIn(b"FOR HOSTEL OFFICE USE ONLY", pdf_bytes)
        self.assertNotIn(b"Thanking you", pdf_bytes)
        self.assertIn(b"APPLICATION FOR MESS CUT", pdf_bytes)
        self.assertIn(b"The Warden", pdf_bytes)
        self.assertIn(b"Yours faithfully", pdf_bytes)

    def test_invalid_request_raises(self):
        profile = {"name": ""}
        request = {"startDate": "2026-12-01", "endDate": "2026-12-05"}
        with self.assertRaises(ValueError):
            generate_mess_cut_pdf_buffer(profile, request)


if __name__ == "__main__":
    unittest.main()
