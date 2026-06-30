"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, getAccessToken, subscribeRealtime } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDate, patientName } from "@/lib/format";
import type { Operation, OperationTest, OperationTestReport, PaymentMethod, PaymentStatus, User } from "@/lib/types";

const checklist = ["CBC", "Blood Sugar (Fasting)", "Blood Sugar (Post Prandial)", "Urine Routine", "HIV", "HBsAg", "ECG", "Physician Fitness"];

export default function OperationDetailsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [me, setMe] = useState<User | null>(null);
  const [operation, setOperation] = useState<Operation | null>(null);
  const [otherTest, setOtherTest] = useState("");
  const [uploadingTestId, setUploadingTestId] = useState<number | null>(null);
  const [confirmingPaymentChange, setConfirmingPaymentChange] = useState(false);
  const [editingPayment, setEditingPayment] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const currentUser = await api.me();
      setMe(currentUser);
      setOperation(await api.operation(Number(params.id)));
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        router.replace("/login");
        return;
      }
      setError(loadError instanceof Error ? loadError.message : "Unable to load operation");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [params.id]);

  useEffect(() => {
    return subscribeRealtime((event) => {
      if (["operations.updated", "payments.updated", "reports.updated"].includes(event.type)) {
        load();
      }
    });
  }, [params.id]);

  const canEditClinical = me?.role === "admin" || me?.role === "doctor";

  async function updateTest(test: OperationTest, patch: Partial<OperationTest>) {
    setSaving(true);
    setError("");
    try {
      await api.updateOperationTest(test.id, patch);
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to update test");
    } finally {
      setSaving(false);
    }
  }

  async function toggleChecklist(test: OperationTest) {
    if (!canEditClinical) return;
    if (test.test_name === "Physician Fitness") {
      await updateTest(test, { fitness_status: test.fitness_status === "fit" ? "pending" : "fit", status: "done" });
      return;
    }
    await updateTest(test, { status: test.status === "done" ? "pending" : "done" });
  }

  async function addOtherTest() {
    if (!otherTest.trim() || !operation || !canEditClinical) return;
    setSaving(true);
    setError("");
    try {
      await api.addOperationTest(operation.id, { test_name: otherTest.trim() });
      setOtherTest("");
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to add test");
    } finally {
      setSaving(false);
    }
  }

  async function uploadReport(test: OperationTest, file?: File) {
    if (!file) return;
    setUploadingTestId(test.id);
    setError("");
    try {
      await api.uploadOperationReport(test.id, file);
      await load();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Unable to upload report");
    } finally {
      setUploadingTestId(null);
    }
  }

  async function deleteReport(report: OperationTestReport) {
    setSaving(true);
    setError("");
    try {
      await api.deleteOperationReport(report.id);
      await load();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete report");
    } finally {
      setSaving(false);
    }
  }

  async function openReport(report: OperationTestReport, download = false) {
    const response = await fetch(api.operationReportUrl(report.id), {
      headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` }
    });
    if (!response.ok) {
      setError("Unable to open report");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    if (download) {
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = report.original_filename;
      anchor.click();
      URL.revokeObjectURL(url);
      return;
    }
    window.open(url, "_blank", "noopener,noreferrer");
  }

  async function updatePayment(payment_status: PaymentStatus, payment_method?: PaymentMethod | null) {
    if (!operation) return;
    setSaving(true);
    setError("");
    try {
      setOperation(await api.updateOperationPayment(operation.id, { payment_status, payment_method: payment_status === "paid" ? payment_method ?? "cash" : null }));
      setConfirmingPaymentChange(false);
      setEditingPayment(false);
    } catch (paymentError) {
      setError(paymentError instanceof Error ? paymentError.message : "Unable to update payment");
    } finally {
      setSaving(false);
    }
  }

  async function deleteOperation() {
    if (!operation || !canEditClinical) return;
    const confirmed = window.confirm("Delete this operation record? Reports and checklists linked to this operation will also be removed.");
    if (!confirmed) return;
    setSaving(true);
    setError("");
    try {
      await api.deleteOperation(operation.id);
      router.replace("/operations");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete operation");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      {loading ? <LoadingState label="Loading operation" /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!loading && operation ? (
        <div className="space-y-5">
          <section className="rounded border border-clinic-line bg-white p-4 shadow-soft">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-2xl font-semibold">{operation.operation_type?.name}</h1>
                <p className="text-sm text-clinic-muted">{patientName(operation.patient)} - {formatDate(operation.operation_date)}</p>
                <p className="mt-1 text-sm text-clinic-muted">Charge: Rs. {Number(operation.operation_charge ?? operation.operation_type?.price ?? 0).toFixed(2)}</p>
              </div>
              <span className={`rounded px-3 py-2 text-sm font-semibold ${operation.ready_for_surgery ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-900"}`}>
                {operation.ready_for_surgery ? "Ready for Surgery" : "Not Ready"}
              </span>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm text-clinic-muted">{operation.remarks || "No remarks"}</p>
            {canEditClinical ? (
              <button type="button" disabled={saving} onClick={deleteOperation} className="mt-4 min-h-10 rounded border border-red-200 px-3 text-sm font-semibold text-red-700 disabled:opacity-60">
                Delete Operation
              </button>
            ) : null}
          </section>

          <section className="rounded border border-clinic-line bg-white p-4 shadow-soft">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-semibold text-clinic-ink">Operation Payment</h2>
                <p className="text-sm text-clinic-muted">{operation.payment_status === "paid" ? `Paid by ${operation.payment_method?.replace("_", " ")}` : "Not paid"}</p>
              </div>
              <OperationPaymentActions
                operation={operation}
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

          <section className="rounded border border-clinic-line bg-white shadow-soft">
            <div className="border-b border-clinic-line px-4 py-3"><h2 className="font-semibold">Pre-operative Checklist</h2></div>
            <div className="grid gap-2 p-4 sm:grid-cols-2 lg:grid-cols-4">
              {checklist.map((name) => {
                const test = operation.tests.find((item) => item.test_name === name);
                const done = name === "Physician Fitness" ? test?.fitness_status === "fit" : test?.status === "done";
                return (
                  <button
                    key={name}
                    disabled={!test || !canEditClinical || saving}
                    onClick={() => test ? toggleChecklist(test) : undefined}
                    className={`min-h-11 rounded border px-3 py-2 text-left text-sm font-semibold disabled:cursor-default ${done ? "border-green-200 bg-green-50 text-green-800" : "border-yellow-200 bg-yellow-50 text-yellow-900"}`}
                  >
                    {name}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="rounded border border-clinic-line bg-white shadow-soft">
            <div className="border-b border-clinic-line px-4 py-3"><h2 className="font-semibold">Reports</h2></div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left">
                <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
                  <tr>
                    <th className="px-4 py-3">Test</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Reports</th>
                    <th className="px-4 py-3">Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {operation.tests.map((test) => (
                    <tr key={test.id} className="border-t border-clinic-line align-top">
                      <td className="px-4 py-3 font-semibold">{test.test_name}</td>
                      <td className="px-4 py-3">
                        {canEditClinical ? (
                          <button
                            type="button"
                            disabled={saving}
                            onClick={() => toggleChecklist(test)}
                            className={`min-h-10 rounded px-3 text-sm font-semibold disabled:opacity-60 ${((test.test_name === "Physician Fitness" ? test.fitness_status === "fit" : test.status === "done")) ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-900"}`}
                          >
                            {test.test_name === "Physician Fitness" ? (test.fitness_status === "fit" ? "Fit" : "Pending") : test.status === "done" ? "Done" : "Pending"}
                          </button>
                        ) : (
                          <span className="capitalize">{test.test_name === "Physician Fitness" ? (test.fitness_status ?? "pending").replace("_", " ") : test.status}</span>
                        )}
                      </td>
                      <td className="space-y-2 px-4 py-3">
                        <input
                          type="file"
                          accept="image/*,application/pdf"
                          disabled={uploadingTestId === test.id}
                          onChange={(event) => uploadReport(test, event.target.files?.[0])}
                          className="block w-full text-sm"
                        />
                        {test.reports.map((report) => (
                          <div key={report.id} className="flex flex-wrap items-center gap-2 rounded border border-clinic-line px-2 py-2 text-sm">
                            <span className="font-semibold text-clinic-ink">{report.original_filename}</span>
                            <button type="button" onClick={() => openReport(report)} className="rounded border border-clinic-line px-2 py-1 font-semibold">Preview</button>
                            <button type="button" onClick={() => openReport(report, true)} className="rounded border border-clinic-line px-2 py-1 font-semibold">Download</button>
                            <button type="button" disabled={saving} onClick={() => deleteReport(report)} className="rounded border border-red-200 px-2 py-1 font-semibold text-red-700 disabled:opacity-60">Delete</button>
                          </div>
                        ))}
                      </td>
                      <td className="px-4 py-3">
                        {canEditClinical ? (
                          <textarea value={test.remarks ?? ""} onChange={(event) => updateTest(test, { remarks: event.target.value })} rows={2} className="w-full rounded border border-clinic-line px-2 py-2" />
                        ) : (
                          <span className="text-sm text-clinic-muted">{test.remarks || "-"}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {canEditClinical ? (
              <div className="flex gap-2 border-t border-clinic-line p-4">
                <input value={otherTest} onChange={(event) => setOtherTest(event.target.value)} placeholder="Add other test" className="min-h-11 flex-1 rounded border border-clinic-line px-3" />
                <button onClick={addOtherTest} disabled={saving} className="rounded bg-clinic-teal px-4 font-semibold text-white disabled:opacity-60">Add</button>
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}

function OperationPaymentActions({
  operation,
  saving,
  editing,
  confirming,
  onChange,
  onRequestChange,
  onCancelChange,
  onConfirmChange
}: {
  operation: Operation;
  saving: boolean;
  editing: boolean;
  confirming: boolean;
  onChange: (paymentStatus: PaymentStatus, paymentMethod?: PaymentMethod | null) => void;
  onRequestChange: () => void;
  onCancelChange: () => void;
  onConfirmChange: () => void;
}) {
  const paidLabel = operation.payment_method === "upi_qr" ? "UPI" : "Cash";
  if (operation.payment_status === "paid" && !editing) {
    return (
      <div className="flex flex-col gap-2 sm:items-end">
        <span className="rounded bg-green-100 px-3 py-2 text-sm font-semibold text-green-800">✓ Paid ({paidLabel})</span>
        {confirming ? (
          <div className="rounded border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-950">
            <p className="font-semibold">Change Payment Status?</p>
            <p className="mt-1">This operation has already been marked as paid.</p>
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
