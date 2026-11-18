/**
 * Persistence layer for student details and request draft.
 * Preserves data in browser LocalStorage with automatic backend synchronization.
 */

const STORAGE_KEYS = {
  STUDENT: 'messcut_student_v2',
  DRAFT: 'messcut_draft_v2',
};

export const FIXED_RECIPIENT = 'The Warden,\nMH 2 Hostel,\nRIT Kottayam.';

function readJSON(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function writeJSON(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function loadStudentData() {
  const data = readJSON(STORAGE_KEYS.STUDENT, {});
  return {
    name: typeof data.name === 'string' ? data.name : '',
    admissionNumber: typeof data.admissionNumber === 'string' ? data.admissionNumber : '',
    semester: typeof data.semester === 'string' ? data.semester : '',
    branch: typeof data.branch === 'string' ? data.branch : '',
    recipientAddress: FIXED_RECIPIENT,
  };
}

export function saveStudentData(student) {
  const payload = {
    name: (student.name || '').trim(),
    admissionNumber: (student.admissionNumber || '').trim(),
    semester: (student.semester || '').trim(),
    branch: (student.branch || '').trim(),
    recipientAddress: FIXED_RECIPIENT,
  };
  writeJSON(STORAGE_KEYS.STUDENT, payload);

  fetch('/api/student', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch(() => {});

  return payload;
}

export function loadRequestDraft() {
  const draft = readJSON(STORAGE_KEYS.DRAFT, {});
  return {
    reason: typeof draft.reason === 'string' ? draft.reason : '',
    startDate: typeof draft.startDate === 'string' ? draft.startDate : '',
    endDate: typeof draft.endDate === 'string' ? draft.endDate : '',
  };
}

export function saveRequestDraft(draft) {
  const payload = {
    reason: draft.reason || '',
    startDate: draft.startDate || '',
    endDate: draft.endDate || '',
  };
  writeJSON(STORAGE_KEYS.DRAFT, payload);

  fetch('/api/draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch(() => {});
}

export function clearAllStoredData() {
  try {
    window.localStorage.removeItem(STORAGE_KEYS.STUDENT);
    window.localStorage.removeItem(STORAGE_KEYS.DRAFT);
    // Also remove any legacy profile keys
    window.localStorage.removeItem('messcut_profiles_v1');
    window.localStorage.removeItem('messcut_active_profile_id_v1');
    window.localStorage.removeItem('messcut_request_draft_v1');
  } catch {
    // Ignore
  }

  fetch('/api/clear', { method: 'POST' }).catch(() => {});
}

export async function syncFromBackendIfEmpty() {
  const local = loadStudentData();
  const hasLocal = local.name || local.admissionNumber;
  if (!hasLocal) {
    try {
      const res = await fetch('/api/student');
      if (res.ok) {
        const remote = await res.json();
        if (remote && (remote.name || remote.admissionNumber)) {
          saveStudentData(remote);
          return true;
        }
      }
    } catch {
      // Backend offline
    }
  }
  return false;
}
