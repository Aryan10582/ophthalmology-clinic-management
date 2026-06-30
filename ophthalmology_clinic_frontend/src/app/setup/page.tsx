"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import type { ClinicSetupPayload, SetupReceptionistPayload } from "@/lib/types";

const emptyReceptionist: SetupReceptionistPayload = {
  username: "",
  password: "",
  confirm_password: ""
};

const initialForm: ClinicSetupPayload = {
  doctor: {
    doctor_name: "",
    username: "",
    password: "",
    confirm_password: ""
  },
  clinic: {
    clinic_name: "",
    doctor_qualifications: "",
    doctor_registration_number: "",
    clinic_address: "",
    clinic_phone: "",
    email: "",
    clinic_timings: "",
    website: ""
  },
  receptionists: []
};

export default function SetupPage() {
  const router = useRouter();
  const [form, setForm] = useState<ClinicSetupPayload>(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.setupStatus()
      .then((status) => {
        if (!status.needs_setup) router.replace("/login");
      })
      .catch((setupError) => setError(setupError instanceof Error ? setupError.message : "Unable to check setup status"))
      .finally(() => setLoading(false));
  }, [router]);

  function updateDoctor<K extends keyof ClinicSetupPayload["doctor"]>(key: K, value: ClinicSetupPayload["doctor"][K]) {
    setForm((current) => ({ ...current, doctor: { ...current.doctor, [key]: value } }));
  }

  function updateClinic<K extends keyof ClinicSetupPayload["clinic"]>(key: K, value: ClinicSetupPayload["clinic"][K]) {
    setForm((current) => ({ ...current, clinic: { ...current.clinic, [key]: value } }));
  }

  function updateReceptionist(index: number, key: keyof SetupReceptionistPayload, value: string) {
    setForm((current) => ({
      ...current,
      receptionists: current.receptionists.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item))
    }));
  }

  function addReceptionist() {
    setForm((current) => ({ ...current, receptionists: [...current.receptionists, { ...emptyReceptionist }] }));
  }

  function removeReceptionist(index: number) {
    setForm((current) => ({ ...current, receptionists: current.receptionists.filter((_, itemIndex) => itemIndex !== index) }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (form.doctor.password !== form.doctor.confirm_password) {
      setError("Doctor password confirmation does not match");
      return;
    }
    const duplicateUsernames = new Set<string>();
    const usernames = [form.doctor.username, ...form.receptionists.map((item) => item.username)].map((item) => item.trim().toLowerCase());
    for (const username of usernames) {
      if (duplicateUsernames.has(username)) {
        setError("Usernames must be unique");
        return;
      }
      duplicateUsernames.add(username);
    }
    for (const receptionist of form.receptionists) {
      if (receptionist.password !== receptionist.confirm_password) {
        setError(`Password confirmation does not match for receptionist ${receptionist.username || ""}`.trim());
        return;
      }
    }
    setSaving(true);
    try {
      await api.completeSetup({
        ...form,
        clinic: {
          ...form.clinic,
          website: form.clinic.website || null
        }
      });
      router.replace("/login");
    } catch (setupError) {
      if (setupError instanceof ApiError) setError(setupError.message);
      else setError(setupError instanceof Error ? setupError.message : "Unable to complete clinic setup");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-clinic-wash px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <section className="mb-5 rounded border border-clinic-line bg-white p-5 shadow-soft">
          <p className="text-sm font-semibold uppercase tracking-wide text-clinic-teal">First-time setup</p>
          <h1 className="mt-1 text-3xl font-semibold text-clinic-ink">Welcome to Iris Eye Clinic</h1>
          <p className="mt-2 text-clinic-muted">Let's configure your clinic before using the application.</p>
        </section>

        {loading ? <LoadingState label="Checking setup status" /> : null}
        {error ? <div className="mb-4"><ErrorState message={error} /></div> : null}

        {!loading ? (
          <form onSubmit={submit} className="space-y-5">
            <section className="rounded border border-clinic-line bg-white p-5 shadow-soft">
              <h2 className="text-lg font-semibold text-clinic-ink">Doctor Account</h2>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <Input label="Doctor Name" value={form.doctor.doctor_name} onChange={(value) => updateDoctor("doctor_name", value)} />
                <Input label="Username" value={form.doctor.username} onChange={(value) => updateDoctor("username", value)} autoComplete="username" />
                <Input label="Password" type="password" value={form.doctor.password} onChange={(value) => updateDoctor("password", value)} autoComplete="new-password" />
                <Input label="Confirm Password" type="password" value={form.doctor.confirm_password} onChange={(value) => updateDoctor("confirm_password", value)} autoComplete="new-password" />
              </div>
            </section>

            <section className="rounded border border-clinic-line bg-white p-5 shadow-soft">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-clinic-ink">Receptionists</h2>
                  <p className="text-sm text-clinic-muted">Optional. Add staff accounts now or manage them later in Doctor Settings.</p>
                </div>
                <button type="button" onClick={addReceptionist} className="min-h-10 rounded border border-clinic-line px-3 text-sm font-semibold text-clinic-ink">
                  Add Receptionist
                </button>
              </div>
              <div className="mt-4 space-y-3">
                {form.receptionists.map((receptionist, index) => (
                  <div key={index} className="rounded border border-clinic-line bg-clinic-wash p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold text-clinic-ink">Receptionist {index + 1}</p>
                      <button type="button" onClick={() => removeReceptionist(index)} className="rounded border border-red-200 bg-white px-3 py-1 text-sm font-semibold text-red-700">
                        Remove
                      </button>
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      <Input label="Username" value={receptionist.username} onChange={(value) => updateReceptionist(index, "username", value)} autoComplete="username" />
                      <Input label="Password" type="password" value={receptionist.password} onChange={(value) => updateReceptionist(index, "password", value)} autoComplete="new-password" />
                      <Input label="Confirm Password" type="password" value={receptionist.confirm_password} onChange={(value) => updateReceptionist(index, "confirm_password", value)} autoComplete="new-password" />
                    </div>
                  </div>
                ))}
                {form.receptionists.length === 0 ? <p className="rounded border border-dashed border-clinic-line px-4 py-5 text-sm text-clinic-muted">No receptionist accounts added yet.</p> : null}
              </div>
            </section>

            <section className="rounded border border-clinic-line bg-white p-5 shadow-soft">
              <h2 className="text-lg font-semibold text-clinic-ink">Clinic Information</h2>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <Input label="Clinic Name" value={form.clinic.clinic_name} onChange={(value) => updateClinic("clinic_name", value)} />
                <Input label="Doctor Qualifications" value={form.clinic.doctor_qualifications} onChange={(value) => updateClinic("doctor_qualifications", value)} />
                <Input label="Medical Registration Number" value={form.clinic.doctor_registration_number} onChange={(value) => updateClinic("doctor_registration_number", value)} />
                <Input label="Phone Number" value={form.clinic.clinic_phone} onChange={(value) => updateClinic("clinic_phone", value)} />
                <Input label="Email" type="email" value={form.clinic.email} onChange={(value) => updateClinic("email", value)} />
                <Input label="Clinic Timings" value={form.clinic.clinic_timings} onChange={(value) => updateClinic("clinic_timings", value)} />
                <Input label="Website (optional)" required={false} value={form.clinic.website ?? ""} onChange={(value) => updateClinic("website", value)} />
              </div>
              <label className="mt-3 block">
                <span className="text-sm font-semibold text-clinic-ink">Clinic Address</span>
                <textarea required value={form.clinic.clinic_address} onChange={(event) => updateClinic("clinic_address", event.target.value)} rows={3} className="mt-2 w-full rounded border border-clinic-line px-3 py-2" />
              </label>
            </section>

            <button disabled={saving} className="min-h-12 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
              {saving ? "Saving setup..." : "Complete Clinic Setup"}
            </button>
          </form>
        ) : null}
      </div>
    </main>
  );
}

function Input({ label, value, onChange, type = "text", required = true, autoComplete }: { label: string; value: string; onChange: (value: string) => void; type?: string; required?: boolean; autoComplete?: string }) {
  return (
    <label>
      <span className="text-sm font-semibold text-clinic-ink">{label}</span>
      <input
        required={required}
        type={type}
        value={value}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3"
      />
    </label>
  );
}
