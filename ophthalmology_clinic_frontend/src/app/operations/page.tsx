"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, subscribeRealtime } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDate, patientName } from "@/lib/format";
import type { Operation, OperationPayload, OperationType, Patient, User } from "@/lib/types";

export default function OperationsPage() {
  const router = useRouter();
  const [me, setMe] = useState<User | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [doctors, setDoctors] = useState<User[]>([]);
  const [types, setTypes] = useState<OperationType[]>([]);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [newType, setNewType] = useState("");
  const [surgeryFilter, setSurgeryFilter] = useState<"all" | "ready" | "not_ready" | "completed">("all");
  const [paymentFilter, setPaymentFilter] = useState<"all" | "paid" | "not_paid">("all");
  const [dateFilter, setDateFilter] = useState("");
  const [form, setForm] = useState<OperationPayload>({
    patient_id: 0,
    doctor_id: 0,
    operation_type_id: 0,
    operation_date: new Date().toISOString().slice(0, 10),
    status: "scheduled",
    remarks: ""
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const currentUser = await api.me();
      const [patientList, typeList, operationList] = await Promise.all([api.patients(), api.operationTypes(), api.operations()]);
      const doctorList = currentUser.role === "admin" ? (await api.users()).filter((user) => user.role === "doctor") : currentUser.role === "doctor" ? [currentUser] : [];
      setMe(currentUser);
      setPatients(patientList);
      setDoctors(doctorList);
      setTypes(typeList);
      setOperations(operationList);
      setForm((current) => ({
        ...current,
        doctor_id: currentUser.role === "doctor" ? currentUser.id : doctorList[0]?.id ?? 0,
        operation_type_id: typeList[0]?.id ?? 0,
        patient_id: patientList[0]?.id ?? 0
      }));
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        router.replace("/login");
        return;
      }
      setError(loadError instanceof Error ? loadError.message : "Unable to load operations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    return subscribeRealtime((event) => {
      if (["operations.updated", "payments.updated", "reports.updated"].includes(event.type)) {
        load();
      }
    });
  }, []);

  async function createOperation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createOperation(form);
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to create operation");
    } finally {
      setSaving(false);
    }
  }

  async function addType() {
    if (!newType.trim()) return;
    const type = await api.createOperationType(newType.trim());
    setTypes((current) => [...current.filter((item) => item.id !== type.id), type]);
    setForm((current) => ({ ...current, operation_type_id: type.id }));
    setNewType("");
  }

  async function archiveType(type: OperationType) {
    setSaving(true);
    setError("");
    try {
      await api.archiveOperationType(type.id);
      await load();
    } catch (archiveError) {
      setError(archiveError instanceof Error ? archiveError.message : "Unable to archive operation type");
    } finally {
      setSaving(false);
    }
  }

  const filteredOperations = operations.filter((operation) => {
    const surgeryMatches =
      surgeryFilter === "all" ||
      (surgeryFilter === "completed" && operation.status === "completed") ||
      (surgeryFilter === "ready" && operation.status !== "completed" && operation.ready_for_surgery) ||
      (surgeryFilter === "not_ready" && operation.status !== "completed" && !operation.ready_for_surgery);
    const paymentMatches = paymentFilter === "all" || operation.payment_status === paymentFilter;
    const dateMatches = !dateFilter || operation.operation_date.slice(0, 10) === dateFilter;
    return surgeryMatches && paymentMatches && dateMatches;
  });

  return (
    <AppShell>
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-semibold text-clinic-ink">Operations</h1>
          <p className="text-sm text-clinic-muted">Operation records, readiness checklist and report uploads.</p>
        </div>
        {loading ? <LoadingState label="Loading operations" /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading ? (
          <section className={`grid gap-5 ${me?.role === "receptionist" ? "" : "xl:grid-cols-[1fr_1.3fr]"}`}>
            {me?.role !== "receptionist" ? (
              <form onSubmit={createOperation} className="rounded border border-clinic-line bg-white p-4 shadow-soft">
                <h2 className="font-semibold">Create Operation Record</h2>
                <div className="mt-4 grid gap-3">
                  <Select label="Patient" value={form.patient_id} onChange={(value) => setForm((current) => ({ ...current, patient_id: value }))} options={patients.map((patient) => ({ value: patient.id, label: `${patientName(patient)} - ${patient.patient_id}` }))} />
                  {me?.role === "admin" ? <Select label="Doctor" value={form.doctor_id} onChange={(value) => setForm((current) => ({ ...current, doctor_id: value }))} options={doctors.map((doctor) => ({ value: doctor.id, label: doctor.full_name }))} /> : null}
                  <Select label="Operation Type" value={form.operation_type_id} onChange={(value) => setForm((current) => ({ ...current, operation_type_id: value }))} options={types.map((type) => ({ value: type.id, label: `${type.name} - Rs. ${Number(type.price ?? 0).toFixed(2)}` }))} />
                  <div className="flex gap-2">
                    <input value={newType} onChange={(event) => setNewType(event.target.value)} placeholder="Add new operation type" className="min-h-11 flex-1 rounded border border-clinic-line px-3" />
                    <button type="button" onClick={addType} className="rounded border border-clinic-line px-3 font-semibold">Add</button>
                  </div>
                  <label>
                    <span className="text-sm font-semibold">Operation Date</span>
                    <input type="date" value={form.operation_date} onChange={(event) => setForm((current) => ({ ...current, operation_date: event.target.value }))} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
                  </label>
                  <label>
                    <span className="text-sm font-semibold">Remarks</span>
                    <textarea value={form.remarks ?? ""} onChange={(event) => setForm((current) => ({ ...current, remarks: event.target.value }))} rows={3} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
                  </label>
                </div>
                <button disabled={saving} className="mt-4 min-h-11 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">Create Operation</button>
              </form>
            ) : null}

            <div className="rounded border border-clinic-line bg-white shadow-soft">
              <div className="border-b border-clinic-line px-4 py-3">
                <h2 className="font-semibold">Operation List</h2>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  <label>
                    <span className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Surgery Status</span>
                    <select value={surgeryFilter} onChange={(event) => setSurgeryFilter(event.target.value as typeof surgeryFilter)} className="mt-1 min-h-10 w-full rounded border border-clinic-line px-3 text-sm">
                      <option value="all">All</option>
                      <option value="ready">Ready</option>
                      <option value="not_ready">Not Ready</option>
                      <option value="completed">Completed</option>
                    </select>
                  </label>
                  <label>
                    <span className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Payment Status</span>
                    <select value={paymentFilter} onChange={(event) => setPaymentFilter(event.target.value as typeof paymentFilter)} className="mt-1 min-h-10 w-full rounded border border-clinic-line px-3 text-sm">
                      <option value="all">All</option>
                      <option value="paid">Paid</option>
                      <option value="not_paid">Not Paid</option>
                    </select>
                  </label>
                  <label>
                    <span className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">Operation Date</span>
                    <input type="date" value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} className="mt-1 min-h-10 w-full rounded border border-clinic-line px-3 text-sm" />
                  </label>
                </div>
              </div>
              <div className="divide-y divide-clinic-line">
                {filteredOperations.map((operation) => (
                  <Link key={operation.id} href={`/operations/${operation.id}`} className="block px-4 py-3 hover:bg-clinic-wash">
                    <p className="font-semibold">{patientName(operation.patient)} - {operation.operation_type?.name}</p>
                    <p className="text-sm text-clinic-muted">{formatDate(operation.operation_date)} - {operation.status === "completed" ? "Completed" : operation.ready_for_surgery ? "Ready for Surgery" : "Not Ready"} - {operation.payment_status === "paid" ? "Paid" : "Not paid"}</p>
                  </Link>
                ))}
                {filteredOperations.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No operations match the selected filters.</p> : null}
              </div>
            </div>

            {me?.role !== "receptionist" ? (
              <div className="rounded border border-clinic-line bg-white shadow-soft xl:col-span-2">
                <div className="border-b border-clinic-line px-4 py-3"><h2 className="font-semibold">Manage Operation Types</h2></div>
                <div className="divide-y divide-clinic-line">
                  {types.map((type) => (
                    <div key={type.id} className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-semibold text-clinic-ink">{type.name}</p>
                        <p className="text-sm text-clinic-muted">Rs. {Number(type.price ?? 0).toFixed(2)}</p>
                      </div>
                      <button disabled={saving} onClick={() => archiveType(type)} className="min-h-10 rounded border border-red-200 px-3 text-sm font-semibold text-red-700 disabled:opacity-60">
                        Archive / Delete
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: number; onChange: (value: number) => void; options: Array<{ value: number; label: string }> }) {
  return (
    <label>
      <span className="text-sm font-semibold">{label}</span>
      <select value={value || ""} onChange={(event) => onChange(Number(event.target.value))} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3">
        <option value="">Select</option>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </label>
  );
}
