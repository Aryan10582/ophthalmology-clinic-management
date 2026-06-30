"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { formatDateTime, patientName } from "@/lib/format";
import type { Patient, User, Visit } from "@/lib/types";

export default function PatientDetailsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const patientId = Number(params.id);
  const [me, setMe] = useState<User | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const currentUser = await api.me();
        const patientData = await api.patient(patientId);
        let visitData: Visit[] = [];
        if (currentUser.role !== "receptionist") {
          visitData = await api.patientVisits(patientId);
        }
        if (!active) return;
        setMe(currentUser);
        setPatient(patientData);
        setVisits(visitData);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          router.replace("/login");
          return;
        }
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load patient");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [patientId, router]);

  return (
    <AppShell>
      {loading ? <LoadingState label="Loading patient" /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!loading && patient ? (
        <div className="space-y-5">
          <section className="rounded border border-clinic-line bg-white p-4 shadow-soft sm:p-5">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <h1 className="text-2xl font-semibold text-clinic-ink">{patientName(patient)}</h1>
                <p className="text-sm text-clinic-muted">{patient.patient_id}</p>
              </div>
              {me?.role !== "receptionist" ? (
                <Link href={`/consultations/new?patientId=${patient.id}`} className="min-h-11 rounded bg-clinic-teal px-4 py-2 text-center text-sm font-semibold text-white">
                  New Consultation
                </Link>
              ) : null}
            </div>
            <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Info label="Age" value={patient.age} />
              <Info label="Sex" value={patient.gender} />
              <Info label="Mobile Number" value={patient.phone ?? "-"} />
              <Info label="Address" value={patient.address ?? "-"} />
            </dl>
          </section>

          <section className="rounded border border-clinic-line bg-white shadow-soft">
            <div className="border-b border-clinic-line px-4 py-3">
              <h2 className="font-semibold text-clinic-ink">Consultations</h2>
            </div>
            <div className="divide-y divide-clinic-line">
              {visits.map((visit) => (
                <Link key={visit.id} href={`/consultations/${visit.id}`} className="block px-4 py-3 hover:bg-clinic-wash">
                  <p className="font-semibold text-clinic-ink">{formatDateTime(visit.visit_date)}</p>
                  <p className="text-sm text-clinic-muted">{visit.chief_complaint}</p>
                </Link>
              ))}
              {visits.length === 0 ? <p className="px-4 py-5 text-sm text-clinic-muted">No consultations available.</p> : null}
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}

function Info({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">{label}</dt>
      <dd className="mt-1 font-semibold text-clinic-ink">{value}</dd>
    </div>
  );
}
