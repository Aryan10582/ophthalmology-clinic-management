import type { Patient } from "./types";

export function patientName(patient?: Pick<Patient, "first_name" | "last_name"> | null) {
  if (!patient) return "Unknown patient";
  return `${patient.first_name} ${patient.last_name}`.trim();
}

export function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value));
}
