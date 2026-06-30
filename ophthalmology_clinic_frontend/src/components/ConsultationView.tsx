"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, subscribeRealtime } from "@/lib/api";
import { formatDate, patientName } from "@/lib/format";
import type { PaymentMethod, PaymentStatus, PrescriptionTemplate, Visit } from "@/lib/types";
import { ErrorState } from "./ErrorState";
import { PatientBanner } from "./PatientBanner";

const examRows = [
  ["Eyelids & Adnexa", "eyelids_adnexa_right", "eyelids_adnexa_left"],
  ["Extra Ocular Movements", "extra_ocular_movements_right", "extra_ocular_movements_left"],
  ["Cornea", "cornea_right", "cornea_left"],
  ["Anterior Chamber", "anterior_chamber_right", "anterior_chamber_left"],
  ["Conjunctiva", "conjunctiva_right", "conjunctiva_left"],
  ["Pupil", "pupil_right", "pupil_left"],
  ["Lens", "lens_right", "lens_left"],
  ["Fundus", "fundus_right", "fundus_left"]
] as const;

export function ConsultationView({ visit: initialVisit }: { visit: Visit }) {
  const [visit, setVisit] = useState(initialVisit);
  const [template, setTemplate] = useState<PrescriptionTemplate | null>(null);
  const [confirmingPaymentChange, setConfirmingPaymentChange] = useState(false);
  const [editingPayment, setEditingPayment] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.prescriptionTemplate().then(setTemplate).catch(() => setTemplate(null));
  }, []);

  useEffect(() => {
    return subscribeRealtime((event) => {
      if (["payments.updated", "consultations.completed"].includes(event.type)) {
        api.visit(visit.id).then(setVisit).catch(() => undefined);
      }
    });
  }, [visit.id]);

  async function endConsultation() {
    setSaving(true);
    setError("");
    try {
      setVisit(await api.endVisit(visit.id));
    } catch (endError) {
      setError(endError instanceof Error ? endError.message : "Unable to end consultation");
    } finally {
      setSaving(false);
    }
  }

  async function updatePayment(payment_status: PaymentStatus, payment_method?: PaymentMethod | null) {
    setSaving(true);
    setError("");
    try {
      setVisit(await api.updateVisitPayment(visit.id, { payment_status, payment_method: payment_status === "paid" ? payment_method ?? "cash" : null }));
      setConfirmingPaymentChange(false);
      setEditingPayment(false);
    } catch (paymentError) {
      setError(paymentError instanceof Error ? paymentError.message : "Unable to update payment");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
    <div className="screen-consultation print-sheet space-y-5">
      {error ? <ErrorState message={error} /> : null}
      <PatientBanner patient={visit.patient} doctor={visit.doctor} visit={visit} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-clinic-ink">{patientName(visit.patient)}</h2>
          <p className="text-sm text-clinic-muted">Presenting complaint: {visit.chief_complaint}</p>
          <p className="text-sm text-clinic-muted">Status: {visit.completed_at ? `Completed ${formatDate(visit.completed_at)}` : "In consultation"}</p>
        </div>
        <div className="no-print flex flex-wrap gap-2">
          {!visit.completed_at ? (
            <button disabled={saving} onClick={endConsultation} className="min-h-11 rounded bg-clinic-teal px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
              End Consultation
            </button>
          ) : null}
          <button type="button" onClick={() => window.print()} className="min-h-11 rounded border border-clinic-line bg-white px-4 py-2 text-sm font-semibold text-clinic-ink">
            Print
          </button>
          <Link href={`/consultations/${visit.id}/edit`} className="min-h-11 rounded border border-clinic-line bg-white px-4 py-2 text-sm font-semibold text-clinic-ink">
            Edit
          </Link>
        </div>
      </div>

      <section className="no-print rounded border border-clinic-line bg-white p-4 shadow-soft">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="font-semibold text-clinic-ink">Consultation Payment</h3>
            <p className="text-sm text-clinic-muted">Fee: Rs. {Number(visit.consultation_fee ?? 0).toFixed(2)} - {visit.payment_status === "paid" ? `Paid by ${visit.payment_method?.replace("_", " ")}` : "Not paid"}</p>
          </div>
          <PaymentActions
            status={visit.payment_status ?? "not_paid"}
            method={visit.payment_method}
            saving={saving}
            editing={editingPayment}
            confirming={confirmingPaymentChange}
            onChange={updatePayment}
            onRequestChange={() => setConfirmingPaymentChange(true)}
            onCancelChange={() => setConfirmingPaymentChange(false)}
            onConfirmChange={() => {
              setConfirmingPaymentChange(false);
              setEditingPayment(true);
            }}
          />
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        {visit.distance_prescription_enabled ? <PrescriptionView title="Distance Prescription" prefix="distance" visit={visit} /> : null}
        {visit.near_prescription_enabled ? <PrescriptionView title="Near Prescription" prefix="near" visit={visit} /> : null}
      </section>

      {visit.iop_enabled ? (
        <section className="rounded border border-clinic-line bg-white shadow-soft">
          <div className="border-b border-clinic-line px-4 py-3">
            <h3 className="font-semibold text-clinic-ink">Intraocular Pressure</h3>
          </div>
          <div className="grid gap-px bg-clinic-line sm:grid-cols-2">
            <div className="bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Right</p>
              <p className="mt-1 text-lg font-semibold">{visit.iop_right ?? "-"} mmHg</p>
            </div>
            <div className="bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Left</p>
              <p className="mt-1 text-lg font-semibold">{visit.iop_left ?? "-"} mmHg</p>
            </div>
          </div>
        </section>
      ) : null}

      <section className="rounded border border-clinic-line bg-white shadow-soft">
        <div className="border-b border-clinic-line px-4 py-3">
          <h3 className="font-semibold text-clinic-ink">Ophthalmic Examination</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-left">
            <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
              <tr>
                <th className="border-b border-clinic-line px-4 py-3">Finding</th>
                <th className="border-b border-clinic-line px-4 py-3">RIGHT EYE</th>
                <th className="border-b border-clinic-line px-4 py-3">LEFT EYE</th>
              </tr>
            </thead>
            <tbody>
              {examRows.map(([label, rightKey, leftKey]) => (
                <tr key={label}>
                  <td className="border-b border-clinic-line px-4 py-3 font-semibold">{label}</td>
                  <td className="border-b border-clinic-line px-4 py-3">{(visit[rightKey] as string | null) || "-"}</td>
                  <td className="border-b border-clinic-line px-4 py-3">{(visit[leftKey] as string | null) || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded border border-clinic-line bg-white p-4 shadow-soft">
        <h3 className="font-semibold text-clinic-ink">Consultation Notes</h3>
        <dl className="mt-3 grid gap-4 md:grid-cols-2">
          <Note label="Diagnosis" value={visit.diagnosis} />
          <Note label="Advice" value={visit.advice} />
          <Note label="Tests Prescribed" value={visit.tests_prescribed} />
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Next Visit</dt>
            <dd className="mt-1 text-sm">{formatDate(visit.follow_up_date)}</dd>
          </div>
          <div className="md:col-span-2">
            <dt className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Additional Notes</dt>
            <dd className="mt-1 whitespace-pre-wrap text-sm">{visit.additional_notes || visit.notes || "-"}</dd>
          </div>
        </dl>
      </section>
    </div>
    <PrintablePrescription visit={visit} template={template} />
    </>
  );
}

function PrintablePrescription({ visit, template }: { visit: Visit; template: PrescriptionTemplate | null }) {
  const templateName = template?.template_name === "minimal_white" ? "minimal_white" : "professional_blue";
  const accent = templateName === "professional_blue" ? "#125f9d" : "#17202a";
  const border = templateName === "professional_blue" ? "#b7d2e8" : "#d8e1e8";
  const doctorName = template?.doctor_name ?? "";
  const qualifications = template?.doctor_qualifications ?? "";
  const registrationNumber = template?.doctor_registration_number ?? "";
  const clinicName = template?.clinic_name ?? "";
  const clinicAddress = template?.clinic_address ?? "";
  const clinicPhone = template?.clinic_phone ?? "";
  const clinicTimings = template?.clinic_timings ?? "";
  const clinicEmail = template?.email ?? "";
  const clinicWebsite = template?.website ?? "";
  const hasLogo = Boolean(template?.clinic_logo);
  const hasSignature = Boolean(template?.doctor_signature);
  return (
    <article className={`prescription-print prescription-${templateName}`} style={{ ["--rx-accent" as string]: accent, ["--rx-border" as string]: border }}>
      <header className={`rx-header${hasLogo ? "" : " rx-header-no-logo"}`}>
        {hasLogo ? (
          <div className="rx-logo-panel">
            <img src={template?.clinic_logo ?? ""} alt="" className="rx-logo" />
          </div>
        ) : null}
        <div className="rx-clinic-info">
          {clinicName ? <h2>{clinicName}</h2> : null}
          {clinicAddress ? <p>{clinicAddress}</p> : null}
          {clinicPhone ? <p><strong>Phone:</strong> {clinicPhone}</p> : null}
          {clinicTimings ? <p><strong>Timings:</strong> {clinicTimings}</p> : null}
          {clinicEmail ? <p><strong>Email:</strong> {clinicEmail}</p> : null}
          {clinicWebsite ? <p><strong>Website:</strong> {clinicWebsite}</p> : null}
        </div>
        <div className="rx-doctor-info">
          {doctorName ? <h1>{doctorName}</h1> : null}
          {qualifications ? <p className="rx-qualification">{qualifications}</p> : null}
          {registrationNumber ? <p className="rx-registration">Reg. No: {registrationNumber}</p> : null}
        </div>
      </header>

      <section className="rx-patient-block">
        <table className="rx-patient-table">
          <colgroup>
            <col className="rx-patient-label" />
            <col className="rx-patient-value rx-patient-name" />
            <col className="rx-patient-label" />
            <col className="rx-patient-value" />
            <col className="rx-patient-label" />
            <col className="rx-patient-value" />
          </colgroup>
          <tbody>
            <tr>
              <th>Patient Name</th>
              <td>{patientName(visit.patient)}</td>
              <th>Patient ID</th>
              <td>{visit.patient?.patient_id || "-"}</td>
              <th>Consultation Date</th>
              <td>{formatDate(visit.visit_date)}</td>
            </tr>
            <tr>
              <th>Age</th>
              <td>{visit.patient?.age ?? "-"}</td>
              <th>Sex</th>
              <td>{visit.patient?.gender || "-"}</td>
              <th>Mobile Number</th>
              <td>{visit.patient?.phone || "-"}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <PrintTextSection title="Chief Complaint" value={visit.chief_complaint} />
      {visit.distance_prescription_enabled ? <PrintPrescriptionTable title="Distance Prescription" prefix="distance" visit={visit} /> : null}
      {visit.near_prescription_enabled ? <PrintPrescriptionTable title="Near Prescription" prefix="near" visit={visit} /> : null}

      <section className="rx-section">
        <h2>Ophthalmic Examination</h2>
        <table className="rx-exam-table">
          <colgroup>
            <col className="rx-exam-finding" />
            <col className="rx-eye-column" />
            <col className="rx-eye-column" />
          </colgroup>
          <thead>
            <tr><th>Finding</th><th>Right Eye</th><th>Left Eye</th></tr>
          </thead>
          <tbody>
            {examRows.map(([label, rightKey, leftKey]) => (
              <tr key={label}>
                <th>{label}</th>
                <td>{(visit[rightKey] as string | null) || "-"}</td>
                <td>{(visit[leftKey] as string | null) || "-"}</td>
              </tr>
            ))}
            {visit.iop_enabled ? (
              <tr>
                <th>Intraocular Pressure</th>
                <td>{visit.iop_right ?? "-"} mmHg</td>
                <td>{visit.iop_left ?? "-"} mmHg</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>

      <PrintTextSection title="Diagnosis" value={visit.diagnosis} />
      <PrintTextSection title="Advice" value={visit.advice} />
      <PrintTextSection title="Tests Prescribed" value={visit.tests_prescribed} />
      <PrintTextSection title="Additional Notes" value={visit.additional_notes || visit.notes} />
      <PrintTextSection title="Next Visit" value={formatDate(visit.follow_up_date)} />

      <footer className="rx-footer">
        {template?.footer_text ? <div className="rx-footer-text">{template.footer_text}</div> : <div />}
        <div className="rx-signature">
          {hasSignature ? (
            <>
              <img src={template?.doctor_signature ?? ""} alt="" />
              {doctorName ? <strong>{doctorName}</strong> : null}
              {qualifications ? <span>{qualifications}</span> : null}
            </>
          ) : (
            <div className="rx-signature-line" />
          )}
        </div>
      </footer>
    </article>
  );
}

function PrintPrescriptionTable({ title, prefix, visit }: { title: string; prefix: "distance" | "near"; visit: Visit }) {
  return (
    <section className="rx-section">
      <h2>{title}</h2>
      <table className="rx-prescription-table">
        <colgroup>
          <col className="rx-rx-eye" />
          <col className="rx-rx-value" />
          <col className="rx-rx-value" />
          <col className="rx-rx-axis" />
          <col className="rx-rx-value" />
          <col className="rx-rx-add" />
        </colgroup>
        <thead><tr><th>Eye</th><th>SPH</th><th>CYL</th><th>AXIS</th><th>VA</th><th>Add</th></tr></thead>
        <tbody>
          <tr><th>Right Eye</th><td>{visit[`${prefix}_right_sphere`] || "-"}</td><td>{visit[`${prefix}_right_cylinder`] || "-"}</td><td>{visit[`${prefix}_right_axis`] ?? "-"}</td><td>{visit[`${prefix}_right_va`] || "-"}</td><td>{visit[`${prefix}_add`] || "-"}</td></tr>
          <tr><th>Left Eye</th><td>{visit[`${prefix}_left_sphere`] || "-"}</td><td>{visit[`${prefix}_left_cylinder`] || "-"}</td><td>{visit[`${prefix}_left_axis`] ?? "-"}</td><td>{visit[`${prefix}_left_va`] || "-"}</td><td>{visit[`${prefix}_add`] || "-"}</td></tr>
        </tbody>
      </table>
    </section>
  );
}

function PrintTextSection({ title, value }: { title: string; value?: string | null }) {
  if (!value) return null;
  return (
    <section className="rx-section">
      <h2>{title}</h2>
      <p>{value}</p>
    </section>
  );
}

function PaymentActions({
  status,
  method,
  saving,
  editing,
  confirming,
  onChange,
  onRequestChange,
  onCancelChange,
  onConfirmChange
}: {
  status: PaymentStatus;
  method?: PaymentMethod | null;
  saving: boolean;
  editing: boolean;
  confirming: boolean;
  onChange: (paymentStatus: PaymentStatus, paymentMethod?: PaymentMethod | null) => void;
  onRequestChange: () => void;
  onCancelChange: () => void;
  onConfirmChange: () => void;
}) {
  const paidLabel = method === "upi_qr" ? "UPI" : "Cash";
  if (status === "paid" && !editing) {
    return (
      <div className="flex flex-col gap-2 sm:items-end">
        <span className="rounded bg-green-100 px-3 py-2 text-sm font-semibold text-green-800">Paid ({paidLabel})</span>
        {confirming ? (
          <div className="rounded border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-950">
            <p className="font-semibold">Change Payment Status?</p>
            <p className="mt-1">This consultation has already been marked as paid.</p>
            <p>Are you sure you want to modify the payment?</p>
            <div className="mt-3 flex gap-2">
              <button type="button" onClick={onCancelChange} className="min-h-9 rounded border border-yellow-300 bg-white px-3 font-semibold">Cancel</button>
              <button type="button" onClick={onConfirmChange} className="min-h-9 rounded bg-clinic-teal px-3 font-semibold text-white">Confirm</button>
            </div>
          </div>
        ) : (
          <button disabled={saving} onClick={onRequestChange} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">Change Payment</button>
        )}
      </div>
    );
  }
  return (
    <div className="flex flex-wrap gap-2">
      <button disabled={saving} onClick={() => onChange("paid", "cash")} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">Cash Paid</button>
      <button disabled={saving} onClick={() => onChange("paid", "upi_qr")} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">UPI Paid</button>
      {editing ? <button disabled={saving} onClick={() => onChange("not_paid", null)} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">Mark Unpaid</button> : null}
    </div>
  );
}

function PrescriptionView({ title, prefix, visit }: { title: string; prefix: "distance" | "near"; visit: Visit }) {
  const values = {
    rightSphere: visit[`${prefix}_right_sphere`],
    rightCylinder: visit[`${prefix}_right_cylinder`],
    rightAxis: visit[`${prefix}_right_axis`],
    rightVa: visit[`${prefix}_right_va`],
    leftSphere: visit[`${prefix}_left_sphere`],
    leftCylinder: visit[`${prefix}_left_cylinder`],
    leftAxis: visit[`${prefix}_left_axis`],
    leftVa: visit[`${prefix}_left_va`],
    add: visit[`${prefix}_add`]
  };

  return (
    <section className="rounded border border-clinic-line bg-white shadow-soft">
      <div className="border-b border-clinic-line px-4 py-3">
        <h3 className="font-semibold text-clinic-ink">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[620px] border-collapse text-left">
          <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
            <tr>
              <th className="border-b border-clinic-line px-4 py-3">Eye</th>
              <th className="border-b border-clinic-line px-4 py-3">Sphere</th>
              <th className="border-b border-clinic-line px-4 py-3">Cylinder</th>
              <th className="border-b border-clinic-line px-4 py-3">Axis</th>
              <th className="border-b border-clinic-line px-4 py-3">VA</th>
              <th className="border-b border-clinic-line px-4 py-3">Add</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border-b border-clinic-line px-4 py-3 font-semibold">RIGHT EYE</td>
              <td className="border-b border-clinic-line px-4 py-3">{values.rightSphere || "-"}</td>
              <td className="border-b border-clinic-line px-4 py-3">{values.rightCylinder || "-"}</td>
              <td className="border-b border-clinic-line px-4 py-3">{values.rightAxis ?? "-"}</td>
              <td className="border-b border-clinic-line px-4 py-3">{values.rightVa || "-"}</td>
              <td className="border-b border-clinic-line px-4 py-3">{values.add || "-"}</td>
            </tr>
            <tr>
              <td className="px-4 py-3 font-semibold">LEFT EYE</td>
              <td className="px-4 py-3">{values.leftSphere || "-"}</td>
              <td className="px-4 py-3">{values.leftCylinder || "-"}</td>
              <td className="px-4 py-3">{values.leftAxis ?? "-"}</td>
              <td className="px-4 py-3">{values.leftVa || "-"}</td>
              <td className="px-4 py-3">{values.add || "-"}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Note({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">{label}</dt>
      <dd className="mt-1 whitespace-pre-wrap text-sm">{value || "-"}</dd>
    </div>
  );
}
