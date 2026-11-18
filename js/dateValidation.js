/**
 * Strict date parsing, inclusive duration calculation, and same-month validation.
 * Uses UTC operations to eliminate timezone and DST drift.
 */

const MS_PER_DAY = 86400000;

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export function getDaysInMonth(year, month) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

export function formatISODate(year, month, day) {
  const y = String(year).padStart(4, '0');
  const m = String(month).padStart(2, '0');
  const d = String(day).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function parseISODate(isoDate) {
  if (typeof isoDate !== 'string') {
    return null;
  }
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate.trim());
  if (!match) {
    return null;
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);

  if (month < 1 || month > 12) {
    return null;
  }
  const daysInMonth = getDaysInMonth(year, month);
  if (day < 1 || day > daysInMonth) {
    return null;
  }

  const dayIndex = Math.floor(Date.UTC(year, month - 1, day) / MS_PER_DAY);
  return {
    year,
    month,
    day,
    daysInMonth,
    dayIndex,
    iso: formatISODate(year, month, day)
  };
}

export function formatDDMMYYYY(isoDate) {
  const parsed = parseISODate(isoDate);
  if (!parsed) {
    return '';
  }
  const d = String(parsed.day).padStart(2, '0');
  const m = String(parsed.month).padStart(2, '0');
  const y = String(parsed.year).padStart(4, '0');
  return `${d}-${m}-${y}`;
}

export function getTodayDDMMYYYY(now = new Date()) {
  const d = String(now.getDate()).padStart(2, '0');
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const y = String(now.getFullYear()).padStart(4, '0');
  return `${d}-${m}-${y}`;
}

