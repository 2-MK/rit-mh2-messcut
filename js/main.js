import {
  clearAllStoredData,
  FIXED_RECIPIENT,
  loadRequestDraft,
  loadStudentData,
  saveRequestDraft,
  saveStudentData,
  syncFromBackendIfEmpty,
} from './storage.js?v=20261118_formal_v4';
import {
  getTodayDDMMYYYY,
  getValidEndDateOptions,
  validateCompleteApplication,
} from './dateValidation.js?v=20261118_formal_v4';
import { buildLetterData, renderLetterPreview } from './letterGenerator.js?v=20261118_formal_v4';
import { buildPdfFilename, downloadMessCutPdf } from './pdfExport.js?v=20261118_formal_v4';

const CHECK_ICON_SVG = `
  <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
  </svg>
`;

const ERROR_ICON_SVG = `
  <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
  </svg>
`;

const INFO_ICON_SVG = `
  <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd" />
  </svg>
`;

const elements = {
  btnClearAll: document.getElementById('btn-clear-all'),
  saveIndicator: document.getElementById('save-indicator'),

  inputName: document.getElementById('input-name'),
  inputAdmission: document.getElementById('input-admission'),
  inputSemester: document.getElementById('input-semester'),
  inputBranch: document.getElementById('input-branch'),

  inputReason: document.getElementById('input-reason'),
  inputStartDate: document.getElementById('input-start-date'),
  inputEndDate: document.getElementById('input-end-date'),

  suggestionsContainer: document.getElementById('suggestions-container'),
  suggestedEndDates: document.getElementById('suggested-end-dates'),
  monthCapacityNote: document.getElementById('month-capacity-note'),

  validationFeedback: document.getElementById('validation-feedback'),
  validationIcon: document.getElementById('validation-icon'),
  validationHeading: document.getElementById('validation-heading'),
  validationMessage: document.getElementById('validation-message'),
  calculatedDaysReadout: document.getElementById('calculated-days-readout'),

  btnDownloadPdf: document.getElementById('btn-download-pdf'),
  btnPrintLetter: document.getElementById('btn-print-letter'),
  btnMobileDownloadPdf: document.getElementById('btn-mobile-download-pdf'),
  btnMobilePrint: document.getElementById('btn-mobile-print'),
  filenamePreview: document.getElementById('filename-preview'),

  tabCompose: document.getElementById('tab-compose'),
  tabPreview: document.getElementById('tab-preview'),
  composerColumn: document.getElementById('composer-column'),
  previewSection: document.getElementById('preview-section'),
  btnToggleZoom: document.getElementById('btn-toggle-zoom'),

  previewValidityLabel: document.getElementById('preview-validity-label'),
  a4Stage: document.getElementById('a4-stage'),
  a4Viewport: document.getElementById('a4-viewport'),
  a4Paper: document.getElementById('a4-paper'),

  modalBackdrop: document.getElementById('modal-backdrop'),
  modalCancel: document.getElementById('modal-cancel'),
  modalConfirm: document.getElementById('modal-confirm'),
};

const state = {
  student: {
    recipientAddress: FIXED_RECIPIENT,
    name: '',
    admissionNumber: '',
    semester: '',
    branch: '',
  },
  requestDraft: {
    reason: '',
    startDate: '',
    endDate: '',
  },
  mobileActiveTab: 'compose',
  previewZoomActual: false,
};

let saveBadgeTimer = null;

function showSavedIndicator(text = 'Auto-saved') {
  elements.saveIndicator.textContent = text;
  elements.saveIndicator.classList.add('is-saved');
  if (saveBadgeTimer) {
    window.clearTimeout(saveBadgeTimer);
  }
  saveBadgeTimer = window.setTimeout(() => {
    elements.saveIndicator.classList.remove('is-saved');
    elements.saveIndicator.textContent = 'Ready';
  }, 1800);
}

function populateInputs() {
  elements.inputName.value = state.student.name;
  elements.inputAdmission.value = state.student.admissionNumber;
  elements.inputSemester.value = state.student.semester;
  elements.inputBranch.value = state.student.branch;

  elements.inputReason.value = state.requestDraft.reason;
  elements.inputStartDate.value = state.requestDraft.startDate;
  elements.inputEndDate.value = state.requestDraft.endDate;
}

