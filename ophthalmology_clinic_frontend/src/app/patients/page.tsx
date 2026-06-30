"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { patientName } from "@/lib/format";
import type { Patient } from "@/lib/types";

export default function PatientsPage() {
  const router = useRouter();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        await api.me();
        const data = await api.patients();
        const sorted = [...data].sort((a, b) => {
          const left = new Date(a.last_visit_at ?? a.created_at).getTime();
          const right = new Date(b.last_visit_at ?? b.created_at).getTime();
          return right - left;
        });
        if (active) setPatients(sorted);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          router.replace("/login");
          return;
        }
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load patients");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [router]);

  const filtered = useMemo(() => {
    const term = query.toLowerCase().trim();
    if (!term) return patients;
    return patients.filter((patient) =>
      [patientName(patient), patient.patient_id, patient.phone ?? ""].some((value) => value.toLowerCase().includes(term))
    );
  }, [patients, query]);

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
          <div>
            <h1 className="text-2xl font-semibold text-clinic-ink">Patient List</h1>
            <p className="text-sm text-clinic-muted">{filtered.length} patient records</p>
          </div>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search patients"
            className="min-h-12 w-full rounded border border-clinic-line bg-white px-3 text-base md:max-w-sm"
          />
        </div>

        {loading ? <LoadingState label="Loading patients" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && !error ? (
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((patient) => (
              <Link key={patient.id} href={`/patients/${patient.id}`} className="rounded border border-clinic-line bg-white p-4 shadow-soft hover:border-clinic-teal">
                <p className="text-lg font-semibold text-clinic-ink">{patientName(patient)}</p>
                <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="font-semibold text-clinic-muted">Patient ID</dt>
                    <dd>{patient.patient_id}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-clinic-muted">Mobile</dt>
                    <dd>{patient.phone ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-clinic-muted">Age</dt>
                    <dd>{patient.age}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-clinic-muted">Sex</dt>
                    <dd>{patient.gender}</dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="font-semibold text-clinic-muted">Last Visit</dt>
                    <dd>{patient.last_visit_at ? new Date(patient.last_visit_at).toLocaleString() : "No completed visit"}</dd>
                  </div>
                </dl>
              </Link>
            ))}
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}
