import { Suspense } from "react";
import { AppShell } from "@/components/AppShell";
import { ConsultationForm } from "@/components/ConsultationForm";
import { LoadingState } from "@/components/LoadingState";

export default function NewConsultationPage() {
  return (
    <AppShell>
      <Suspense fallback={<LoadingState label="Preparing consultation" />}>
        <ConsultationForm mode="create" />
      </Suspense>
    </AppShell>
  );
}