function updateUIAndPreview() {
  const startOptions = getValidEndDateOptions(state.requestDraft.startDate);

  if (!startOptions.hasStart || !startOptions.canAccommodate) {
    elements.inputEndDate.disabled = true;
    elements.inputEndDate.removeAttribute('min');
    elements.inputEndDate.removeAttribute('max');
    elements.suggestionsContainer.hidden = true;
    elements.suggestedEndDates.innerHTML = '';
  } else {
    elements.inputEndDate.disabled = false;
    elements.inputEndDate.min = startOptions.minEndDateISO;
    elements.inputEndDate.max = startOptions.maxEndDateISO;

    elements.suggestionsContainer.hidden = false;
    elements.monthCapacityNote.textContent = `${startOptions.remainingDaysInMonth} days remaining in ${startOptions.monthLabel}`;
    elements.suggestedEndDates.innerHTML = '';

    for (const suggestion of startOptions.suggestions) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'suggestion-btn';
      if (state.requestDraft.endDate === suggestion.iso) {
        btn.classList.add('is-active');
      }
      btn.dataset.iso = suggestion.iso;
      btn.innerHTML = `
        <span class="suggestion-days">${suggestion.days} Days</span>
        <span class="suggestion-date">${suggestion.display}</span>
      `;
      btn.addEventListener('click', () => {
        state.requestDraft.endDate = suggestion.iso;
        elements.inputEndDate.value = suggestion.iso;
        saveRequestDraft(state.requestDraft);
        updateUIAndPreview();
      });
      elements.suggestedEndDates.appendChild(btn);
    }
  }

  const evaluation = validateCompleteApplication(state.student, state.requestDraft);
  const { dateValidation, missingFields, isReadyForExport } = evaluation;

  elements.validationFeedback.classList.remove(
    'validation-neutral',
    'validation-valid',
    'validation-error'
  );
  elements.inputStartDate.classList.remove('is-invalid');
  elements.inputEndDate.classList.remove('is-invalid');

  if (!state.requestDraft.startDate) {
    elements.validationFeedback.classList.add('validation-neutral');
    elements.validationIcon.innerHTML = INFO_ICON_SVG;
    elements.validationHeading.textContent = dateValidation.heading;
    elements.validationMessage.textContent = dateValidation.message;
    elements.calculatedDaysReadout.textContent = '';
  } else if (dateValidation.isValid) {
    elements.validationFeedback.classList.add('validation-valid');
    elements.validationIcon.innerHTML = CHECK_ICON_SVG;
    elements.validationHeading.textContent = dateValidation.heading;
    elements.validationMessage.textContent = dateValidation.message;
    elements.calculatedDaysReadout.textContent = `${dateValidation.totalDays} Days`;
  } else {
    elements.validationFeedback.classList.add('validation-error');
    elements.validationIcon.innerHTML = ERROR_ICON_SVG;
    elements.validationHeading.textContent = dateValidation.heading;
    elements.validationMessage.textContent = dateValidation.message;
    elements.calculatedDaysReadout.textContent =
      dateValidation.totalDays !== null ? `${dateValidation.totalDays} Days (Invalid)` : '';

    if (dateValidation.code === 'INSUFFICIENT_MONTH_DAYS' || dateValidation.code === 'INVALID_START') {
      elements.inputStartDate.classList.add('is-invalid');
    } else if (state.requestDraft.endDate) {
      elements.inputEndDate.classList.add('is-invalid');
    }
  }

  elements.btnDownloadPdf.disabled = !isReadyForExport;
  elements.btnDownloadPdf.setAttribute('aria-disabled', String(!isReadyForExport));
  elements.btnPrintLetter.disabled = !isReadyForExport;
  elements.btnPrintLetter.setAttribute('aria-disabled', String(!isReadyForExport));
  elements.btnMobileDownloadPdf.disabled = !isReadyForExport;
  elements.btnMobileDownloadPdf.setAttribute('aria-disabled', String(!isReadyForExport));
  elements.btnMobilePrint.disabled = !isReadyForExport;
  elements.btnMobilePrint.setAttribute('aria-disabled', String(!isReadyForExport));

  if (isReadyForExport) {
    const filename = buildPdfFilename(
      state.student.name,
      state.requestDraft.startDate,
      state.requestDraft.endDate
    );
    elements.filenamePreview.textContent = `Filename: ${filename}`;
  } else if (missingFields.length > 0 && dateValidation.isValid) {
    elements.filenamePreview.textContent = `Complete required fields to export: ${missingFields.join(', ')}`;
  } else {
    elements.filenamePreview.textContent =
      'Filename: Name_DD-MM-YYYY-DD-MM-YYYY.pdf (ready when all fields and dates are valid)';
  }

  elements.previewValidityLabel.classList.remove('is-valid', 'is-invalid');
  if (isReadyForExport) {
    elements.previewValidityLabel.textContent = 'Ready to Export';
    elements.previewValidityLabel.classList.add('is-valid');
  } else if (
    state.requestDraft.startDate &&
    !dateValidation.isValid &&
    dateValidation.code !== 'MISSING_END'
  ) {
    elements.previewValidityLabel.textContent = 'Invalid Date Selection';
    elements.previewValidityLabel.classList.add('is-invalid');
  } else {
    elements.previewValidityLabel.textContent = 'Incomplete';
  }

  const letterData = buildLetterData(state.student, state.requestDraft);
  renderLetterPreview(elements.a4Paper, letterData);
  scaleA4Preview();
}