export function getMonthLabel(year, month) {
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

export function getValidEndDateOptions(startDateISO) {
  const start = parseISODate(startDateISO);
  if (!start) {
    return {
      hasStart: false,
      canAccommodate: false,
      remainingDaysInMonth: 0,
      daysInMonth: 0,
      monthLabel: '',
      latestValidStartISO: null,
      minEndDateISO: null,
      maxEndDateISO: null,
      suggestions: []
    };
  }

  const remainingDaysInMonth = start.daysInMonth - start.day + 1;
  const monthLabel = getMonthLabel(start.year, start.month);
  const latestValidStartDay = start.daysInMonth - 6;
  const latestValidStartISO = formatISODate(start.year, start.month, latestValidStartDay);

  if (remainingDaysInMonth < 7) {
    return {
      hasStart: true,
      canAccommodate: false,
      remainingDaysInMonth,
      daysInMonth: start.daysInMonth,
      monthLabel,
      latestValidStartISO,
      minEndDateISO: null,
      maxEndDateISO: null,
      suggestions: []
    };
  }

  const suggestions = [];
  for (let days = 7; days <= remainingDaysInMonth; days += 7) {
    const endDay = start.day + days - 1;
    const iso = formatISODate(start.year, start.month, endDay);
    suggestions.push({
      days,
      iso,
      display: formatDDMMYYYY(iso)
    });
  }

  return {
    hasStart: true,
    canAccommodate: true,
    remainingDaysInMonth,
    daysInMonth: start.daysInMonth,
    monthLabel,
    latestValidStartISO,
    minEndDateISO: suggestions[0].iso,
    maxEndDateISO: suggestions[suggestions.length - 1].iso,
    suggestions
  };
}

export function validateDateRange(startDateISO, endDateISO) {
  if (!startDateISO) {
    return {
      isValid: false,
      code: 'MISSING_START',
      heading: 'Select start and end dates',
      message: 'Choose a start date to view valid same-month end dates in multiples of 7 days.',
      totalDays: null,
      startDisplay: '',
      endDisplay: '',
      suggestions: []
    };
  }

  const start = parseISODate(startDateISO);
  if (!start) {
    return {
      isValid: false,
      code: 'INVALID_START',
      heading: 'Invalid start date',
      message: 'Please choose a valid start date from the calendar.',
      totalDays: null,
      startDisplay: '',
      endDisplay: '',
      suggestions: []
    };
  }

  const options = getValidEndDateOptions(start.iso);
  const startDisplay = formatDDMMYYYY(start.iso);
  const monthEndDisplay = formatDDMMYYYY(formatISODate(start.year, start.month, start.daysInMonth));

  if (!options.canAccommodate) {
    const latestValidDisplay = formatDDMMYYYY(options.latestValidStartISO);
    const nextMonthYear = start.month === 12 ? start.year + 1 : start.year;
    const nextMonthNum = start.month === 12 ? 1 : start.month + 1;
    const nextMonthStartDisplay = formatDDMMYYYY(formatISODate(nextMonthYear, nextMonthNum, 1));

    return {
      isValid: false,
      code: 'INSUFFICIENT_MONTH_DAYS',
      heading: 'Insufficient days remaining in month',
      message: `Starting ${startDisplay} leaves only ${options.remainingDaysInMonth} consecutive day${options.remainingDaysInMonth === 1 ? '' : 's'} in ${options.monthLabel} (ending ${monthEndDisplay}). At least 7 consecutive days within the same month are required. Select ${latestValidDisplay} or earlier, or start on ${nextMonthStartDisplay}.`,
      totalDays: null,
      startDisplay,
      endDisplay: '',
      suggestions: []
    };
  }

  if (!endDateISO) {
    return {
      isValid: false,
      code: 'MISSING_END',
      heading: 'Select a valid end date',
      message: `Choose one of the valid same-month end dates for ${options.monthLabel} (${options.suggestions.map((s) => `${s.days}d: ${s.display}`).join(', ')}).`,
      totalDays: null,
      startDisplay,
      endDisplay: '',
      suggestions: options.suggestions
    };
  }

  const end = parseISODate(endDateISO);
  if (!end) {
    return {
      isValid: false,
      code: 'INVALID_END',
      heading: 'Invalid end date',
      message: 'Please choose a valid end date from the calendar or suggested durations.',
      totalDays: null,
      startDisplay,
      endDisplay: '',
      suggestions: options.suggestions
    };
  }

  const endDisplay = formatDDMMYYYY(end.iso);

  if (end.dayIndex < start.dayIndex) {
    return {
      isValid: false,
      code: 'END_BEFORE_START',
      heading: 'End date precedes start date',
      message: `End date (${endDisplay}) cannot be earlier than start date (${startDisplay}).`,
      totalDays: null,
      startDisplay,
      endDisplay,
      suggestions: options.suggestions
    };
  }

  const totalDays = end.dayIndex - start.dayIndex + 1;

  if (start.year !== end.year || start.month !== end.month) {
    const endMonthLabel = getMonthLabel(end.year, end.month);
    return {
      isValid: false,
      code: 'CROSS_MONTH_FORBIDDEN',
      heading: 'Cross-month requests are not permitted',
      message: `Start date (${startDisplay}) is in ${options.monthLabel} and end date (${endDisplay}) is in ${endMonthLabel}. The entire mess cut must stay within ${options.monthLabel}.`,
      totalDays,
      startDisplay,
      endDisplay,
      suggestions: options.suggestions
    };
  }

  if (totalDays < 7 || totalDays % 7 !== 0) {
    const validList = options.suggestions.map((s) => `${s.display} (${s.days} days)`).join(', ');
    return {
      isValid: false,
      code: 'NOT_MULTIPLE_OF_7',
      heading: `Invalid duration (${totalDays} day${totalDays === 1 ? '' : 's'})`,
      message: `Inclusive duration from ${startDisplay} to ${endDisplay} is ${totalDays} day${totalDays === 1 ? '' : 's'}. Mess cut duration must strictly be a multiple of 7 days. Valid end dates for ${startDisplay}: ${validList}.`,
      totalDays,
      startDisplay,
      endDisplay,
      suggestions: options.suggestions
    };
  }

  return {
    isValid: true,
    code: 'VALID',
    heading: `Valid Mess Cut Period (${totalDays} Days)`,
    message: `${startDisplay} to ${endDisplay} is ${totalDays} inclusive days within ${options.monthLabel}.`,
    totalDays,
    startDisplay,
    endDisplay,
    suggestions: options.suggestions
  };
}

export const FIXED_RECIPIENT = 'The Warden,\nMH 2 Hostel,\nRIT Kottayam.';

export function validateCompleteApplication(profile, request) {
  const missingFields = [];
  const recipient = (profile.recipientAddress || FIXED_RECIPIENT).trim();
  if (!recipient) {
    missingFields.push('Recipient Address');
  }
  if (!profile.name || !profile.name.trim()) {
    missingFields.push('Student Name');
  }
  if (!profile.admissionNumber || !profile.admissionNumber.trim()) {
    missingFields.push('Admission Number');
  }
  if (!profile.semester || !profile.semester.trim()) {
    missingFields.push('Semester');
  }
  if (!profile.branch || !profile.branch.trim()) {
    missingFields.push('Branch');
  }
  if (!request.reason || !request.reason.trim()) {
    missingFields.push('Reason for Mess Cut');
  }

  const dateValidation = validateDateRange(request.startDate || '', request.endDate || '');
  const isReadyForExport = missingFields.length === 0 && dateValidation.isValid;

  return {
    isReadyForExport,
    missingFields,
    dateValidation
  };
}
