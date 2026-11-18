import { formatDDMMYYYY, validateCompleteApplication } from './dateValidation.js?v=20261118_formal_v4';
import { buildLetterData } from './letterGenerator.js?v=20261118_formal_v4';

const A4_WIDTH = 595.28;
const A4_HEIGHT = 841.89;
const MARGIN_X = 56;
const CONTENT_WIDTH = A4_WIDTH - MARGIN_X * 2;

const TIMES_ROMAN_WIDTHS = {
  32: 250, 33: 333, 34: 408, 35: 500, 36: 500, 37: 833, 38: 778, 39: 180,
  40: 333, 41: 333, 42: 500, 43: 564, 44: 250, 45: 333, 46: 250, 47: 278,
  48: 500, 49: 500, 50: 500, 51: 500, 52: 500, 53: 500, 54: 500, 55: 500,
  56: 500, 57: 500, 58: 278, 59: 278, 60: 564, 61: 564, 62: 564, 63: 444,
  64: 921, 65: 722, 66: 667, 67: 667, 68: 722, 69: 611, 70: 556, 71: 722,
  72: 722, 73: 333, 74: 389, 75: 722, 76: 611, 77: 889, 78: 722, 79: 722,
  80: 556, 81: 722, 82: 667, 83: 556, 84: 611, 85: 722, 86: 722, 87: 944,
  88: 722, 89: 722, 90: 611, 91: 333, 92: 278, 93: 333, 94: 469, 95: 500,
  96: 333, 97: 444, 98: 500, 99: 444, 100: 500, 101: 444, 102: 333, 103: 500,
  104: 500, 105: 278, 106: 278, 107: 500, 108: 278, 109: 778, 110: 500, 111: 500,
  112: 500, 113: 500, 114: 333, 115: 389, 116: 278, 117: 500, 118: 500, 119: 722,
  120: 500, 121: 500, 122: 444, 123: 480, 124: 200, 125: 480, 126: 541,
};

const TIMES_BOLD_WIDTHS = {
  32: 250, 33: 333, 34: 555, 35: 500, 36: 500, 37: 1000, 38: 833, 39: 278,
  40: 333, 41: 333, 42: 500, 43: 570, 44: 250, 45: 333, 46: 250, 47: 278,
  48: 500, 49: 500, 50: 500, 51: 500, 52: 500, 53: 500, 54: 500, 55: 500,
  56: 500, 57: 500, 58: 333, 59: 333, 60: 570, 61: 570, 62: 570, 63: 500,
  64: 930, 65: 722, 66: 667, 67: 722, 68: 722, 69: 667, 70: 611, 71: 778,
  72: 778, 73: 389, 74: 500, 75: 778, 76: 667, 77: 944, 78: 722, 79: 778,
  80: 611, 81: 778, 82: 722, 83: 556, 84: 667, 85: 722, 86: 722, 87: 1000,
  88: 722, 89: 722, 90: 667, 91: 333, 92: 278, 93: 333, 94: 581, 95: 500,
  96: 333, 97: 500, 98: 556, 99: 444, 100: 556, 101: 444, 102: 333, 103: 500,
  104: 556, 105: 278, 106: 333, 107: 556, 108: 278, 109: 833, 110: 556, 111: 500,
  112: 556, 113: 556, 114: 444, 115: 389, 116: 333, 117: 556, 118: 500, 119: 722,
  120: 500, 121: 500, 122: 444, 123: 394, 124: 220, 125: 394, 126: 520,
};

function sanitizePdfText(text) {
  return String(text || '')
    .replace(/[\u2018\u2019\u201A]/g, "'")
    .replace(/[\u201C\u201D\u201E]/g, '"')
    .replace(/[\u2013\u2014\u2212]/g, '-')
    .replace(/\u2026/g, '...')
    .replace(/\u00A0/g, ' ')
    .replace(/[^\x20-\x7E]/g, ' ');
}

