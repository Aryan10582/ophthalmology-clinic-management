"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ConsultationView } from "@/components/ConsultationView";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import type { Visit } from "@/lib/types";

export default function ConsultationDetailsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [visit, setVisit] = useState<Visit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        await api.me();
        const data = await api.visit(Number(params.id));
        if (active) setVisit(data);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          router.replace("/login");
          return;
        }
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load consultation");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [params.id, router]);

  return (
    <AppShell>
      {loading ? <LoadingState label="Loading consultation" /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!loading && visit ? <ConsultationView visit={visit} /> : null}
    </AppShell>
  );
}
