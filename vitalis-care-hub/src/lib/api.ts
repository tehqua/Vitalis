/**
 * api.ts — Vitalis Admin API service layer
 *
 * All admin API calls go through this module.
 * Base URL is read from VITE_API_BASE_URL (default: http://localhost:8000)
 *
 * Admin JWT is stored in sessionStorage under "admin_token".
 * Every request attaches Authorization: Bearer <token> automatically.
 */

const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

/** Admin token: stored in sessionStorage on login, or from env for dev */
function getToken(): string | null {
  return (
    sessionStorage.getItem('admin_token') ??
    (import.meta as any).env?.VITE_ADMIN_SECRET_KEY ??
    null
  );
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> ?? {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface OverviewStats {
  active_patients: number;
  sessions_today: number;
  reminders_sent_today: number;
  pending_codes: number;
  new_forgot_requests: number;
}

export interface ActivityItem {
  time: string;
  type: string;
  patient: string;
  status: string;
}

export interface SystemService {
  name: string;
  status: 'Operational' | 'Degraded' | 'Down';
}

export interface Patient {
  id: string;           // format: FirstName###_LastName###_uuid
  name: string;
  status: 'Active' | 'Pending' | 'Inactive';
  consented: boolean;
  consent_date: string;
  last_session: string;
  sessions: number;
  email?: string;
  phone?: string;
}

export interface PatientCode {
  patient_id: string;   // IS the login code: FirstName###_LastName###_uuid
  patient_name: string;
  issued_at: string;
  status: 'Active' | 'Used' | 'Revoked';
  first_login_at: string | null;
}

export interface MedicationSchedule {
  id: string;
  patient_id: string;
  patient_name: string;
  medication: string;
  dosage: string;
  frequency: string;
  times: string[];
  start_date: string;
  end_date: string | null;
  reminders_sent: number;
  reminders_total: number;
  status: 'Active' | 'Paused' | 'Completed';
}

export interface ReminderLog {
  id: string;
  sent_at: string;
  patient_name: string;
  medication: string;
  email_masked: string;
  status: 'Delivered' | 'Failed' | 'Pending';
  error?: string;
}

export interface ForgotRequest {
  id: string;
  submitted_at: string;
  name: string;
  dob: string;
  phone: string;
  email: string;
  visit_date: string;
  department: string;
  notes: string;
  status: 'New' | 'In Progress' | 'Resolved';
}

// ─── Overview ────────────────────────────────────────────────────────────────

export async function fetchOverviewStats(): Promise<OverviewStats> {
  return request<OverviewStats>('/api/admin/stats');
}

export async function fetchRecentActivity(): Promise<ActivityItem[]> {
  return request<ActivityItem[]>('/api/admin/activity');
}

export async function fetchSystemStatus(): Promise<SystemService[]> {
  return request<SystemService[]>('/api/admin/system-status');
}

// ─── Patients ─────────────────────────────────────────────────────────────────

export async function fetchPatients(): Promise<Patient[]> {
  return request<Patient[]>('/api/admin/patients');
}

export async function createPatient(data: { name: string; email: string; phone: string }): Promise<Patient> {
  return request<Patient>('/api/admin/patients', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ─── Patient Codes (Patient ID = Login Code) ─────────────────────────────────

export async function fetchPatientCodes(): Promise<PatientCode[]> {
  return request<PatientCode[]>('/api/admin/patient-codes');
}

export async function revokePatientCode(patientId: string): Promise<void> {
  return request<void>(`/api/admin/patient-codes/${encodeURIComponent(patientId)}/revoke`, {
    method: 'PATCH',
  });
}

// ─── Medications ──────────────────────────────────────────────────────────────

export async function fetchMedications(): Promise<MedicationSchedule[]> {
  return request<MedicationSchedule[]>('/api/admin/medications');
}

export async function createMedication(data: Partial<MedicationSchedule>): Promise<MedicationSchedule> {
  return request<MedicationSchedule>('/api/admin/medications', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateMedicationStatus(id: string, status: string): Promise<void> {
  return request<void>(`/api/admin/medications/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function deleteMedication(id: string): Promise<void> {
  return request<void>(`/api/admin/medications/${id}`, { method: 'DELETE' });
}

// ─── Reminders Log ────────────────────────────────────────────────────────────

export async function fetchReminderLogs(): Promise<ReminderLog[]> {
  return request<ReminderLog[]>('/api/admin/reminder-logs');
}

// ─── Forgot ID Requests ──────────────────────────────────────────────────────

export async function fetchForgotRequests(): Promise<ForgotRequest[]> {
  return request<ForgotRequest[]>('/api/admin/forgot-id-requests');
}

export async function updateForgotRequestStatus(id: string, status: string): Promise<void> {
  return request<void>(`/api/admin/forgot-id-requests/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}
