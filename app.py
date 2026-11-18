#!/usr/bin/env python3
"""Mess Cut Request Generator - Local Application Server.

A lightweight, robust local web server providing:
- Full responsive UI with Live A4 Preview
- Python ReportLab PDF Generation with minimal colors and executive typography
- Local JSON storage persistence
- Runs on Python standard library http.server (zero framework dependencies)
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import threading
import time
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from date_rules import (
    FIXED_RECIPIENT,
    get_valid_end_date_options,
    validate_complete_application,
    validate_date_range,
)
from pdf_generator import generate_mess_cut_pdf_buffer
from storage import (
    clear_all_data,
    load_request_draft,
    load_student_data,
    save_request_draft,
    save_student_data,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = BASE_DIR if os.path.exists(os.path.join(BASE_DIR, "index.html")) else os.path.join(BASE_DIR, "static")


class MessCutRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving static UI and REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format: str, *args):
        # Clean minimalist server logging
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {self.command} {self.path} - {args[1]}\n")

    def send_json(self, data: dict | list, status: int = HTTPStatus.OK):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/student":
            self.send_json(load_student_data())
            return
        elif path == "/api/draft":
            self.send_json(load_request_draft())
            return
        elif path == "/" or path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = self.read_json_body()
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/student":
            saved = save_student_data(body)
            self.send_json({"success": saved, "student": load_student_data()})
            return

        elif path == "/api/draft":
            saved = save_request_draft(body)
            self.send_json({"success": saved})
            return

        elif path == "/api/clear":
            clear_all_data()
            self.send_json({"success": True})
            return

        elif path == "/api/validate":
            profile = body.get("profile", {})
            profile["recipientAddress"] = FIXED_RECIPIENT
            request = body.get("request", {})
            result = validate_complete_application(profile, request)
            self.send_json(result)
            return

        elif path == "/api/date-options":
            start_date = body.get("startDate", "")
            options = get_valid_end_date_options(start_date)
            self.send_json(options)
            return

        elif path == "/api/generate-pdf":
            profile = body.get("profile", {})
            profile["recipientAddress"] = FIXED_RECIPIENT
            request = body.get("request", {})

            try:
                buf, filename = generate_mess_cut_pdf_buffer(profile, request)
                pdf_bytes = buf.getvalue()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(pdf_bytes)
            except ValueError as e:
                self.send_json({"error": str(e)}, status=HTTPStatus.UNPROCESSABLE_ENTITY)
            except Exception as e:
                self.send_json({"error": f"Internal error: {str(e)}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def start_server(port: int = 8000, open_browser: bool = True):
    """Start local HTTP server and open browser."""
    address = ("", port)
    server = ThreadingHTTPServer(address, MessCutRequestHandler)
    url = f"http://localhost:{port}"

    print("=" * 64)
    print("  MESS CUT REQUEST GENERATOR")
    print("  Recipient: The Warden, MH 2 Hostel, RIT Kottayam.")
    print("  Minimalist & Professional Academic Letter Suite")
    print("=" * 64)
    print(f"  Server URL:    {url}")
    print(f"  Local Dir:     {BASE_DIR}")
    print(f"  PDF Engine:    ReportLab (Monochrome / Minimal Color A4)")
    print("  Press Ctrl+C to terminate.")
    print("=" * 64)

    if open_browser:
        def _open():
            time.sleep(0.7)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mess Cut Request Generator")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    args = parser.parse_args()

    start_server(port=args.port, open_browser=not args.no_browser)
