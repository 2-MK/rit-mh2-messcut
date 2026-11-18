from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_generator import generate_mess_cut_pdf_buffer
from date_rules import validate_complete_application

FIXED_RECIPIENT = "The Warden,\nMH 2 Hostel,\nRIT Kottayam."


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function handler for /api/generate-pdf."""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except Exception:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode("utf-8"))
            return

        profile = body.get("profile", {})
        profile["recipientAddress"] = FIXED_RECIPIENT
        request = body.get("request", {})

        eval_result = validate_complete_application(profile, request)
        if not eval_result["is_ready_for_export"]:
            self.send_response(422)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "; ".join(eval_result["missing_fields"])}).encode("utf-8"))
            return

        try:
            buf, filename = generate_mess_cut_pdf_buffer(profile, request)
            pdf_bytes = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(pdf_bytes)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(pdf_bytes)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({
                "service": "RIT MH 2 Hostel Mess Cut PDF API",
                "status": "online",
                "recipient": FIXED_RECIPIENT
            }).encode("utf-8")
        )