function escapePdfLiteral(text) {
  return sanitizePdfText(text)
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)');
}

function measureTextWidth(text, fontKey, fontSize) {
  const table = fontKey === 'F2' ? TIMES_BOLD_WIDTHS : TIMES_ROMAN_WIDTHS;
  const clean = sanitizePdfText(text);
  let units = 0;
  for (let i = 0; i < clean.length; i += 1) {
    const code = clean.charCodeAt(i);
    units += table[code] || 500;
  }
  return (units / 1000) * fontSize;
}

function wrapText(text, fontKey, fontSize, maxWidth) {
  const clean = sanitizePdfText(text).trim();
  if (!clean) {
    return [''];
  }
  const rawParagraphs = clean.split(/\r?\n/);
  const lines = [];

  for (const para of rawParagraphs) {
    const words = para.trim().split(/\s+/).filter(Boolean);
    if (words.length === 0) {
      lines.push('');
      continue;
    }
    let currentLine = words[0];
    for (let i = 1; i < words.length; i += 1) {
      const candidate = `${currentLine} ${words[i]}`;
      if (measureTextWidth(candidate, fontKey, fontSize) <= maxWidth) {
        currentLine = candidate;
      } else {
        lines.push(currentLine);
        currentLine = words[i];
      }
    }
    lines.push(currentLine);
  }
  return lines;
}

