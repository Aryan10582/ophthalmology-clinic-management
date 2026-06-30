import type { Patient, User, Visit } from "@/lib/types";
import { formatDateTime, patientName } from "@/lib/format";

type PatientBannerProps = {
  patient?: Patient | null;
  doctor?: User | null;
  visit?: Pick<Visit, "visit_date"> | null;
};

export function PatientBanner({ patient, doctor, visit }: PatientBannerProps) {
  const items = [
    ["Patient Name", patientName(patient)],
    ["Age", patient ? String(patient.age) : "-"],
    ["Sex", patient?.gender ?? "-"],
    ["Mobile Number", patient?.phone ?? "-"],
    ["Patient ID", patient?.patient_id ?? "-"],
    ["Visit Date", visit?.visit_date ? formatDateTime(visit.visit_date) : "New visit"],
    ["Doctor Name", doctor?.full_name ?? "-"]
  ];

  return (
    <section className="rounded border border-clinic-line bg-white shadow-soft">
      <div className="border-b border-clinic-line px-4 py-3 sm:px-5">
        <h1 className="text-base font-semibold text-clinic-ink sm:text-lg">Consultation Sheet</h1>
      </div>
      <dl className="grid gap-px bg-clinic-line sm:grid-cols-2 lg:grid-cols-4">
        {items.map(([label, value]) => (
          <div key={label} className="min-h-20 bg-white px-4 py-3">
            <dt className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">{label}</dt>
            <dd className="mt-1 text-base font-semibold text-clinic-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
