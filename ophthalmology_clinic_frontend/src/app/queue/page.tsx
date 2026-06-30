"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, subscribeRealtime } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDateTime, patientName } from "@/lib/format";
import type { Patient, PaymentMethod, PaymentStatus, QueueEntry, QueueEntryPayload, TodayIncome, User } from "@/lib/types";

const emptyQueueForm: QueueEntryPayload = {
  patient_id: null,
  first_name: "",
  last_name: "",
  age: null,
  gender: "",
  phone: "",
  address: "",
  reason: "Routine eye check-up"
};

export default function QueuePage() {
  const router = useRouter();
  const [me, setMe] = useState<User | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [queue, setQueue] = useState<QueueEntry[]>([]);
  const [completed, setCompleted] = useState<QueueEntry[]>([]);
  const [income, setIncome] = useState<TodayIncome | null>(null);
  const [form, setForm] = useState<QueueEntryPayload>(emptyQueueForm);
  const [confirmingPaymentId, setConfirmingPaymentId] = useState<number | null>(null);
  const [editingPaymentId, setEditingPaymentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const currentUser = await api.me();
      const [patientList, queueList, completedList, incomeSummary] = await Promise.all([
        api.patients(),
        api.queueToday(),
        api.completedQueueToday(),
        api.queueTodayIncome().catch(() => null)
      ]);
      setMe(currentUser);
      setPatients(patientList);
      setQueue(queueList);
      setCompleted(completedList);
      setIncome(incomeSummary);
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        router.replace("/login");
        return;
      }
      setError(loadError instanceof Error ? loadError.message : "Unable to load queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    return subscribeRealtime((event) => {
      if (["queue.updated", "payments.updated", "consultations.completed"].includes(event.type)) {
        load();
      }
    });
  }, []);

  const waiting = useMemo(() => queue.filter((entry) => entry.status === "waiting"), [queue]);
  const topEntry = waiting[0];
  async function addToQueue(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.addQueueEntry(form);
      setForm(emptyQueueForm);
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to add patient to queue");
    } finally {
      setSaving(false);
    }
  }

  async function startConsultation(entry: QueueEntry) {
    setSaving(true);
    setError("");
    try {
      const started = await api.startQueueEntry(entry.id);
      router.push(`/consultations/new?patientId=${started.patient_id}`);
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Unable to start consultation");
    } finally {
      setSaving(false);
    }
  }

  async function updatePayment(visitId: number, payment_status: PaymentStatus, payment_method?: PaymentMethod | null) {
    setSaving(true);
    setError("");
    try {
      await api.updateVisitPayment(visitId, {
        payment_status,
        payment_method: payment_status === "paid" ? payment_method ?? "cash" : null
      });
      setConfirmingPaymentId(null);
      setEditingPaymentId(null);
      await load();
    } catch (paymentError) {
      setError(paymentError instanceof Error ? paymentError.message : "Unable to update payment");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-2xl font-semibold text-clinic-ink">Today's Queue</h1>
            <p className="text-sm text-clinic-muted">Active consultations, completed patients and payment status</p>
          </div>
          {topEntry && me?.role !== "receptionist" ? (
            <button disabled={saving} onClick={() => startConsultation(topEntry)} className="min-h-11 rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
              Start Top Patient
            </button>
          ) : null}
        </div>

        {loading ? <LoadingState label="Loading queue" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading ? (
          <section className="grid gap-5 xl:grid-cols-2">
            <QueuePanel entries={queue} saving={saving} canStart={me?.role !== "receptionist"} onStart={startConsultation} />

            <div className="rounded border border-clinic-line bg-white shadow-soft">
              <div className="flex flex-col gap-2 border-b border-clinic-line px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                <h2 className="font-semibold text-clinic-ink">Completed Today</h2>
                {income ? <span className="text-sm font-semibold text-clinic-teal">Income: Rs. {Number(income.total_income).toFixed(2)}</span> : null}
              </div>
              <div className="divide-y divide-clinic-line">
                {completed.map((entry, index) => {
                  return (
                    <div key={entry.id} className="space-y-3 px-4 py-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="font-semibold text-clinic-ink">{index + 1}. {patientName(entry.patient)}</p>
                          <p className="text-sm text-clinic-muted">
                            Consultation #{entry.completed_visit_id ?? entry.id} - {entry.patient?.patient_id} - {formatDateTime(entry.completed_at)}
                          </p>
                        </div>
                        <span className={`rounded px-3 py-1 text-sm font-semibold ${entry.payment_status === "paid" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-900"}`}>
                          {entry.payment_status === "paid" ? `Paid${entry.payment_method ? ` (${entry.payment_method.replace("_", " ")})` : ""}` : "Not paid"}
                        </span>
                      </div>
                      {entry.completed_visit_id ? (
                        <QueuePaymentActions
                          entry={entry}
                          saving={saving}
                          editing={editingPaymentId === entry.completed_visit_id}
                          confirming={confirmingPaymentId === entry.completed_visit_id}
                          onChange={(status, method) => updatePayment(entry.completed_visit_id!, status, method)}
                          onRequestChange={() => setConfirmingPaymentId(entry.completed_visit_id!)}
                          onCancelChange={() => setConfirmingPaymentId(null)}
                          onConfirmChange={() => {
                            setConfirmingPaymentId(null);
                            setEditingPaymentId(entry.completed_visit_id!);
                          }}
                        />
                      ) : null}
                    </div>
                  );
                })}
                {completed.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No completed consultations yet.</p> : null}
              </div>
            </div>

            {me?.role !== "doctor" ? (
              <form onSubmit={addToQueue} className="rounded border border-clinic-line bg-white p-4 shadow-soft xl:col-span-2">
                <h2 className="font-semibold text-clinic-ink">Add Patient To Queue</h2>
                <label className="mt-4 block">
                  <span className="text-sm font-semibold">Existing patient</span>
                  <select
                    value={form.patient_id ?? ""}
                    onChange={(event) => setForm((current) => ({ ...current, patient_id: event.target.value ? Number(event.target.value) : null }))}
                    className="mt-2 min-h-12 w-full rounded border border-clinic-line px-3"
                  >
                    <option value="">New patient or search by details</option>
                    {patients.map((patient) => (
                      <option key={patient.id} value={patient.id}>{patientName(patient)} - {patient.patient_id}</option>
                    ))}
                  </select>
                </label>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Input label="First Name" value={form.first_name ?? ""} onChange={(value) => setForm((current) => ({ ...current, first_name: value }))} />
                  <Input label="Last Name" value={form.last_name ?? ""} onChange={(value) => setForm((current) => ({ ...current, last_name: value }))} />
                  <Input label="Age" type="number" value={form.age?.toString() ?? ""} onChange={(value) => setForm((current) => ({ ...current, age: value ? Number(value) : null }))} />
                  <Input label="Sex" value={form.gender ?? ""} onChange={(value) => setForm((current) => ({ ...current, gender: value }))} />
                  <Input label="Mobile" value={form.phone ?? ""} onChange={(value) => setForm((current) => ({ ...current, phone: value }))} />
                  <Input label="Reason" value={form.reason ?? ""} onChange={(value) => setForm((current) => ({ ...current, reason: value }))} />
                </div>
                <label className="mt-3 block">
                  <span className="text-sm font-semibold">Address</span>
                  <textarea value={form.address ?? ""} onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))} rows={3} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
                </label>
                <button disabled={saving} className="mt-4 min-h-11 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
                  {saving ? "Adding..." : "Add To Queue"}
                </button>
              </form>
            ) : null}
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}