function setMobileTab(tab) {
  state.mobileActiveTab = tab;
  const isCompose = tab === 'compose';

  elements.tabCompose.classList.toggle('is-active', isCompose);
  elements.tabCompose.setAttribute('aria-selected', String(isCompose));

  elements.tabPreview.classList.toggle('is-active', !isCompose);
  elements.tabPreview.setAttribute('aria-selected', String(!isCompose));

  elements.composerColumn.classList.toggle('is-mobile-hidden', !isCompose);
  elements.previewSection.classList.toggle('is-mobile-hidden', isCompose);

  if (!isCompose) {
    window.requestAnimationFrame(() => scaleA4Preview());
  }
}

function scaleA4Preview() {
  const baseWidth = 794;
  const baseHeight = Math.max(1123, elements.a4Paper.scrollHeight);
  const isMobileViewport = window.innerWidth <= 960;

  if (isMobileViewport && state.previewZoomActual) {
    elements.a4Stage.classList.add('is-zoomed');
    elements.a4Paper.style.transform = 'scale(1)';
    elements.a4Viewport.style.width = `${baseWidth}px`;
    elements.a4Viewport.style.height = `${baseHeight}px`;
    return;
  }

  elements.a4Stage.classList.remove('is-zoomed');
  const stageStyles = window.getComputedStyle(elements.a4Stage);
  const padLeft = parseFloat(stageStyles.paddingLeft) || 0;
  const padRight = parseFloat(stageStyles.paddingRight) || 0;
  const rawWidth = elements.a4Stage.clientWidth - padLeft - padRight;

  if (rawWidth <= 0) {
    return;
  }

  const availableWidth = Math.max(240, rawWidth);
  const scale = Math.min(1, availableWidth / baseWidth);

  elements.a4Paper.style.transform = `scale(${scale})`;
  elements.a4Viewport.style.width = `${Math.round(baseWidth * scale)}px`;
  elements.a4Viewport.style.height = `${Math.round(baseHeight * scale)}px`;
}

function handleStudentFieldChange() {
  state.student = {
    recipientAddress: FIXED_RECIPIENT,
    name: elements.inputName.value,
    admissionNumber: elements.inputAdmission.value,
    semester: elements.inputSemester.value,
    branch: elements.inputBranch.value,
  };

  saveStudentData(state.student);
  showSavedIndicator('Auto-saved');
  updateUIAndPreview();
}

function handleStartDateChange() {
  const newStart = elements.inputStartDate.value;
  state.requestDraft.startDate = newStart;

  const options = getValidEndDateOptions(newStart);
  if (!options.canAccommodate) {
    state.requestDraft.endDate = '';
    elements.inputEndDate.value = '';
  } else if (state.requestDraft.endDate) {
    const currentEnd = state.requestDraft.endDate;
    if (currentEnd < options.minEndDateISO || currentEnd > options.maxEndDateISO) {
      state.requestDraft.endDate = '';
      elements.inputEndDate.value = '';
    }
  }

  saveRequestDraft(state.requestDraft);
  updateUIAndPreview();
}

function handleEndDateChange() {
  state.requestDraft.endDate = elements.inputEndDate.value;
  saveRequestDraft(state.requestDraft);
  updateUIAndPreview();
}

function handleReasonChange() {
  state.requestDraft.reason = elements.inputReason.value;
  saveRequestDraft(state.requestDraft);
  updateUIAndPreview();
}

function openClearAllModal() {
  elements.modalBackdrop.hidden = false;
  elements.modalConfirm.focus();
}

