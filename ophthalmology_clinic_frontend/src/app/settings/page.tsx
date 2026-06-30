"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import type { PrescriptionTemplate } from "@/lib/types";

const templates = [
  ["professional_blue", "Professional Blue"],
  ["minimal_white", "Minimal White"]
];

export default function SettingsPage() {
  const router = useRouter();
  const [template, setTemplate] = useState<PrescriptionTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const me = await api.me();
        if (!["admin", "doctor"].includes(me.role)) {
          router.replace("/dashboard");
          return;
        }
        setTemplate(await api.prescriptionTemplate());
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) router.replace("/login");
        else setError(loadError instanceof Error ? loadError.message : "Unable to load settings");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [router]);

  function update<K extends keyof PrescriptionTemplate>(key: K, value: PrescriptionTemplate[K]) {
    setTemplate((current) => (current ? { ...current, [key]: value } : current));
  }

  function uploadImage(key: "clinic_logo" | "doctor_signature", file?: File) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => update(key, String(reader.result));
    reader.readAsDataURL(file);
  }

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!template) return;
    setSaving(true);
    setError("");
    try {
      setTemplate(await api.updatePrescriptionTemplate(template));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save template");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-semibold text-clinic-ink">Doctor Settings</h1>
          <p className="text-sm text-clinic-muted">Prescription pad details and clinic branding.</p>
        </div>
        {loading ? <LoadingState label="Loading settings" /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && template ? (
          <form onSubmit={save} className="grid gap-5 xl:grid-cols-[1fr_0.75fr]">
            <section className="rounded border border-clinic-line bg-white p-4 shadow-soft">
              <h2 className="font-semibold text-clinic-ink">Prescription Pad Setup</h2>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <Select label="Template" value={template.template_name} options={templates} onChange={(value) => update("template_name", value)} />
                <Input label="Doctor Name" value={template.doctor_name ?? ""} onChange={(value) => update("doctor_name", value)} />
                <Input label="Qualifications" value={template.doctor_qualifications ?? ""} onChange={(value) => update("doctor_qualifications", value)} />
                <Input label="Registration Number" value={template.doctor_registration_number ?? ""} onChange={(value) => update("doctor_registration_number", value)} />
                <Input label="Clinic Name" value={template.clinic_name ?? ""} onChange={(value) => update("clinic_name", value)} />
                <Input label="Clinic Phone Number" value={template.clinic_phone ?? ""} onChange={(value) => update("clinic_phone", value)} />
                <Input label="Clinic Timings" value={template.clinic_timings ?? ""} onChange={(value) => update("clinic_timings", value)} />
                <Input label="Email (optional)" value={template.email ?? ""} onChange={(value) => update("email", value)} />
                <Input label="Website (optional)" value={template.website ?? ""} onChange={(value) => update("website", value)} />
              </div>
              <label className="mt-3 block">
                <span className="text-sm font-semibold">Clinic Address</span>
                <textarea value={template.clinic_address ?? ""} onChange={(event) => update("clinic_address", event.target.value)} rows={3} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
              </label>
              <label className="mt-3 block">
                <span className="text-sm font-semibold">Footer Text (optional)</span>
                <textarea value={template.footer_text ?? ""} onChange={(event) => update("footer_text", event.target.value)} rows={2} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
              </label>
              <button disabled={saving} className="mt-5 min-h-11 rounded bg-clinic-teal px-5 py-2 font-semibold text-white disabled:opacity-60">
                {saving ? "Saving..." : "Save Prescription Settings"}
              </button>
            </section>

            <section className="rounded border border-clinic-line bg-white p-4 shadow-soft">
              <h2 className="font-semibold text-clinic-ink">Branding Images</h2>
              <div className="mt-4 space-y-4">
                <ImageUpload label="Upload Clinic Logo" preview={template.clinic_logo} onChange={(file) => uploadImage("clinic_logo", file)} onClear={() => update("clinic_logo", null)} />
                <ImageUpload label="Upload Doctor Signature" preview={template.doctor_signature} onChange={(file) => uploadImage("doctor_signature", file)} onClear={() => update("doctor_signature", null)} />
              </div>
            </section>
          </form>
        ) : null}
      </div>
    </AppShell>
  );
}

function Input({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label>
      <span className="text-sm font-semibold">{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
    </label>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[][]; onChange: (value: string) => void }) {
  return (
    <label>
      <span className="text-sm font-semibold">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3">
        {options.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
      </select>
    </label>
  );
}

function ImageUpload({ label, preview, onChange, onClear }: { label: string; preview?: string | null; onChange: (file?: File) => void; onClear: () => void }) {
  return (
    <div>
      <label className="block">
        <span className="text-sm font-semibold">{label}</span>
        <input type="file" accept="image/*" onChange={(event) => onChange(event.target.files?.[0])} className="mt-2 block w-full rounded border border-clinic-line px-3 py-2 text-sm" />
      </label>
      <div className="mt-2 flex min-h-24 items-center justify-center rounded border border-dashed border-clinic-line bg-clinic-wash p-3">
        {preview ? <img src={preview} alt="" className="max-h-24 max-w-full object-contain" /> : <span className="text-sm text-clinic-muted">No image uploaded</span>}
      </div>
      {preview ? (
        <button type="button" onClick={onClear} className="mt-2 min-h-9 rounded border border-clinic-line px-3 text-sm font-semibold text-clinic-ink">
          Remove
        </button>
      ) : null}
    </div>
  );
}