export function buildPdfFilename(studentName, startDateISO, endDateISO) {
  const sanitizedName = String(studentName || 'Student')
    .trim()
    .replace(/[\\/:*?"<>|]/g, '')
    .replace(/\s+/g, '_') || 'Student';
  const startDisplay = formatDDMMYYYY(startDateISO);
  const endDisplay = formatDDMMYYYY(endDateISO);
  return `${sanitizedName}_${startDisplay}-${endDisplay}.pdf`;
}

/**
 * Generates an authentic formal Indian academic letter PDF blob on client side.
 */
export function createMessCutPdfBlob(profile, request) {
  const validation = validateCompleteApplication(profile, request);
  if (!validation.isReadyForExport) {
    throw new Error('Cannot export PDF: required student fields or mess cut date rules are incomplete.');
  }

  const letter = buildLetterData(profile, request);
  const filename = buildPdfFilename(profile.name, request.startDate, request.endDate);
  const ops = [];

  const drawText = (text, x, y, fontKey = 'F1', size = 10.5, rgb = [0, 0, 0]) => {
    ops.push(
      `BT /${fontKey} ${size} Tf ${rgb[0].toFixed(3)} ${rgb[1].toFixed(3)} ${rgb[2].toFixed(3)} rg ` +
        `1 0 0 1 ${x.toFixed(2)} ${y.toFixed(2)} Tm (${escapePdfLiteral(text)}) Tj ET`
    );
  };

  const drawCenteredText = (text, centerY, fontKey = 'F2', size = 11, rgb = [0, 0, 0]) => {
    const w = measureTextWidth(text, fontKey, size);
    const startX = (A4_WIDTH - w) / 2;
    drawText(text, startX, centerY, fontKey, size, rgb);
  };

  const drawLine = (x1, y1, x2, y2, width = 0.5, rgb = [0.2, 0.2, 0.2]) => {
    ops.push(
      `${width.toFixed(2)} w ${rgb[0].toFixed(3)} ${rgb[1].toFixed(3)} ${rgb[2].toFixed(3)} RG ` +
        `${x1.toFixed(2)} ${y1.toFixed(2)} m ${x2.toFixed(2)} ${y2.toFixed(2)} l S`
    );
  };

  const fillRect = (x, y, w, h, rgb) => {
    ops.push(
      `${rgb[0].toFixed(3)} ${rgb[1].toFixed(3)} ${rgb[2].toFixed(3)} rg ` +
        `${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re f`
    );
  };

  const strokeRect = (x, y, w, h, width = 0.5, rgb = [0.6, 0.6, 0.6]) => {
    ops.push(
      `${width.toFixed(2)} w ${rgb[0].toFixed(3)} ${rgb[1].toFixed(3)} ${rgb[2].toFixed(3)} RG ` +
        `${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re S`
    );
  };

  let y = A4_HEIGHT - 48;

  // 1. Formal Institutional Letterhead (Centered)
  drawCenteredText('RAJIV GANDHI INSTITUTE OF TECHNOLOGY, KOTTAYAM', y, 'F2', 12, [0, 0, 0]);
  y -= 15;
  drawCenteredText("MEN'S HOSTEL 2 (MH 2)", y, 'F2', 10.5, [0.2, 0.2, 0.2]);
  y -= 14;
  drawCenteredText('APPLICATION FOR MESS CUT', y, 'F2', 11, [0, 0, 0]);
  y -= 10;

  // Double Divider Line
  drawLine(MARGIN_X, y, A4_WIDTH - MARGIN_X, y, 1.0, [0.25, 0.25, 0.25]);
  y -= 2;
  drawLine(MARGIN_X, y, A4_WIDTH - MARGIN_X, y, 0.4, [0.25, 0.25, 0.25]);
  y -= 18;

  // 2. Place & Date Row
  drawText('Place: Kottayam', MARGIN_X, y, 'F1', 10.5);
  const dateStr = `Date: ${letter.currentDate}`;
  const dateW = measureTextWidth(dateStr, 'F1', 10.5);
  drawText(dateStr, A4_WIDTH - MARGIN_X - dateW, y, 'F1', 10.5);
  y -= 20;

  // 3. From Block
  drawText('From:', MARGIN_X, y, 'F2', 10.5);
  y -= 14;
  drawText(letter.name, MARGIN_X + 16, y, 'F2', 10.5);
  y -= 14;
  const fromLines = [
    `Admission No.: ${letter.admissionNumber}`,
    `Semester: ${letter.semester}, Branch: ${letter.branch}`,
    'MH 2 Hostel, RIT Kottayam',
  ];
  for (const fline of fromLines) {
    drawText(fline, MARGIN_X + 16, y, 'F1', 10.5);
    y -= 14;
  }
  y -= 8;

  // 4. To Block
  drawText('To:', MARGIN_X, y, 'F2', 10.5);
  y -= 14;
  const toLines = [
    'The Warden,',
    'MH 2 Hostel,',
    'RIT Kottayam.',
  ];
  for (const tline of toLines) {
    drawText(tline, MARGIN_X + 16, y, 'F1', 10.5);
    y -= 14;
  }
  y -= 10;

  // 5. Salutation
  drawText('Respected Sir,', MARGIN_X, y, 'F1', 10.5);
  y -= 16;

  // 6. Subject Line (Bold, Underlined)
  drawText(letter.subject, MARGIN_X + 16, y, 'F2', 10.5);
  const subjW = measureTextWidth(letter.subject, 'F2', 10.5);
  drawLine(MARGIN_X + 16, y - 2, MARGIN_X + 16 + subjW, y - 2, 0.5, [0, 0, 0]);
  y -= 20;

  // 7. Opening Paragraph
  const openLines = wrapText(letter.openingParagraph, 'F1', 10.5, CONTENT_WIDTH);
  for (let i = 0; i < openLines.length; i += 1) {
    const lineX = i === 0 ? MARGIN_X + 18 : MARGIN_X;
    drawText(openLines[i], lineX, y, 'F1', 10.5);
    y -= 15;
  }
  y -= 8;

  // 8. Formal Summary Table
  const col1W = 150;
  const col2W = CONTENT_WIDTH - col1W;
  const tableData = [
    ['Student Name', letter.name],
    ['Admission Number', letter.admissionNumber],
    ['Semester & Branch', `${letter.semester}, ${letter.branch}`],
    ['Mess Cut Duration', `${letter.totalDaysText} (Inclusive)`],
    ['Inclusive Dates', `${letter.startDisplay} to ${letter.endDisplay}`],
    ['Reason for Absence', letter.reason],
  ];

  for (const [label, val] of tableData) {
    const wrappedVal = wrapText(val, 'F1', 9.5, col2W - 16);
    const rowH = Math.max(20, wrappedVal.length * 13 + 8);
    const rowBottom = y - rowH;

    // Light zebra fill
    fillRect(MARGIN_X, rowBottom, col1W, rowH, [0.975, 0.975, 0.975]);
    // Cell borders
    strokeRect(MARGIN_X, rowBottom, col1W, rowH, 0.5, [0.65, 0.65, 0.65]);
    strokeRect(MARGIN_X + col1W, rowBottom, col2W, rowH, 0.5, [0.65, 0.65, 0.65]);

    drawText(label, MARGIN_X + 8, y - 13, 'F2', 9.5);
    let valY = y - 13;
    for (const vline of wrappedVal) {
      drawText(vline, MARGIN_X + col1W + 8, valY, 'F1', 9.5);
      valY -= 13;
    }

    y = rowBottom;
  }

  y -= 16;

  // 9. Declaration Paragraph
  const declLines = wrapText(letter.declarationParagraph, 'F1', 10.5, CONTENT_WIDTH);
  for (let i = 0; i < declLines.length; i += 1) {
    const lineX = i === 0 ? MARGIN_X + 18 : MARGIN_X;
    drawText(declLines[i], lineX, y, 'F1', 10.5);
    y -= 15;
  }
  y -= 12;

  // 10. Sign-off Block (Bottom Left)
  const signoffX = MARGIN_X;
  drawText('Yours faithfully,', signoffX, y, 'F1', 10.5);
  y -= 38;

  drawText(letter.name, signoffX, y, 'F2', 10.5);
  y -= 14;
  drawText(`Adm No: ${letter.admissionNumber}`, signoffX, y, 'F1', 10);
  y -= 14;
  drawText(`${letter.semester}, ${letter.branch}`, signoffX, y, 'F1', 10);

  const streamContent = ops.join('\n');
  const encoder = new TextEncoder();
  const streamBytes = encoder.encode(streamContent);

  const objects = [
    '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
    '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
    `3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${A4_WIDTH.toFixed(2)} ${A4_HEIGHT.toFixed(2)}] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>\nendobj\n`,
    '4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>\nendobj\n',
    '5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>\nendobj\n',
    `6 0 obj\n<< /Length ${streamBytes.length} >>\nstream\n${streamContent}\nendstream\nendobj\n`,
  ];

  const header = '%PDF-1.4\n';
  const chunks = [encoder.encode(header)];
  let currentOffset = chunks[0].length;
  const offsets = [0];

  for (const objStr of objects) {
    offsets.push(currentOffset);
    const bytes = encoder.encode(objStr);
    chunks.push(bytes);
    currentOffset += bytes.length;
  }

  const xrefOffset = currentOffset;
  let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 1; i <= objects.length; i += 1) {
    xref += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  }
  const trailer =
    `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\n` +
    `startxref\n${xrefOffset}\n%%EOF\n`;

  chunks.push(encoder.encode(xref + trailer));

  const blob = new Blob(chunks, { type: 'application/pdf' });
  return { blob, filename };
}

/**
 * Triggers PDF download. Attempts Python server ReportLab generation first,
 * falling back seamlessly to client-side vector generation.
 */
export async function downloadMessCutPdf(profile, request) {
  const filename = buildPdfFilename(profile.name, request.startDate, request.endDate);

  try {
    const res = await fetch('/api/generate-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile, request })
    });
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      setTimeout(() => URL.revokeObjectURL(url), 1500);
      return filename;
    }
  } catch {
    // Fall back to client generation
  }

  const { blob } = createMessCutPdfBlob(profile, request);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(url), 1500);
  return filename;
}
