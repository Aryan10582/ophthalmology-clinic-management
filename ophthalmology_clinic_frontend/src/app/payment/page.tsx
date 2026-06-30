"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, getAccessToken, subscribeRealtime } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import type { AnalyticsSummary, Expense, ExpensePayload, OperationType, PaymentSetting } from "@/lib/types";

const CONSULTATION_FEE_KEY = "consultation_fee";

const emptyExpense: ExpensePayload = {
  expense_name: "",
  category: "Medical Supplies",
  amount: 0,
  expense_date: new Date().toISOString().slice(0, 10),
  notes: ""
};

export default function PaymentPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<PaymentSetting[]>([]);
  const [types, setTypes] = useState<OperationType[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [consultationFee, setConsultationFee] = useState("");
  const [prices, setPrices] = useState<Record<number, string>>({});
  const [expenseForm, setExpenseForm] = useState<ExpensePayload>(emptyExpense);
  const [expenseQuery, setExpenseQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const currentUser = await api.me();
      if (!["admin", "doctor"].includes(currentUser.role)) {
        router.replace("/dashboard");
        return;
      }
      const expenseSearch = new URLSearchParams();
      if (expenseQuery.trim()) expenseSearch.set("search", expenseQuery.trim());
      if (categoryFilter) expenseSearch.set("category", categoryFilter);
      const expensePath = expenseSearch.toString() ? `?${expenseSearch.toString()}` : "";
      const [settingList, operationTypes, analytics, expenseList, categoryList] = await Promise.all([
        api.paymentSettings(),
        api.operationTypes(),
        api.analyticsSummary(),
        api.expenses(expensePath),
        api.expenseCategories()
      ]);
      setSettings(settingList);
      setTypes(operationTypes);
      setSummary(analytics);
      setExpenses(expenseList);
      setCategories(categoryList);
      setConsultationFee(String(settingList.find((item) => item.setting_key === CONSULTATION_FEE_KEY)?.amount ?? 0));
      setPrices(Object.fromEntries(operationTypes.map((type) => [type.id, String(type.price ?? 0)])));
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        router.replace("/login");
        return;
      }
      if (loadError instanceof ApiError && loadError.status === 403) {
        router.replace("/dashboard");
        return;
      }
      setError(loadError instanceof Error ? loadError.message : "Unable to load analytics and finance");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [expenseQuery, categoryFilter]);

  useEffect(() => {
    return subscribeRealtime((event) => {
      if (["finance.updated", "payments.updated", "operations.updated", "consultations.completed"].includes(event.type)) {
        load();
      }
    });
  }, []);

  async function saveConsultationFee(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.updatePaymentSetting(CONSULTATION_FEE_KEY, Number(consultationFee));
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save consultation fee");
    } finally {
      setSaving(false);
    }
  }

  async function saveOperationPrice(type: OperationType) {
    setSaving(true);
    setError("");
    try {
      await api.updateOperationTypePrice(type.id, Number(prices[type.id] ?? 0));
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save operation price");
    } finally {
      setSaving(false);
    }
  }

  async function createExpense(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createExpense({ ...expenseForm, amount: Number(expenseForm.amount), notes: expenseForm.notes || null });
      setExpenseForm(emptyExpense);
      await load();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to record expense");
    } finally {
      setSaving(false);
    }
  }

  async function deleteExpense(expense: Expense) {
    setSaving(true);
    setError("");
    try {
      await api.deleteExpense(expense.id);
      await load();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete expense");
    } finally {
      setSaving(false);
    }
  }

  async function downloadReport() {
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(new Date().setMonth(new Date().getMonth() - 11)).toISOString().slice(0, 10);
    const response = await fetch(api.financialReportUrl(start, end), {
      headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` }
    });
    if (!response.ok) {
      setError("Unable to export financial report");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `financial-report-${start}-to-${end}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const maxTrendValue = useMemo(() => {
    if (!summary) return 1;
    return Math.max(...summary.monthly_trends.map((item) => Number(item.total_revenue) + Number(item.expenses)), 1);
  }, [summary]);

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-2xl font-semibold text-clinic-ink">Analytics & Finance</h1>
            <p className="text-sm text-clinic-muted">Doctor-only revenue, expenses, profit and clinic analytics.</p>
          </div>
          <button onClick={downloadReport} className="min-h-11 rounded border border-clinic-line bg-white px-4 py-2 font-semibold text-clinic-ink">
            Export Report
          </button>
        </div>

        {loading ? <LoadingState label="Loading analytics" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && summary ? (
          <>
            <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <FinanceMetric label="Today's Profit" value={summary.finance.today.net_profit} />
              <FinanceMetric label="Weekly Profit" value={summary.finance.week.net_profit} />
              <FinanceMetric label="Monthly Profit" value={summary.finance.month.net_profit} />
              <FinanceMetric label="Yearly Profit" value={summary.finance.year.net_profit} />
            </section>

            <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <FinanceMetric label="Today's Revenue" value={summary.finance.today.total_revenue} muted={`Expenses Rs. ${money(summary.finance.today.total_expenses)}`} />
              <FinanceMetric label="Weekly Revenue" value={summary.finance.week.total_revenue} muted={`Expenses Rs. ${money(summary.finance.week.total_expenses)}`} />
              <FinanceMetric label="Monthly Revenue" value={summary.finance.month.total_revenue} muted={`Expenses Rs. ${money(summary.finance.month.total_expenses)}`} />
              <FinanceMetric label="Yearly Revenue" value={summary.finance.year.total_revenue} muted={`Expenses Rs. ${money(summary.finance.year.total_expenses)}`} />
            </section>

            <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
              <div className="rounded border border-clinic-line bg-white p-4 shadow-soft">
                <h2 className="font-semibold text-clinic-ink">Revenue vs Expense Trend</h2>
                <div className="mt-4 space-y-3">
                  {summary.monthly_trends.map((item) => (
                    <div key={item.month} className="grid grid-cols-[70px_1fr] items-center gap-3">
                      <span className="text-sm font-semibold text-clinic-muted">{item.month.slice(5)}</span>
                      <div className="space-y-1">
                        <Bar label="Revenue" value={Number(item.total_revenue)} max={maxTrendValue} className="bg-clinic-teal" />
                        <Bar label="Expenses" value={Number(item.expenses)} max={maxTrendValue} className="bg-rose-500" />
                        <Bar label="Profit" value={Math.max(Number(item.profit), 0)} max={maxTrendValue} className="bg-emerald-500" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded border border-clinic-line bg-white p-4 shadow-soft">
                <h2 className="font-semibold text-clinic-ink">Clinic Analytics</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <MiniMetric label="Daily Consultations" value={summary.consultations.daily_consultations} />
                  <MiniMetric label="Weekly Consultations" value={summary.consultations.weekly_consultations} />
                  <MiniMetric label="Monthly Consultations" value={summary.consultations.monthly_consultations} />
                  <MiniMetric label="Total Consultations" value={summary.consultations.total_consultations} />
                  <MiniMetric label="New Patients" value={summary.patients.new_patients} />
                  <MiniMetric label="Returning Patients" value={summary.patients.returning_patients} />
                  <MiniMetric label="Avg Consults / Day" value={summary.patients.average_consultations_per_day} />
                  <MiniMetric label="Avg Ops / Month" value={summary.patients.average_operations_per_month} />
                </div>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-2">
              <SettingsPanel
                settings={settings}
                types={types}
                consultationFee={consultationFee}
                prices={prices}
                saving={saving}
                onFee={setConsultationFee}
                onPrice={(id, value) => setPrices((current) => ({ ...current, [id]: value }))}
                onSaveFee={saveConsultationFee}
                onSavePrice={saveOperationPrice}
              />

              <div className="rounded border border-clinic-line bg-white shadow-soft">
                <div className="border-b border-clinic-line px-4 py-3">
                  <h2 className="font-semibold text-clinic-ink">Operation Analytics</h2>
                </div>
                <div className="divide-y divide-clinic-line">
                  {summary.operation_types.map((item) => (
                    <div key={item.operation_type} className="px-4 py-3">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-clinic-ink">{item.operation_type}</p>
                        <p className="text-sm font-semibold">{item.total_count} ({item.percentage.toFixed(1)}%)</p>
                      </div>
                      <div className="mt-2 h-2 rounded bg-clinic-wash">
                        <div className="h-2 rounded bg-clinic-teal" style={{ width: `${Math.min(item.percentage, 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
              <form onSubmit={createExpense} className="rounded border border-clinic-line bg-white p-4 shadow-soft">
                <h2 className="font-semibold text-clinic-ink">Record Expense</h2>
                <div className="mt-4 grid gap-3">
                  <Input label="Expense Name" value={expenseForm.expense_name} onChange={(value) => setExpenseForm((current) => ({ ...current, expense_name: value }))} />
                  <label>
                    <span className="text-sm font-semibold">Category</span>
                    <input list="expense-categories" value={expenseForm.category} onChange={(event) => setExpenseForm((current) => ({ ...current, category: event.target.value }))} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
                    <datalist id="expense-categories">
                      {categories.map((category) => <option key={category} value={category} />)}
                    </datalist>
                  </label>
                  <Input label="Amount" type="number" value={String(expenseForm.amount)} onChange={(value) => setExpenseForm((current) => ({ ...current, amount: Number(value) }))} />
                  <Input label="Date" type="date" value={expenseForm.expense_date} onChange={(value) => setExpenseForm((current) => ({ ...current, expense_date: value }))} />
                  <label>
                    <span className="text-sm font-semibold">Notes</span>
                    <textarea value={expenseForm.notes ?? ""} onChange={(event) => setExpenseForm((current) => ({ ...current, notes: event.target.value }))} rows={3} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
                  </label>
                </div>
                <button disabled={saving} className="mt-4 min-h-11 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
                  Add Expense
                </button>
              </form>

              <div className="rounded border border-clinic-line bg-white shadow-soft">
                <div className="grid gap-3 border-b border-clinic-line px-4 py-3 md:grid-cols-[1fr_220px]">
                  <input value={expenseQuery} onChange={(event) => setExpenseQuery(event.target.value)} placeholder="Search expenses" className="min-h-11 rounded border border-clinic-line px-3" />
                  <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)} className="min-h-11 rounded border border-clinic-line px-3">
                    <option value="">All categories</option>
                    {categories.map((category) => <option key={category} value={category}>{category}</option>)}
                  </select>
                </div>
                <div className="divide-y divide-clinic-line">
                  {expenses.map((expense) => (
                    <div key={expense.id} className="grid gap-3 px-4 py-3 md:grid-cols-[1fr_auto_auto] md:items-center">
                      <div>
                        <p className="font-semibold text-clinic-ink">{expense.expense_name}</p>
                        <p className="text-sm text-clinic-muted">{expense.category} - {expense.expense_date}</p>
                      </div>
                      <p className="font-semibold">Rs. {money(expense.amount)}</p>
                      <button disabled={saving} onClick={() => deleteExpense(expense)} className="min-h-10 rounded border border-red-200 px-3 text-sm font-semibold text-red-700 disabled:opacity-60">
                        Delete
                      </button>
                    </div>
                  ))}
                  {expenses.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No expenses found.</p> : null}
                </div>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

function money(value: string | number) {
  return Number(value ?? 0).toFixed(2);
}

function FinanceMetric({ label, value, muted }: { label: string; value: string | number; muted?: string }) {
  return (
    <div className="rounded border border-clinic-line bg-white p-4 shadow-soft">
      <p className="text-sm font-semibold text-clinic-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-clinic-ink">Rs. {money(value)}</p>
      {muted ? <p className="mt-1 text-xs text-clinic-muted">{muted}</p> : null}
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-clinic-line bg-clinic-wash p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">{label}</p>
      <p className="mt-1 text-xl font-semibold text-clinic-ink">{value}</p>
    </div>
  );
}

function Bar({ label, value, max, className }: { label: string; value: number; max: number; className: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 text-xs text-clinic-muted">{label}</span>
      <div className="h-2 flex-1 rounded bg-clinic-wash">
        <div className={`h-2 rounded ${className}`} style={{ width: `${Math.max(3, Math.min((value / max) * 100, 100))}%` }} />
      </div>
      <span className="w-20 text-right text-xs font-semibold">Rs. {money(value)}</span>
    </div>
  );
}

function SettingsPanel({
  types,
  consultationFee,
  prices,
  saving,
  onFee,
  onPrice,
  onSaveFee,
  onSavePrice
}: {
  settings: PaymentSetting[];
  types: OperationType[];
  consultationFee: string;
  prices: Record<number, string>;
  saving: boolean;
  onFee: (value: string) => void;
  onPrice: (id: number, value: string) => void;
  onSaveFee: (event: React.FormEvent<HTMLFormElement>) => void;
  onSavePrice: (type: OperationType) => void;
}) {
  return (
    <div className="rounded border border-clinic-line bg-white shadow-soft">
      <form onSubmit={onSaveFee} className="border-b border-clinic-line p-4">
        <h2 className="font-semibold text-clinic-ink">Charges</h2>
        <label className="mt-3 block">
          <span className="text-sm font-semibold text-clinic-muted">Consultation Fee</span>
          <input type="number" min={0} step="0.01" value={consultationFee} onChange={(event) => onFee(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
        </label>
        <button disabled={saving} className="mt-3 min-h-10 rounded bg-clinic-teal px-4 font-semibold text-white disabled:opacity-60">Save Fee</button>
      </form>
      <div className="divide-y divide-clinic-line">
        {types.map((type) => (
          <div key={type.id} className="grid gap-3 px-4 py-3 sm:grid-cols-[1fr_150px_auto] sm:items-center">
            <p className="font-semibold text-clinic-ink">{type.name}</p>
            <input type="number" min={0} step="0.01" value={prices[type.id] ?? ""} onChange={(event) => onPrice(type.id, event.target.value)} className="min-h-10 rounded border border-clinic-line px-3" />
            <button disabled={saving} onClick={() => onSavePrice(type)} className="min-h-10 rounded border border-clinic-line px-3 font-semibold disabled:opacity-60">Save</button>
          </div>
        ))}
      </div>
    </div>
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
