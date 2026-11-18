#!/usr/bin/env python3
"""Desktop GUI for Mess Cut Request Generator using Tkinter.

Provides a clean, minimal desktop interface with full validation,
fixed recipient addressing, and direct ReportLab PDF export.
"""

from __future__ import annotations
import os
import sys
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk
from tkinter.filedialog import asksaveasfilename

from date_rules import (
    FIXED_RECIPIENT,
    format_dd_mm_yyyy,
    get_today_dd_mm_yyyy,
    parse_iso_date,
    validate_complete_application,
)
from pdf_generator import generate_mess_cut_pdf_buffer
from storage import (
    load_request_draft,
    load_student_data,
    save_request_draft,
    save_student_data,
)


class MessCutGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mess Cut Request Generator")
        self.geometry("980x740")
        self.minsize(860, 640)

        # Minimalist Slate Palette
        self.COLOR_BG = "#f8fafc"
        self.COLOR_SURFACE = "#ffffff"
        self.COLOR_TEXT = "#0f172a"
        self.COLOR_MUTED = "#64748b"
        self.COLOR_BORDER = "#cbd5e1"
        self.COLOR_ACCENT = "#0f172a"

        self.configure(bg=self.COLOR_BG)
        self.student = load_student_data()
        self.draft = load_request_draft()

        self._setup_styles()
        self._build_ui()
        self._load_saved_data()
        self._update_validation_and_preview()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.COLOR_BG)
        style.configure("Surface.TFrame", background=self.COLOR_SURFACE)
        style.configure("TLabel", background=self.COLOR_BG, foreground=self.COLOR_TEXT, font=("Segoe UI", 10))
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Muted.TLabel", foreground=self.COLOR_MUTED, font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        style.configure("Primary.TButton", background=self.COLOR_ACCENT, foreground="#ffffff", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#1e293b")])

    def _build_ui(self):
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Left Column: Inputs
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # Fixed Recipient Banner
        recip_frame = tk.Frame(left_frame, bg="#f1f5f9", relief="solid", bd=1, padx=10, pady=8)
        recip_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(recip_frame, text="RECIPIENT (FIXED)", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(recip_frame, text="The Warden, MH 2 Hostel, RIT Kottayam.", bg="#f1f5f9", fg="#0f172a", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        # Student Details Group
        group1 = ttk.LabelFrame(left_frame, text=" Student Details ", padding=10)
        group1.pack(fill=tk.X, pady=6)

        ttk.Label(group1, text="Student Name:").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_name = ttk.Entry(group1)
        self.ent_name.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(group1, text="Admission Number:").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_adm = ttk.Entry(group1)
        self.ent_adm.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(group1, text="Semester:").grid(row=2, column=0, sticky="w", pady=4)
        self.ent_sem = ttk.Entry(group1)
        self.ent_sem.grid(row=2, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(group1, text="Branch:").grid(row=3, column=0, sticky="w", pady=4)
        self.ent_branch = ttk.Entry(group1)
        self.ent_branch.grid(row=3, column=1, sticky="ew", padx=6, pady=4)
        group1.columnconfigure(1, weight=1)

        # Request Details Group
        group2 = ttk.LabelFrame(left_frame, text=" Mess Cut Details ", padding=10)
        group2.pack(fill=tk.X, pady=6)

        ttk.Label(group2, text="Reason:").grid(row=0, column=0, sticky="nw", pady=4)
        self.txt_reason = tk.Text(group2, height=2, width=30, font=("Segoe UI", 9))
        self.txt_reason.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(group2, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_start = ttk.Entry(group2)
        self.ent_start.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        self.ent_start.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Label(group2, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", pady=4)
        self.ent_end = ttk.Entry(group2)
        self.ent_end.grid(row=2, column=1, sticky="ew", padx=6, pady=4)

        # Duration Quick-Select Buttons
        dur_frame = ttk.Frame(group2)
        dur_frame.grid(row=3, column=0, columnspan=2, pady=6)
        ttk.Label(dur_frame, text="Set Duration:").pack(side=tk.LEFT, padx=4)
        for days in [7, 14, 21, 28]:
            btn = ttk.Button(dur_frame, text=f"{days} Days", command=lambda d=days: self._set_days(d))
            btn.pack(side=tk.LEFT, padx=3)

        group2.columnconfigure(1, weight=1)

        # Validation feedback box
        self.val_box = tk.Label(left_frame, text="", bg="#f1f5f9", fg="#0f172a", relief="solid", bd=1, padx=8, pady=6, wraplength=380, justify="left", font=("Segoe UI", 9))
        self.val_box.pack(fill=tk.X, pady=8)

        # Action Buttons
        act_frame = ttk.Frame(left_frame)
        act_frame.pack(fill=tk.X, pady=8)

        self.btn_save_pdf = tk.Button(act_frame, text="Download PDF (A4)", bg="#0f172a", fg="#ffffff", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=8, command=self._export_pdf)
        self.btn_save_pdf.pack(fill=tk.X)

        # Wire live updates
        for entry in [self.ent_name, self.ent_adm, self.ent_sem, self.ent_branch, self.ent_start, self.ent_end]:
            entry.bind("<KeyRelease>", lambda e: self._on_field_change())
        self.txt_reason.bind("<KeyRelease>", lambda e: self._on_field_change())

        # Right Column: Live A4 Textual Preview
        right_frame = ttk.LabelFrame(main_paned, text=" Live Formal Letter Preview (Minimalist Ink) ", padding=10)
        main_paned.add(right_frame, weight=2)

        self.preview_text = tk.Text(right_frame, bg="#ffffff", fg="#0f172a", font=("Times New Roman", 11), wrap="word", padx=20, pady=20, relief="solid", bd=1)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

    def _load_saved_data(self):
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, self.student.get("name", ""))
        self.ent_adm.delete(0, tk.END)
        self.ent_adm.insert(0, self.student.get("admissionNumber", ""))
        self.ent_sem.delete(0, tk.END)
        self.ent_sem.insert(0, self.student.get("semester", ""))
        self.ent_branch.delete(0, tk.END)
        self.ent_branch.insert(0, self.student.get("branch", ""))

        self.txt_reason.delete("1.0", tk.END)
        self.txt_reason.insert("1.0", self.draft.get("reason", ""))
        if self.draft.get("startDate"):
            self.ent_start.delete(0, tk.END)
            self.ent_start.insert(0, self.draft.get("startDate"))
        if self.draft.get("endDate"):
            self.ent_end.delete(0, tk.END)
            self.ent_end.insert(0, self.draft.get("endDate"))

    def _set_days(self, days: int):
        start_str = self.ent_start.get().strip()
        start = parse_iso_date(start_str)
        if start:
            end = start + timedelta(days=days - 1)
            self.ent_end.delete(0, tk.END)
            self.ent_end.insert(0, end.strftime("%Y-%m-%d"))
            self._on_field_change()

    def _get_current_data(self):
        profile = {
            "name": self.ent_name.get().strip(),
            "admissionNumber": self.ent_adm.get().strip(),
            "semester": self.ent_sem.get().strip(),
            "branch": self.ent_branch.get().strip(),
            "recipientAddress": FIXED_RECIPIENT
        }
        request = {
            "reason": self.txt_reason.get("1.0", tk.END).strip(),
            "startDate": self.ent_start.get().strip(),
            "endDate": self.ent_end.get().strip()
        }
        return profile, request

    def _on_field_change(self):
        profile, request = self._get_current_data()
        save_student_data(profile)
        save_request_draft(request)
        self._update_validation_and_preview()

    def _update_validation_and_preview(self):
        profile, request = self._get_current_data()
        eval_result = validate_complete_application(profile, request)
        date_val = eval_result["date_validation"]

        if eval_result["is_ready_for_export"]:
            self.val_box.config(
                text=f"✓ VALID: {date_val['message']} ({date_val['total_days']} Days)",
                bg="#f0fdf4", fg="#166534"
            )
            self.btn_save_pdf.config(state="normal")
        else:
            issues = []
            if eval_result["missing_fields"]:
                issues.append("Missing: " + ", ".join(eval_result["missing_fields"]))
            if not date_val["is_valid"]:
                issues.append(date_val["message"])
            self.val_box.config(
                text="⚠ " + (" | ".join(issues) if issues else "Incomplete request"),
                bg="#fef2f2", fg="#991b1b"
            )
            self.btn_save_pdf.config(state="disabled")

        name = profile["name"] or "[Student Name]"
        adm = profile["admissionNumber"] or "[Admission Number]"
        sem = profile["semester"] or "[Semester]"
        branch = profile["branch"] or "[Branch]"
        reason = request["reason"] or "[Reason for mess cut]"
        s_disp = format_dd_mm_yyyy(request["startDate"]) or "[Start Date]"
        e_disp = format_dd_mm_yyyy(request["endDate"]) or "[End Date]"
        days_disp = f"{date_val['total_days']} Days" if date_val['is_valid'] else "[Total Days]"

        preview = f"""================================================================================
             RAJIV GANDHI INSTITUTE OF TECHNOLOGY, KOTTAYAM
                        MEN'S HOSTEL 2 (MH 2)
                      APPLICATION FOR MESS CUT
================================================================================
Place: Kottayam                                                 Date: {get_today_dd_mm_yyyy()}

From:
    {name}
    Admission No.: {adm}
    Semester: {sem}, Branch: {branch}
    MH 2 Hostel, RIT Kottayam

To:
    The Warden,
    MH 2 Hostel,
    RIT Kottayam.

Respected Sir,

Sub: Request for Mess Cut from {s_disp} to {e_disp} ({days_disp}) - reg.
--------------------------------------------------------------------------------

I am a resident of MH 2 Hostel studying in {sem}, {branch}. I respectfully request you to kindly grant me a mess cut for a period of {days_disp}, commencing from {s_disp} to {e_disp} (both days inclusive), as {reason}.

SUMMARY OF DETAILS:
--------------------------------------------------------------------------------
Student Name        : {name}
Admission Number    : {adm}
Semester & Branch   : {sem}, {branch}
Mess Cut Duration   : {days_disp} (Inclusive)
Inclusive Dates     : {s_disp} to {e_disp}
Reason for Absence  : {reason}
--------------------------------------------------------------------------------

I hereby declare that I will not be consuming food or availing of hostel mess facilities during the aforementioned period. I kindly request you to approve my application and make the eligible deduction in my monthly mess dues as per hostel regulations.

Yours faithfully,

(Signature)
{name}
Adm No: {adm}
{sem}, {branch}
================================================================================
"""
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", preview)

    def _export_pdf(self):
        profile, request = self._get_current_data()
        eval_result = validate_complete_application(profile, request)
        if not eval_result["is_ready_for_export"]:
            messagebox.showerror("Export Blocked", "Please resolve missing fields or date validation errors first.")
            return

        default_name = f"{profile['name']}_{format_dd_mm_yyyy(request['startDate'])}-{format_dd_mm_yyyy(request['endDate'])}.pdf"
        filepath = asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=default_name
        )
        if filepath:
            buf, _ = generate_mess_cut_pdf_buffer(profile, request)
            with open(filepath, "wb") as f:
                f.write(buf.getvalue())
            messagebox.showinfo("Export Successful", f"Saved PDF to:\n{filepath}")


if __name__ == "__main__":
    app = MessCutGUI()
    app.mainloop()
