import { formatDDMMYYYY, getTodayDDMMYYYY, validateCompleteApplication } from './dateValidation.js';

function escapeHTML(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function buildLetterData(profile, request, now = new Date()) {
  const validation = validateCompleteApplication(profile, request);
  const currentDate = getTodayDDMMYYYY(now);

  const name = (profile.name || '').trim();
  const admissionNumber = (profile.admissionNumber || '').trim();
  const semester = (profile.semester || '').trim();
  const branch = (profile.branch || '').trim();
  const reason = (request.reason || '').trim();

  const startDisplay = formatDDMMYYYY(request.startDate || '');
  const endDisplay = formatDDMMYYYY(request.endDate || '');
  const totalDays = validation.dateValidation.isValid
    ? validation.dateValidation.totalDays
    : null;

  const displayName = name || '[Student Name]';
  const displayAdmission = admissionNumber || '[Admission Number]';
  const displaySemester = semester || '[Semester]';
  const displayBranch = branch || '[Branch]';
  const displayReason = reason || '[Reason for mess cut]';
  const displayStart = startDisplay || '[Start Date]';
  const displayEnd = endDisplay || '[End Date]';
  const displayDays = totalDays !== null ? `${totalDays} Days` : '[Total Days]';

  const subject = `Sub: Request for Mess Cut from ${displayStart} to ${displayEnd} (${displayDays}) - reg.`;

  const openingParagraph =
    `I am a resident of MH 2 Hostel, currently studying in ${displaySemester}, ${displayBranch}. ` +
    `I respectfully request you to kindly grant me a mess cut for a period of ${displayDays}, ` +
    `commencing from ${displayStart} to ${displayEnd} (both days inclusive), as ${displayReason}.`;

  const declarationParagraph =
    `I hereby declare that I will not be consuming food or availing of hostel mess facilities during ` +
    `the aforementioned period. I kindly request you to approve my application and make the eligible ` +
    `deduction in my monthly mess dues as per hostel regulations.`;

  return {
    isReadyForExport: validation.isReadyForExport,
    missingFields: validation.missingFields,
    dateValidation: validation.dateValidation,
    currentDate,
    name: displayName,
    admissionNumber: displayAdmission,
    semester: displaySemester,
    branch: displayBranch,
    reason: displayReason,
    startDisplay: displayStart,
    endDisplay: displayEnd,
    totalDaysText: displayDays,
    subject,
    openingParagraph,
    declarationParagraph,
    hasMissingName: !name,
    hasMissingAdmission: !admissionNumber,
    hasMissingSemester: !semester,
    hasMissingBranch: !branch,
    hasMissingReason: !reason,
  };
}

export function renderLetterPreview(container, letter) {
  let invalidBannerHTML = '';
  if (!letter.isReadyForExport) {
    const issues = [];
    if (letter.missingFields.length > 0) {
      issues.push(`Missing: ${letter.missingFields.join(', ')}.`);
    }
    if (!letter.dateValidation.isValid) {
      issues.push(`Date: ${letter.dateValidation.message}`);
    }
    invalidBannerHTML = `
      <div class="letter-invalid-note" role="note">
        <strong>Application Incomplete:</strong> ${escapeHTML(issues.join(' '))}
      </div>
    `;
  }

  container.innerHTML = `
    <!-- Formal Institutional Letterhead -->
    <div class="formal-header">
      <h3 class="inst-title">RAJIV GANDHI INSTITUTE OF TECHNOLOGY, KOTTAYAM</h3>
      <h4 class="inst-subtitle">MEN'S HOSTEL 2 (MH 2)</h4>
      <h4 class="inst-doc-name">APPLICATION FOR MESS CUT</h4>
      <div class="inst-double-rule"></div>
    </div>

    <!-- Date & Place Row -->
    <div class="formal-meta-row">
      <span>Place: Kottayam</span>
      <span>Date: ${escapeHTML(letter.currentDate)}</span>
    </div>

    <!-- Formal From Block -->
    <div class="formal-address-block">
      <div class="addr-label">From:</div>
      <div class="addr-content">
        <div class="addr-name">${escapeHTML(letter.name)}</div>
        <div>Admission No.: ${escapeHTML(letter.admissionNumber)}</div>
        <div>Semester: ${escapeHTML(letter.semester)}, Branch: ${escapeHTML(letter.branch)}</div>
        <div>MH 2 Hostel, RIT Kottayam</div>
      </div>
    </div>

    <!-- Formal To Block -->
    <div class="formal-address-block">
      <div class="addr-label">To:</div>
      <div class="addr-content">
        <div>The Warden,</div>
        <div>MH 2 Hostel,</div>
        <div>RIT Kottayam.</div>
      </div>
    </div>

    <!-- Salutation -->
    <p class="formal-salutation">Respected Sir,</p>

    <!-- Formal Subject Line -->
    <p class="formal-subject"><u>${escapeHTML(letter.subject)}</u></p>

    <!-- Opening Paragraph -->
    <p class="formal-paragraph">${escapeHTML(letter.openingParagraph)}</p>

    <!-- Formal Structured Summary Table -->
    <table class="formal-table" aria-label="Mess Cut Details">
      <tbody>
        <tr>
          <th scope="row">Student Name</th>
          <td>${escapeHTML(letter.name)}</td>
        </tr>
        <tr>
          <th scope="row">Admission Number</th>
          <td>${escapeHTML(letter.admissionNumber)}</td>
        </tr>
        <tr>
          <th scope="row">Semester &amp; Branch</th>
          <td>${escapeHTML(letter.semester)}, ${escapeHTML(letter.branch)}</td>
        </tr>
        <tr>
          <th scope="row">Mess Cut Duration</th>
          <td><strong>${escapeHTML(letter.totalDaysText)} (Inclusive)</strong></td>
        </tr>
        <tr>
          <th scope="row">Inclusive Dates</th>
          <td>${escapeHTML(letter.startDisplay)} to ${escapeHTML(letter.endDisplay)}</td>
        </tr>
        <tr>
          <th scope="row">Reason for Absence</th>
          <td>${escapeHTML(letter.reason)}</td>
        </tr>
      </tbody>
    </table>

    <!-- Declaration Paragraph -->
    <p class="formal-paragraph">${escapeHTML(letter.declarationParagraph)}</p>

    <!-- Sign-off Block (Bottom Left) -->
    <div class="formal-signoff-block">
      <p class="signoff-salutation">Yours faithfully,</p>
      <div class="formal-signature-gap"></div>
      <p class="student-name"><strong>${escapeHTML(letter.name)}</strong></p>
      <p class="student-meta">Adm No: ${escapeHTML(letter.admissionNumber)}</p>
      <p class="student-meta">${escapeHTML(letter.semester)}, ${escapeHTML(letter.branch)}</p>
    </div>

    ${invalidBannerHTML}
  `;
}