function QueuePaymentActions({
  entry,
  saving,
  editing,
  confirming,
  onChange,
  onRequestChange,
  onCancelChange,
  onConfirmChange
}: {
  entry: QueueEntry;
  saving: boolean;
  editing: boolean;
  confirming: boolean;
  onChange: (paymentStatus: PaymentStatus, paymentMethod?: PaymentMethod | null) => void;
  onRequestChange: () => void;
  onCancelChange: () => void;
  onConfirmChange: () => void;
}) {
  const paidLabel = entry.payment_method === "upi_qr" ? "UPI" : "Cash";
  if (entry.payment_status === "paid" && !editing) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded bg-green-100 px-3 py-2 text-sm font-semibold text-green-800">✓ Paid ({paidLabel})</span>
          <button disabled={saving} onClick={onRequestChange} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">Change Payment</button>
        </div>
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
        ) : null}
      </div>
    );
  }
  return (
    <div className="flex flex-wrap gap-2">
      <button disabled={saving} onClick={() => onChange("paid", "cash")} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">
        Cash Paid
      </button>
      <button disabled={saving} onClick={() => onChange("paid", "upi_qr")} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">
        UPI Paid
      </button>
      {editing ? (
        <button disabled={saving} onClick={() => onChange("not_paid", null)} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">
          Mark Unpaid
        </button>
      ) : null}
    </div>
  );
}

function QueuePanel({ entries, saving, canStart, onStart }: { entries: QueueEntry[]; saving: boolean; canStart: boolean; onStart: (entry: QueueEntry) => void }) {
  return (
    <div className="rounded border border-clinic-line bg-white shadow-soft">
      <div className="border-b border-clinic-line px-4 py-3">
        <h2 className="font-semibold text-clinic-ink">Active Queue</h2>
      </div>
      <div className="divide-y divide-clinic-line">
        {entries.map((entry, index) => (
          <div key={entry.id} className="flex flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-semibold text-clinic-ink">{index + 1}. {patientName(entry.patient)}</p>
              <p className="text-sm text-clinic-muted">
                {entry.patient?.patient_id} - {entry.patient?.phone ?? "No mobile"} - {formatDateTime(entry.created_at)}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-clinic-wash px-3 py-1 text-sm font-semibold capitalize text-clinic-ink">{entry.status.replace("_", " ")}</span>
              {canStart ? (
                <button disabled={saving} onClick={() => onStart(entry)} className="min-h-10 rounded bg-clinic-teal px-3 text-sm font-semibold text-white disabled:opacity-60">
                  Start
                </button>
              ) : null}
            </div>
          </div>
        ))}
        {entries.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No patients in queue.</p> : null}
      </div>
    </div>
  );
}

function Input({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="text-sm font-semibold">{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
    </label>
  );
}
