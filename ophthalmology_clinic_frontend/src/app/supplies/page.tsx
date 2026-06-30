"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, subscribeRealtime } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDateTime } from "@/lib/format";
import type { MedicalSupply, MedicalSupplyBatchPayload, MedicalSupplyPayload, Notification, SupplyCategory, User } from "@/lib/types";

const categories: Array<{ value: SupplyCategory; label: string }> = [
  { value: "emergency", label: "Emergency" },
  { value: "operation", label: "Operation" },
  { value: "general", label: "General" }
];

const emptyForm: MedicalSupplyPayload = {
  category: "general",
  name: "",
  current_stock: 0,
  unit: "pcs",
  minimum_stock: 0,
  expiry_date: null,
  notes: ""
};

const emptyBatch: MedicalSupplyBatchPayload = {
  batch_code: "",
  quantity: 1,
  expiry_date: new Date().toISOString().slice(0, 10),
  purchase_date: new Date().toISOString().slice(0, 10),
  notes: ""
};

export default function SuppliesPage() {
  const router = useRouter();
  const [me, setMe] = useState<User | null>(null);
  const [supplies, setSupplies] = useState<MedicalSupply[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [form, setForm] = useState<MedicalSupplyPayload>(emptyForm);
  const [batchSupplyId, setBatchSupplyId] = useState<number | null>(null);
  const [batchForm, setBatchForm] = useState<MedicalSupplyBatchPayload>(emptyBatch);
  const [consumeDrafts, setConsumeDrafts] = useState<Record<number, string>>({});
  const [expiryFilter, setExpiryFilter] = useState<"all" | "expired" | "expiring_soon" | "safe">("all");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const currentUser = await api.me();
      const [supplyList, notificationList] = await Promise.all([api.supplies(), api.notifications()]);
      setMe(currentUser);
      setSupplies(supplyList);
      setNotifications(notificationList);
      setBatchSupplyId((current) => current ?? supplyList[0]?.id ?? null);
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        router.replace("/login");
        return;
      }
      setError(loadError instanceof Error ? loadError.message : "Unable to load medical supplies");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    return subscribeRealtime((event) => {
      if (event.type === "supplies.updated") {
        load();
      }
    });
  }, []);

  const grouped = useMemo(() => {
    const visibleSupplies = expiryFilter === "all" ? supplies : supplies.filter((supply) => supply.expiry_status === expiryFilter);
    return categories.map((category) => ({
      ...category,
      supplies: visibleSupplies.filter((supply) => supply.category === category.value)
    }));
  }, [expiryFilter, supplies]);

  async function createSupply(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createSupply({
        ...form,
        current_stock: 0,
        minimum_stock: Number(form.minimum_stock),
        notes: form.notes || null
      });
      setForm(emptyForm);
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to create supply");
    } finally {
      setSaving(false);
    }
  }

  async function addBatch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!batchSupplyId) return;
    setSaving(true);
    setError("");
    try {
      await api.addSupplyBatch(batchSupplyId, { ...batchForm, quantity: Number(batchForm.quantity), notes: batchForm.notes || null });
      setBatchForm(emptyBatch);
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to add batch");
    } finally {
      setSaving(false);
    }
  }

  async function consumeStock(supply: MedicalSupply) {
    const quantity = Number(consumeDrafts[supply.id] ?? 0);
    if (!quantity) return;
    setSaving(true);
    setError("");
    try {
      await api.consumeSupply(supply.id, quantity);
      setConsumeDrafts((current) => ({ ...current, [supply.id]: "" }));
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to consume stock");
    } finally {
      setSaving(false);
    }
  }

  async function deleteBatch(batchId: number, batchCode: string) {
    if (!window.confirm(`Delete inventory batch "${batchCode}"?\n\nOnly this batch will be removed and stock totals will be recalculated.`)) return;
    setSaving(true);
    setError("");
    try {
      await api.deleteSupplyBatch(batchId);
      await load();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete batch");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-2xl font-semibold text-clinic-ink">Medical Supplies</h1>
            <p className="text-sm text-clinic-muted">Emergency, operation and general stock with low-stock and expiry alerts.</p>
          </div>
          <select value={expiryFilter} onChange={(event) => setExpiryFilter(event.target.value as typeof expiryFilter)} className="min-h-11 rounded border border-clinic-line bg-white px-3">
            <option value="all">All expiry statuses</option>
            <option value="expired">Expired</option>
            <option value="expiring_soon">Expiring soon</option>
            <option value="safe">Safe</option>
          </select>
        </div>

        {loading ? <LoadingState label="Loading supplies" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading ? (
          <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-5">
              {grouped.map((group) => (
                <div key={group.value} className="rounded border border-clinic-line bg-white shadow-soft">
                  <div className="border-b border-clinic-line px-4 py-3">
                    <h2 className="font-semibold text-clinic-ink">{group.label}</h2>
                  </div>
                  <div className="divide-y divide-clinic-line">
                    {group.supplies.map((supply) => (
                      <div key={supply.id} className="space-y-3 px-4 py-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-semibold text-clinic-ink">{supply.name}</p>
                            {supply.is_low_stock ? <span className="rounded bg-red-100 px-2 py-1 text-xs font-semibold text-red-800">Low stock</span> : null}
                            {supply.expiry_status === "expired" ? <span className="rounded bg-red-100 px-2 py-1 text-xs font-semibold text-red-800">Expired</span> : null}
                            {supply.expiry_status === "expiring_soon" ? <span className="rounded bg-yellow-100 px-2 py-1 text-xs font-semibold text-yellow-900">Near expiry</span> : null}
                          </div>
                          <p className="text-sm text-clinic-muted">
                            Minimum {supply.minimum_stock} {supply.unit} - Updated {formatDateTime(supply.updated_at)}
                          </p>
                          <p className="text-sm text-clinic-muted">
                            Expiry: {supply.expiry_date ?? "Not tracked"} {typeof supply.days_to_expiry === "number" ? `(${supply.days_to_expiry} days)` : ""}
                          </p>
                          {supply.notes ? <p className="mt-1 text-sm text-clinic-muted">{supply.notes}</p> : null}
                        </div>
                        <div className="overflow-x-auto rounded border border-clinic-line">
                          <table className="w-full min-w-[560px] text-left text-sm">
                            <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
                              <tr><th className="px-3 py-2">Batch</th><th className="px-3 py-2">Remaining</th><th className="px-3 py-2">Purchased</th><th className="px-3 py-2">Expiry</th><th className="px-3 py-2">Status</th>{me?.role === "doctor" || me?.role === "admin" ? <th className="px-3 py-2">Action</th> : null}</tr>
                            </thead>
                            <tbody>
                              {supply.batches.map((batch) => (
                                <tr key={batch.id} className="border-t border-clinic-line">
                                  <td className="px-3 py-2 font-semibold">{batch.batch_code}</td>
                                  <td className="px-3 py-2">{batch.quantity_remaining} / {batch.quantity_initial} {supply.unit}</td>
                                  <td className="px-3 py-2">{batch.purchase_date}</td>
                                  <td className="px-3 py-2">{batch.expiry_date}</td>
                                  <td className="px-3 py-2 capitalize">{batch.expiry_status.replace("_", " ")}</td>
                                  {me?.role === "doctor" || me?.role === "admin" ? (
                                    <td className="px-3 py-2">
                                      <button type="button" disabled={saving} onClick={() => deleteBatch(batch.id, batch.batch_code)} className="min-h-9 rounded border border-red-200 px-2 text-xs font-semibold text-red-700 disabled:opacity-60">
                                        Delete
                                      </button>
                                    </td>
                                  ) : null}
                                </tr>
                              ))}
                              {supply.batches.length === 0 ? <tr><td colSpan={me?.role === "doctor" || me?.role === "admin" ? 6 : 5} className="px-3 py-3 text-clinic-muted">No batches yet. Add a purchase batch.</td></tr> : null}
                            </tbody>
                          </table>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <input type="number" min={1} placeholder="Consume qty" value={consumeDrafts[supply.id] ?? ""} onChange={(event) => setConsumeDrafts((current) => ({ ...current, [supply.id]: event.target.value }))} className="min-h-10 rounded border border-clinic-line px-3" />
                          <button disabled={saving} onClick={() => consumeStock(supply)} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">
                            Consume FEFO
                          </button>
                          <button type="button" onClick={() => setBatchSupplyId(supply.id)} className="min-h-10 rounded bg-clinic-teal px-3 text-sm font-semibold text-white">
                            Add New Batch
                          </button>
                        </div>
                      </div>
                    ))}
                    {group.supplies.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No supplies in this category.</p> : null}
                  </div>
                </div>
              ))}
            </div>

            <aside className="space-y-5">
              <form onSubmit={createSupply} className="rounded border border-clinic-line bg-white p-4 shadow-soft">
                <h2 className="font-semibold text-clinic-ink">Add Supply</h2>
                <div className="mt-4 grid gap-3">
                  <label>
                    <span className="text-sm font-semibold">Category</span>
                    <select value={form.category} onChange={(event) => setForm((current) => ({ ...current, category: event.target.value as SupplyCategory }))} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3">
                      {categories.map((category) => <option key={category.value} value={category.value}>{category.label}</option>)}
                    </select>
                  </label>
                  <Input label="Name" value={form.name} onChange={(value) => setForm((current) => ({ ...current, name: value }))} />
                  <Input label="Unit" value={form.unit} onChange={(value) => setForm((current) => ({ ...current, unit: value }))} />
                  <Input label="Minimum Stock" type="number" value={String(form.minimum_stock)} onChange={(value) => setForm((current) => ({ ...current, minimum_stock: Number(value) }))} />
                  <label>
                    <span className="text-sm font-semibold">Expiry Date</span>
                    <input type="date" value={form.expiry_date ?? ""} onChange={(event) => setForm((current) => ({ ...current, expiry_date: event.target.value || null }))} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
                  </label>
                  <label>
                    <span className="text-sm font-semibold">Notes</span>
                    <textarea value={form.notes ?? ""} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} rows={3} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
                  </label>
                </div>
                <button disabled={saving} className="mt-4 min-h-11 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
                  Add Supply
                </button>
              </form>

              <form onSubmit={addBatch} className="rounded border border-clinic-line bg-white p-4 shadow-soft">
                <h2 className="font-semibold text-clinic-ink">Add New Batch</h2>
                <label className="mt-4 block">
                  <span className="text-sm font-semibold">Supply</span>
                  <select value={batchSupplyId ?? ""} onChange={(event) => setBatchSupplyId(Number(event.target.value))} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3">
                    {supplies.map((supply) => <option key={supply.id} value={supply.id}>{supply.name}</option>)}
                  </select>
                </label>
                <div className="mt-4 grid gap-3">
                  <Input label="Batch ID" value={batchForm.batch_code} onChange={(value) => setBatchForm((current) => ({ ...current, batch_code: value }))} />
                  <Input label="Quantity" type="number" value={String(batchForm.quantity)} onChange={(value) => setBatchForm((current) => ({ ...current, quantity: Number(value) }))} />
                  <Input label="Purchase Date" type="date" value={batchForm.purchase_date} onChange={(value) => setBatchForm((current) => ({ ...current, purchase_date: value }))} />
                  <Input label="Expiry Date" type="date" value={batchForm.expiry_date} onChange={(value) => setBatchForm((current) => ({ ...current, expiry_date: value }))} />
                  <label>
                    <span className="text-sm font-semibold">Notes</span>
                    <textarea value={batchForm.notes ?? ""} onChange={(event) => setBatchForm((current) => ({ ...current, notes: event.target.value }))} rows={2} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
                  </label>
                </div>
                <button disabled={saving || !batchSupplyId} className="mt-4 min-h-11 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
                  Add Batch
                </button>
              </form>

              <div className="rounded border border-clinic-line bg-white shadow-soft">
                <div className="border-b border-clinic-line px-4 py-3">
                  <h2 className="font-semibold text-clinic-ink">Notifications</h2>
                </div>
                <div className="divide-y divide-clinic-line">
                  {notifications.map((notification) => (
                    <div key={notification.id} className="px-4 py-3">
                      <p className="font-semibold text-clinic-ink">{notification.title}</p>
                      <p className="text-sm text-clinic-muted">{notification.message}</p>
                      <p className="mt-1 text-xs text-clinic-muted">{formatDateTime(notification.created_at)}</p>
                    </div>
                  ))}
                  {notifications.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No notifications.</p> : null}
                </div>
              </div>
            </aside>
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}

function Input({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label>
      <span className="text-sm font-semibold">{label}</span>
      <input required type={type} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
    </label>
  );
}
