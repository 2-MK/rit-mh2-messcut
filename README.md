# Mess Cut Request Generator

An institutional formal Mess Cut Request Generator engineered with a **minimalist, executive monochrome and slate design** for formal academic hostel submissions.

---

## ✦ Key Features

- **Fixed Recipient**: Pre-configured and permanently addressed to:
  ```text
  The Warden,
  MH 2 Hostel,
  RIT Kottayam.
  ```
- **Streamlined Student Details**: Direct entry for Student Name, Admission Number, Semester, and Branch with seamless local auto-saving.
- **Strict Mess Cut Date Engine**:
  - Durations must strictly be multiples of 7 days: **7, 14, 21, or 28 days** (both days inclusive).
  - Start and end dates must remain strictly within the **same calendar month** (no cross-month cuts).
  - Automatic check for at least 7 consecutive days remaining in the month.
  - Dynamic suggestion buttons (7d, 14d, 21d, 28d) with pre-calculated calendar dates.
- **Live A4 Letter Preview**:
  - Live proportional A4 preview sheet (210 × 297 mm) updated in real-time.
  - Executive institutional letter formatting (institutional title bar, auto-updating date, TO/FROM address block, bordered subject, formal body, structured summary table, signature space).
  - Zoom 100% / Fit Page toggle.
- **Minimalist Professional Output**:
  - Clean slate & monochrome typography (Times-Roman / Times-Bold in official PDF, deep slate `#0f172a` ink, crisp hairline borders).
  - No loud, neon colors: restrained, authoritative design suitable for submission to hostel wardens and college administrators.
- **Direct PDF Export**:
  - Powered by Python's **ReportLab** library for byte-accurate, selectable-text vector A4 PDFs.
  - Standardized institutional filename formatting: `Name_DD-MM-YYYY-DD-MM-YYYY.pdf` (e.g. `Ajay_Nath_01-12-2026-14-12-2026.pdf`).
  - Seamless client-side vector PDF fallback for offline operation.
- **Three Interfaces**:
  1. **Web App (`app.py`)**: Full responsive web UI with live A4 preview and auto-launch in browser.
  2. **Desktop GUI (`gui.py`)**: Standalone Tkinter desktop application for Windows.
  3. **CLI (`cli.py`)**: Command-line tool for terminal or automated batch script generation.

---

## ✦ Project Structure

```text
messcut_request/
├── app.py                # Local Python web server (zero-dependency, auto-opens browser)
├── gui.py                # Standalone Tkinter desktop GUI
├── cli.py                # Command-line interface for rapid PDF generation
├── pdf_generator.py      # ReportLab PDF engine (minimal-color executive A4 layout)
├── date_rules.py         # Pure Python date rules, calculations & validation logic
├── storage.py            # Local JSON profile and draft persistence layer
├── test_messcut.py       # Automated unit test suite (14 test cases)
├── data/
│   └── profiles.json     # Saved student profiles & drafts storage
├── output/               # Default output folder for generated PDFs
└── static/
    ├── index.html        # Semantic, accessible HTML app layout
    ├── css/
    │   └── styles.css    # Minimalist executive theme with minimal colors
    └── js/
        ├── main.js           # UI state & reactive event binding
        ├── dateValidation.js # Client-side date rule engine
        ├── letterGenerator.js# Live A4 letter preview builder
        ├── pdfExport.js      # ReportLab integration & client vector fallback
        └── storage.js        # LocalStorage and backend sync manager
```

---

## ✦ How to Run

### 1. Web Application (Recommended)
Starts the local server and automatically opens the application in your default web browser:
```bash
python app.py
```
*Optional flags:*
- `--port 8080`: Run on a custom port (default is `8000`).
- `--no-browser`: Do not automatically launch the browser window.

### 2. Standalone Desktop GUI
If you prefer running as a native Windows desktop app:
```bash
python gui.py
```

### 3. Command-Line Interface (CLI)
Generate an official PDF directly from the terminal:
```bash
python cli.py --name "Ajay Nath" \
              --admission "24CS042" \
              --semester "S5" \
              --branch "Computer Science & Engineering" \
              --reason "Visiting home for personal reasons" \
              --start "2026-12-01" \
              --days 14
```
*Output PDF will be saved to `output/Ajay_Nath_01-12-2026-14-12-2026.pdf`.*

### 4. Running the Test Suite
Run the 15 automated unit tests covering date math, calendar bounds, validation errors, and ReportLab PDF generation:
```bash
python test_messcut.py
```

---

## ✦ Minimalist Design Philosophy

The original website used multiple bright saturated colors (bright blue `#1e40af`, green `#166534`, red `#991b1b`). Per your request for a **professional output with minimal colors**, this Python clone employs:
- **Monochrome & Deep Slate Ink**: `#0f172a` for primary text and headings, providing sharp contrast without harsh pitch-black saturation.
- **Refined Neutral Surfaces**: `#f8fafc` canvas background and `#f1f5f9` subtle panels with fine `#e2e8f0` hairline borders.
- **Restrained Status Feedback**: Muted forest slate for valid selections and muted crimson slate for errors, keeping the user interface calm and executive.
- **Authoritative Letter Typography**: The formal letter and generated PDF use high-grade serif typography, crisp table rules, and institutional spacing appropriate for official college administrative records.