function closeModal() {
  elements.modalBackdrop.hidden = true;
}

function bindEvents() {
  elements.btnClearAll.addEventListener('click', openClearAllModal);

  [
    elements.inputName,
    elements.inputAdmission,
    elements.inputSemester,
    elements.inputBranch,
  ].forEach((input) => {
    input.addEventListener('input', handleStudentFieldChange);
  });

  elements.inputReason.addEventListener('input', handleReasonChange);
  elements.inputStartDate.addEventListener('change', handleStartDateChange);
  elements.inputEndDate.addEventListener('change', handleEndDateChange);

  const triggerPdfDownload = async () => {
    const evaluation = validateCompleteApplication(state.student, state.requestDraft);
    if (!evaluation.isReadyForExport) {
      updateUIAndPreview();
      return;
    }
    try {
      elements.btnDownloadPdf.disabled = true;
      elements.btnMobileDownloadPdf.disabled = true;
      const filename = await downloadMessCutPdf(state.student, state.requestDraft);
      showSavedIndicator(`Downloaded ${filename}`);
    } catch (err) {
      elements.validationFeedback.classList.remove('validation-neutral', 'validation-valid');
      elements.validationFeedback.classList.add('validation-error');
      elements.validationIcon.innerHTML = ERROR_ICON_SVG;
      elements.validationHeading.textContent = 'Export Blocked';
      elements.validationMessage.textContent =
        err instanceof Error ? err.message : 'Unable to generate PDF.';
    } finally {
      elements.btnDownloadPdf.disabled = false;
      elements.btnMobileDownloadPdf.disabled = false;
    }
  };

  const triggerPrint = () => {
    const evaluation = validateCompleteApplication(state.student, state.requestDraft);
    if (!evaluation.isReadyForExport) {
      updateUIAndPreview();
      return;
    }
    window.print();
  };

  elements.btnDownloadPdf.addEventListener('click', triggerPdfDownload);
  elements.btnMobileDownloadPdf.addEventListener('click', triggerPdfDownload);
  elements.btnPrintLetter.addEventListener('click', triggerPrint);
  elements.btnMobilePrint.addEventListener('click', triggerPrint);

  elements.tabCompose.addEventListener('click', () => setMobileTab('compose'));
  elements.tabPreview.addEventListener('click', () => setMobileTab('preview'));
  elements.btnToggleZoom.addEventListener('click', () => {
    state.previewZoomActual = !state.previewZoomActual;
    elements.btnToggleZoom.classList.toggle('is-active', state.previewZoomActual);
    elements.btnToggleZoom.setAttribute('aria-pressed', String(state.previewZoomActual));
    elements.btnToggleZoom.textContent = state.previewZoomActual ? 'Fit Page' : 'Zoom 100%';
    scaleA4Preview();
  });

  elements.modalCancel.addEventListener('click', closeModal);
  elements.modalConfirm.addEventListener('click', () => {
    clearAllStoredData();
    state.student = {
      recipientAddress: FIXED_RECIPIENT,
      name: '',
      admissionNumber: '',
      semester: '',
      branch: '',
    };
    state.requestDraft = {
      reason: '',
      startDate: '',
      endDate: '',
    };
    populateInputs();
    updateUIAndPreview();
    elements.saveIndicator.textContent = 'Cleared';
    closeModal();
  });

  elements.modalBackdrop.addEventListener('click', (event) => {
    if (event.target === elements.modalBackdrop) {
      closeModal();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !elements.modalBackdrop.hidden) {
      closeModal();
    }
  });

  if (typeof ResizeObserver !== 'undefined') {
    const observer = new ResizeObserver(() => scaleA4Preview());
    observer.observe(elements.a4Stage);
  }
  window.addEventListener('resize', scaleA4Preview);
}

function setupAutoDateRefresh() {
  let lastKnownDate = getTodayDDMMYYYY();

  const checkDayChange = () => {
    const currentDate = getTodayDDMMYYYY();
    if (currentDate !== lastKnownDate) {
      lastKnownDate = currentDate;
      updateUIAndPreview();
    }
  };

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      checkDayChange();
    }
  });
  window.addEventListener('focus', checkDayChange);
  window.setInterval(checkDayChange, 60000);
}

async function init() {
  await syncFromBackendIfEmpty();
  state.student = loadStudentData();
  state.requestDraft = loadRequestDraft();
  populateInputs();
  bindEvents();
  setupAutoDateRefresh();
  updateUIAndPreview();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
