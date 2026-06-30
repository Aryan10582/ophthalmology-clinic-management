import { AppShell } from "@/components/AppShell";
import { ConsultationForm } from "@/components/ConsultationForm";

export default function EditConsultationPage({ params }: { params: { id: string } }) {
  return (
    <AppShell>
      <ConsultationForm mode="edit" visitId={Number(params.id)} />
    </AppShell>
  );
}
