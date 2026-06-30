"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDateTime, patientName } from "@/lib/format";
import type { Patient, User, Visit } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<User | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const currentUser = await api.me();
        const patientList = await api.patients();
        let visitList: Visit[] = [];
        if (currentUser.role !== "receptionist") {
          visitList = await api.visits();
        }
        if (!active) return;
        setMe(currentUser);
        setPatients(patientList);
        setVisits(visitList);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          router.replace("/login");
          return;
        }
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load dashboard");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [router]);

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-2xl font-semibold text-clinic-ink">Dashboard</h1>
            <p className="text-sm text-clinic-muted">{me ? `${me.full_name} · ${me.role}` : "Clinic overview"}</p>
          </div>
          <Link href="/consultations/new" className="min-h-11 rounded bg-clinic-teal px-4 py-2 text-center text-sm font-semibold text-white">
            New Consultation
          </Link>
        </div>

        {loading ? <LoadingState label="Loading dashboard" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && !error ? (
          <>
            <section className="grid gap-4 md:grid-cols-3">
              <Metric label="Patients" value={patients.length} />
              <Metric label="Consultations" value={visits.length} />
              <Metric label="Active Session" value={me?.role ?? "-"} />
            </section>

            <section className="grid gap-5 lg:grid-cols-[1fr_1.4fr]">
              <div className="rounded border border-clinic-line bg-white shadow-soft">
                <div className="border-b border-clinic-line px-4 py-3">
                  <h2 className="font-semibold text-clinic-ink">Recent Patients</h2>
                </div>
                <div className="divide-y divide-clinic-line">
                  {patients.slice(0, 6).map((patient) => (
                    <Link key={patient.id} href={`/patients/${patient.id}`} className="block px-4 py-3 hover:bg-clinic-wash">
                      <p className="font-semibold text-clinic-ink">{patientName(patient)}</p>
                      <p className="text-sm text-clinic-muted">{patient.patient_id} · {patient.phone ?? "No mobile"}</p>
                    </Link>
                  ))}
                </div>
              </div>

              <div className="rounded border border-clinic-line bg-white shadow-soft">
                <div className="border-b border-clinic-line px-4 py-3">
                  <h2 className="font-semibold text-clinic-ink">Recent Consultations</h2>
                </div>
                <div className="divide-y divide-clinic-line">
                  {visits.slice(0, 6).map((visit) => (
                    <Link key={visit.id} href={`/consultations/${visit.id}`} className="block px-4 py-3 hover:bg-clinic-wash">
                      <p className="font-semibold text-clinic-ink">{patientName(visit.patient)}</p>
                      <p className="text-sm text-clinic-muted">{formatDateTime(visit.visit_date)} · {visit.chief_complaint}</p>
                    </Link>
                  ))}
                  {visits.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No consultations available.</p> : null}
                </div>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-clinic-line bg-white p-4 shadow-soft">
      <p className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-clinic-ink">{value}</p>
    </div>
  );
}
