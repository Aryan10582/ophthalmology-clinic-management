"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import type { PrescriptionTemplate, User } from "@/lib/types";

const templates = [
  ["professional_blue", "Professional Blue"],
  ["minimal_white", "Minimal White"]
];

export default function SettingsPage() {
  const router = useRouter();
  const [me, setMe] = useState<User | null>(null);
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
        setMe(me);
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
          <>
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
            {me?.role === "doctor" ? <ReceptionistManagement /> : null}
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

function ReceptionistManagement() {
  const [receptionists, setReceptionists] = useState<User[]>([]);
  const [draft, setDraft] = useState({ username: "", password: "", confirm_password: "" });
  const [resetDrafts, setResetDrafts] = useState<Record<number, { password: string; confirm_password: string }>>({});
  const [renames, setRenames] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const items = await api.receptionists();
      setReceptionists(items);
      setRenames(Object.fromEntries(items.map((item) => [item.id, item.username])));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load receptionists");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createReceptionist(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createReceptionist(draft);
      setDraft({ username: "", password: "", confirm_password: "" });
      await load();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create receptionist");
    } finally {
      setSaving(false);
    }
  }

  async function renameReceptionist(receptionist: User) {
    const username = renames[receptionist.id]?.trim();
    if (!username || username === receptionist.username) return;
    setSaving(true);
    setError("");
    try {
      await api.updateReceptionist(receptionist.id, { username });
      await load();
    } catch (renameError) {
      setError(renameError instanceof Error ? renameError.message : "Unable to update username");
    } finally {
      setSaving(false);
    }
  }

  async function resetPassword(receptionist: User) {
    const draftValue = resetDrafts[receptionist.id] ?? { password: "", confirm_password: "" };
    if (!draftValue.password) return;
    setSaving(true);
    setError("");
    try {
      await api.updateReceptionist(receptionist.id, draftValue);
      setResetDrafts((current) => ({ ...current, [receptionist.id]: { password: "", confirm_password: "" } }));
      await load();
    } catch (resetError) {
      setError(resetError instanceof Error ? resetError.message : "Unable to reset password");
    } finally {
      setSaving(false);
    }
  }

  async function deleteReceptionist(receptionist: User) {
    if (!window.confirm(`Delete receptionist "${receptionist.username}"? Clinic records will not be affected.`)) return;
    setSaving(true);
    setError("");
    try {
      await api.deleteReceptionist(receptionist.id);
      await load();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete receptionist");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded border border-clinic-line bg-white p-4 shadow-soft">
      <div>
        <h2 className="font-semibold text-clinic-ink">Receptionist Management</h2>
        <p className="text-sm text-clinic-muted">Create, remove, rename, and reset receptionist accounts.</p>
      </div>
      {loading ? <div className="mt-3"><LoadingState label="Loading receptionists" /></div> : null}
      {error ? <div className="mt-3"><ErrorState message={error} /></div> : null}
      <form onSubmit={createReceptionist} className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]">
        <Input label="Username" value={draft.username} onChange={(value) => setDraft((current) => ({ ...current, username: value }))} />
        <Input label="Password" type="password" value={draft.password} onChange={(value) => setDraft((current) => ({ ...current, password: value }))} />
        <Input label="Confirm Password" type="password" value={draft.confirm_password} onChange={(value) => setDraft((current) => ({ ...current, confirm_password: value }))} />
        <button disabled={saving} className="min-h-11 self-end rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
          Create
        </button>
      </form>
      <div className="mt-4 divide-y divide-clinic-line rounded border border-clinic-line">
        {receptionists.map((receptionist) => {
          const resetDraft = resetDrafts[receptionist.id] ?? { password: "", confirm_password: "" };
          return (
            <div key={receptionist.id} className="space-y-3 p-3">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
                <Input label="Username" value={renames[receptionist.id] ?? receptionist.username} onChange={(value) => setRenames((current) => ({ ...current, [receptionist.id]: value }))} />
                <button type="button" disabled={saving} onClick={() => renameReceptionist(receptionist)} className="min-h-11 rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">
                  Change Username
                </button>
                <button type="button" disabled={saving} onClick={() => deleteReceptionist(receptionist)} className="min-h-11 rounded border border-red-200 px-3 text-sm font-semibold text-red-700 disabled:opacity-60">
                  Delete
                </button>
              </div>
              <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
                <Input label="New Password" type="password" value={resetDraft.password} onChange={(value) => setResetDrafts((current) => ({ ...current, [receptionist.id]: { ...resetDraft, password: value } }))} />
                <Input label="Confirm New Password" type="password" value={resetDraft.confirm_password} onChange={(value) => setResetDrafts((current) => ({ ...current, [receptionist.id]: { ...resetDraft, confirm_password: value } }))} />
                <button type="button" disabled={saving} onClick={() => resetPassword(receptionist)} className="min-h-11 self-end rounded border border-clinic-line px-3 text-sm font-semibold disabled:opacity-60">
                  Reset Password
                </button>
              </div>
            </div>
          );
        })}
        {!loading && receptionists.length === 0 ? <p className="p-4 text-sm text-clinic-muted">No receptionist accounts yet.</p> : null}
      </div>
    </section>
  );
}

function Input({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label>
      <span className="text-sm font-semibold">{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3" />
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
