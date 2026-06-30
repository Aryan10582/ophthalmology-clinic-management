"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDate } from "@/lib/format";
import type { CalendarEvent } from "@/lib/types";

const colorClass: Record<string, string> = {
  red: "border-red-200 bg-red-50 text-red-800",
  green: "border-green-200 bg-green-50 text-green-800",
  yellow: "border-yellow-200 bg-yellow-50 text-yellow-900",
  blue: "border-blue-200 bg-blue-50 text-blue-800"
};

const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function CalendarPage() {
  const router = useRouter();
  const [filter, setFilter] = useState("all");
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [month, setMonth] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        await api.me();
        const data = await api.calendarEvents(filter);
        if (active) setEvents(data);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          router.replace("/login");
          return;
        }
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load calendar");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [filter, router]);

  const eventsByDate = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const key = event.date.slice(0, 10);
      map.set(key, [...(map.get(key) ?? []), event]);
    }
    return map;
  }, [events]);

  const days = useMemo(() => calendarDays(month), [month]);
  const selectedEvents = eventsByDate.get(selectedDate) ?? [];

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-2xl font-semibold">Calendar</h1>
            <p className="text-sm text-clinic-muted">Monthly operation and follow-up view</p>
          </div>
          <div className="flex gap-2 overflow-x-auto">
            {["all", "operations", "followups"].map((item) => (
              <button key={item} onClick={() => setFilter(item)} className={`min-h-11 rounded px-4 text-sm font-semibold capitalize ${filter === item ? "bg-clinic-teal text-white" : "bg-white text-clinic-ink"}`}>
                {item}
              </button>
            ))}
          </div>
        </div>

        {loading ? <LoadingState label="Loading calendar" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && !error ? (
          <section className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
            <div className="rounded border border-clinic-line bg-white shadow-soft">
              <div className="flex items-center justify-between border-b border-clinic-line px-4 py-3">
                <button onClick={() => setMonth(addMonths(month, -1))} className="min-h-10 rounded border border-clinic-line px-3 font-semibold">Prev</button>
                <h2 className="text-lg font-semibold text-clinic-ink">{month.toLocaleDateString(undefined, { month: "long", year: "numeric" })}</h2>
                <button onClick={() => setMonth(addMonths(month, 1))} className="min-h-10 rounded border border-clinic-line px-3 font-semibold">Next</button>
              </div>
              <div className="grid grid-cols-7 border-b border-clinic-line bg-clinic-wash text-center text-xs font-semibold uppercase tracking-wide text-clinic-muted">
                {weekdays.map((day) => <div key={day} className="px-2 py-3">{day}</div>)}
              </div>
              <div className="grid grid-cols-7">
                {days.map((day) => {
                  const key = toDateKey(day);
                  const dayEvents = eventsByDate.get(key) ?? [];
                  const inMonth = day.getMonth() === month.getMonth();
                  const selected = key === selectedDate;
                  return (
                    <button
                      key={key}
                      onClick={() => setSelectedDate(key)}
                      className={`min-h-24 border-b border-r border-clinic-line p-2 text-left transition ${selected ? "bg-clinic-mint" : "bg-white"} ${inMonth ? "" : "text-clinic-muted opacity-60"}`}
                    >
                      <span className="text-sm font-semibold">{day.getDate()}</span>
                      <div className="mt-2 space-y-1">
                        {dayEvents.slice(0, 2).map((event) => (
                          <span key={event.id} className={`block truncate rounded border px-2 py-1 text-xs font-semibold ${colorClass[event.color] ?? "border-clinic-line bg-clinic-wash text-clinic-ink"}`}>
                            {event.title}
                          </span>
                        ))}
                        {dayEvents.length > 2 ? <span className="block text-xs font-semibold text-clinic-muted">+{dayEvents.length - 2} more</span> : null}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <aside className="rounded border border-clinic-line bg-white shadow-soft">
              <div className="border-b border-clinic-line px-4 py-3">
                <h2 className="font-semibold text-clinic-ink">{formatDate(selectedDate)}</h2>
              </div>
              <div className="divide-y divide-clinic-line">
                {selectedEvents.map((event) => (
                  <article key={event.id} className="px-4 py-3">
                    <span className={`inline-block rounded border px-2 py-1 text-xs font-semibold ${colorClass[event.color] ?? "border-clinic-line bg-clinic-wash"}`}>
                      {event.category.replaceAll("_", " ")}
                    </span>
                    <h3 className="mt-2 font-semibold text-clinic-ink">{event.title}</h3>
                    <p className="text-sm text-clinic-muted">{event.patient_name}</p>
                  </article>
                ))}
                {selectedEvents.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No events on this date.</p> : null}
              </div>
            </aside>
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}

function startOfMonth(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), 1);
}

function addMonths(value: Date, months: number) {
  return new Date(value.getFullYear(), value.getMonth() + months, 1);
}

function toDateKey(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function calendarDays(month: Date) {
  const first = startOfMonth(month);
  const start = new Date(first);
  start.setDate(first.getDate() - first.getDay());
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}
