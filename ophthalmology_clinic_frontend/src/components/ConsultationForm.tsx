"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { ConsultationStartPayload, Patient, PatientHistory, PatientPayload, Suggestion, SuggestionFieldName, User, Visit, VisitPayload } from "@/lib/types";
import { patientName } from "@/lib/format";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { PatientBanner } from "./PatientBanner";

const POWER_VALUES = Array.from({ length: 161 }, (_, index) => {
  const value = -20 + index * 0.25;
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
});
const AXIS_VALUES = Array.from({ length: 181 }, (_, index) => index);
const DISTANCE_VA_OPTIONS = ["6/6", "6/9", "6/12", "6/18", "6/24", "6/36", "6/60", "CF", "HM", "PL", "NPL"];
const NEAR_VA_OPTIONS = ["N6", "N8", "N10", "N12", "N18", "N24", "N36", "N48"];
const EXAM_OPTIONS = ["Normal", "Clear", "Quiet", "Round reactive", "Immature cataract", "Pseudophakia", "Early changes", "Other"];

const examRows = [
  ["Eyelids & Adnexa", "eyelids_adnexa_right", "eyelids_adnexa_left"],
  ["Extra Ocular Movements", "extra_ocular_movements_right", "extra_ocular_movements_left"],
  ["Cornea", "cornea_right", "cornea_left"],
  ["Anterior Chamber", "anterior_chamber_right", "anterior_chamber_left"],
  ["Conjunctiva", "conjunctiva_right", "conjunctiva_left"],
  ["Pupil", "pupil_right", "pupil_left"],
  ["Lens", "lens_right", "lens_left"],
  ["Fundus", "fundus_right", "fundus_left"]
] as const;

const emptyPayload: VisitPayload = {
  patient_id: 0,
  doctor_id: 0,
  chief_complaint: "",
  diagnosis: "",
  prescription: "",
  notes: "",
  follow_up_date: null,
  right_eye_sph: "",
  right_eye_cyl: "",
  right_eye_axis: null,
  right_eye_va: "",
  left_eye_sph: "",
  left_eye_cyl: "",
  left_eye_axis: null,
  left_eye_va: "",
  slit_lamp_enabled: false,
  slit_lamp_findings: "",
  fundus_enabled: false,
  fundus_findings: "",
  general_findings_enabled: false,
  general_findings: "",
  iop_enabled: false,
  iop_right: null,
  iop_left: null,
  additional_notes: "",
  distance_prescription_enabled: true,
  distance_right_sphere: "",
  distance_right_cylinder: "",
  distance_right_axis: null,
  distance_right_va: "",
  distance_left_sphere: "",
  distance_left_cylinder: "",
  distance_left_axis: null,
  distance_left_va: "",
  distance_add: "",
  near_prescription_enabled: false,
  near_right_sphere: "",
  near_right_cylinder: "",
  near_right_axis: null,
  near_right_va: "",
  near_left_sphere: "",
  near_left_cylinder: "",
  near_left_axis: null,
  near_left_va: "",
  near_add: "",
  eyelids_adnexa_right: "Normal",
  eyelids_adnexa_left: "Normal",
  extra_ocular_movements_right: "Full",
  extra_ocular_movements_left: "Full",
  cornea_right: "Clear",
  cornea_left: "Clear",
  anterior_chamber_right: "Normal depth",
  anterior_chamber_left: "Normal depth",
  conjunctiva_right: "Quiet",
  conjunctiva_left: "Quiet",
  pupil_right: "Round reactive",
  pupil_left: "Round reactive",
  lens_right: "Clear",
  lens_left: "Clear",
  fundus_right: "Normal",
  fundus_left: "Normal",
  advice: "",
  tests_prescribed: ""
};

type PatientFormState = {
  patient_id: string;
  first_name: string;
  last_name: string;
  age: string;
  gender: string;
  phone: string;
  address: string;
  occupation: string;
  date_of_birth: string;
};

const emptyPatientForm: PatientFormState = {
  patient_id: "",
  first_name: "",
  last_name: "",
  age: "",
  gender: "",
  phone: "",
  address: "",
  occupation: "",
  date_of_birth: ""
};

type ConsultationFormProps = {
  mode: "create" | "edit";
  visitId?: number;
};

export function ConsultationForm({ mode, visitId }: ConsultationFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialPatientId = Number(searchParams.get("patientId") ?? 0);
  const [me, setMe] = useState<User | null>(null);
  const [doctors, setDoctors] = useState<User[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientForm, setPatientForm] = useState<PatientFormState>(emptyPatientForm);
  const [patientQuery, setPatientQuery] = useState("");
  const [patientMatches, setPatientMatches] = useState<Patient[]>([]);
  const [history, setHistory] = useState<PatientHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [visit, setVisit] = useState<Visit | null>(null);
  const [payload, setPayload] = useState<VisitPayload>(emptyPayload);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const currentUser = await api.me();
        const [patientList, existingVisit, doctorList] = await Promise.all([
          api.patients(),
          mode === "edit" && visitId ? api.visit(visitId) : Promise.resolve(null),
          api.doctors().catch(() => [] as User[])
        ]);

        if (!active) return;
        setMe(currentUser);
        setPatients(patientList);
        setDoctors(doctorList);
        setVisit(existingVisit);

        if (existingVisit) {
          setPayload(toPayload(existingVisit));
          const existingPatient = existingVisit.patient ?? patientList.find((patient) => patient.id === existingVisit.patient_id) ?? null;
          if (existingPatient) {
            setPatientForm(patientToForm(existingPatient));
            setPatientQuery(`${patientName(existingPatient)} ${existingPatient.phone ?? ""}`.trim());
          }
        } else {
          const rupa = doctorList.find((doctor) => doctor.full_name.toLowerCase() === "dr. rupa kapale");
          const initialPatient = patientList.find((patient) => patient.id === initialPatientId) ?? null;
          if (initialPatient) {
            setPatientForm(patientToForm(initialPatient));
            setPatientQuery(`${patientName(initialPatient)} ${initialPatient.phone ?? ""}`.trim());
          }
          setPayload({
            ...emptyPayload,
            patient_id: initialPatientId,
            doctor_id: currentUser.role === "doctor" ? currentUser.id : rupa?.id ?? doctorList[0]?.id ?? 0
          });
        }
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : "Unable to load consultation");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [initialPatientId, mode, visitId]);

  const selectedPatient = useMemo(
    () => patients.find((patient) => patient.id === Number(payload.patient_id)) ?? visit?.patient ?? null,
    [patients, payload.patient_id, visit]
  );
  const selectedDoctor = useMemo(
    () => (me?.role === "doctor" ? me : doctors.find((doctor) => doctor.id === Number(payload.doctor_id)) ?? visit?.doctor ?? null),
    [doctors, me, payload.doctor_id, visit]
  );
  const canEditMedical = me?.role === "admin" || me?.role === "doctor";

  useEffect(() => {
    let active = true;
    const query = patientQuery.trim();
    if (mode !== "create" || query.length < 2) {
      setPatientMatches([]);
      return;
    }
    const timer = window.setTimeout(() => {
      api.searchPatients(query)
        .then((matches) => {
          if (active) setPatientMatches(matches);
        })
        .catch(() => {
          if (active) setPatientMatches([]);
        });
    }, 150);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [mode, patientQuery]);

  useEffect(() => {
    let active = true;
    if (!selectedPatient || !canEditMedical) {
      setHistory(null);
      return;
    }
    setHistoryLoading(true);
    api.patientHistory(selectedPatient.id)
      .then((data) => {
        if (active) setHistory(data);
      })
      .catch(() => {
        if (active) setHistory(null);
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => {
      active = false;
    };
  }, [canEditMedical, selectedPatient]);

  function update<K extends keyof VisitPayload>(key: K, value: VisitPayload[K]) {
    setPayload((current) => ({ ...current, [key]: value }));
  }

  function updatePatient<K extends keyof PatientFormState>(key: K, value: PatientFormState[K]) {
    setPatientForm((current) => ({ ...current, [key]: value }));
  }

  function selectPatient(patient: Patient) {
    setPatients((current) => (current.some((item) => item.id === patient.id) ? current : [patient, ...current]));
    setPatientForm(patientToForm(patient));
    setPatientQuery(`${patientName(patient)} ${patient.phone ?? ""}`.trim());
    setPatientMatches([]);
    setPayload((current) => ({ ...current, patient_id: patient.id }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");

    if (!payload.doctor_id) {
      setError("Doctor is required.");
      setSaving(false);
      return;
    }
    if (mode === "create" && !payload.patient_id && !patientForm.first_name.trim()) {
      setError("Patient name is required.");
      setSaving(false);
      return;
    }
    if (mode === "create" && !payload.patient_id && !patientForm.age.trim()) {
      setError("Patient age is required.");
      setSaving(false);
      return;
    }
    if (canEditMedical && !payload.chief_complaint.trim()) {
      setError("Presenting complaint is required.");
      setSaving(false);
      return;
    }
    if (canEditMedical && !payload.distance_prescription_enabled && !payload.near_prescription_enabled) {
      setError("Select Distance Prescription, Near Prescription, or both.");
      setSaving(false);
      return;
    }

    try {
      let saved: Visit;
      if (mode === "edit" && visitId) {
        const normalized = normalizePayload(payload);
        saved = await api.replaceVisit(visitId, normalized);
      } else {
        const started = await api.startConsultation(toConsultationStartPayload(payload, patientForm, canEditMedical));
        if (canEditMedical) {
          const normalized = normalizePayload({
            ...payload,
            patient_id: started.patient_id,
            doctor_id: started.doctor_id
          });
          saved = await api.replaceVisit(started.id, normalized);
        } else {
          saved = started;
        }
      }
      if (!canEditMedical) {
        router.push(saved.patient_id ? `/patients/${saved.patient_id}` : "/queue");
        return;
      }
      router.push(`/consultations/${saved.id}`);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save consultation");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState label="Loading consultation" />;

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {error ? <ErrorState message={error} /> : null}
      <PatientBanner patient={selectedPatient} doctor={selectedDoctor} visit={visit} />

      <section className="rounded border border-clinic-line bg-white p-4 shadow-soft sm:p-5">
        <PatientIntakeSection
          mode={mode}
          query={patientQuery}
          matches={patientMatches}
          form={patientForm}
          selectedPatient={selectedPatient}
          onQuery={setPatientQuery}
          onSelect={selectPatient}
          onChange={updatePatient}
        />

        <div className="mt-4 grid gap-4 lg:grid-cols-2">

          <label className="block">
            <span className="text-sm font-semibold text-clinic-ink">Doctor</span>
            {me?.role === "doctor" ? (
              <input className="mt-2 min-h-12 w-full rounded border border-clinic-line bg-clinic-wash px-3" value={me.full_name} disabled />
            ) : (
              <select
                required
                value={payload.doctor_id || ""}
                onChange={(event) => update("doctor_id", Number(event.target.value))}
                className="mt-2 min-h-12 w-full rounded border border-clinic-line bg-white px-3 text-base"
              >
                <option value="">Select doctor</option>
                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.full_name}
                  </option>
                ))}
              </select>
            )}
          </label>

          {canEditMedical ? (
            <label className="block">
              <span className="text-sm font-semibold text-clinic-ink">Next Visit</span>
              <input
                type="date"
                value={payload.follow_up_date ?? ""}
                onChange={(event) => update("follow_up_date", event.target.value || null)}
                className="mt-2 min-h-12 w-full rounded border border-clinic-line px-3 text-base"
              />
            </label>
          ) : null}
        </div>

        <ReadOnlyPatientDetails patient={selectedPatient} />

        {canEditMedical ? (
          <label className="mt-4 block">
            <span className="text-sm font-semibold text-clinic-ink">Presenting Complaint</span>
            <SuggestingTextarea
              required
              fieldName="chief_complaint"
              value={payload.chief_complaint}
              onChange={(value) => update("chief_complaint", value)}
              rows={3}
            />
          </label>
        ) : (
          <p className="mt-4 rounded border border-clinic-line bg-clinic-wash px-3 py-3 text-sm text-clinic-muted">
            Receptionist intake creates the patient record and starts today&apos;s consultation. Medical sections are completed by the doctor.
          </p>
        )}
      </section>

      {canEditMedical ? (
        <>
          <PatientHistoryPanel history={history} loading={historyLoading} />
          <PrescriptionSection payload={payload} update={update} />
          <IopSection payload={payload} update={update} />
          <ExaminationTable payload={payload} update={update} />

          <section className="grid gap-4 lg:grid-cols-2">
            <LargeText label="Diagnosis" fieldName="diagnosis" value={payload.diagnosis ?? ""} onChange={(value) => update("diagnosis", value)} />
            <LargeText label="Advice" fieldName="advice" value={payload.advice ?? ""} onChange={(value) => update("advice", value)} />
            <LargeText label="Tests Prescribed" fieldName="tests_prescribed" value={payload.tests_prescribed ?? ""} onChange={(value) => update("tests_prescribed", value)} />
            <LargeText label="Additional Clinical Notes" fieldName="clinical_notes" value={payload.additional_notes ?? ""} onChange={(value) => update("additional_notes", value)} />
          </section>
        </>
      ) : null}

      <div className="sticky bottom-0 -mx-4 border-t border-clinic-line bg-white/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded sm:border sm:shadow-soft">
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={() => router.back()}
            className="min-h-12 rounded border border-clinic-line bg-white px-5 py-2 font-semibold text-clinic-ink"
          >
            Cancel
          </button>
          <button type="submit" disabled={saving} className="min-h-12 rounded bg-clinic-teal px-5 py-2 font-semibold text-white disabled:opacity-60">
            {saving ? "Saving..." : mode === "edit" ? "Update Consultation" : canEditMedical ? "Create Consultation" : "Create Consultation Intake"}
          </button>
        </div>
      </div>
    </form>
  );
}

function PatientIntakeSection({
  mode,
  query,
  matches,
  form,
  selectedPatient,
  onQuery,
  onSelect,
  onChange
}: {
  mode: "create" | "edit";
  query: string;
  matches: Patient[];
  form: PatientFormState;
  selectedPatient: Patient | null;
  onQuery: (value: string) => void;
  onSelect: (patient: Patient) => void;
  onChange: <K extends keyof PatientFormState>(key: K, value: PatientFormState[K]) => void;
}) {
  return (
    <div>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-semibold text-clinic-ink">Patient Intake</h2>
          <p className="text-sm text-clinic-muted">Search an existing patient or enter new demographics to start today&apos;s consultation.</p>
        </div>
        {selectedPatient ? <span className="rounded bg-clinic-mint px-3 py-1 text-sm font-semibold text-clinic-ink">Existing patient selected</span> : null}
      </div>

      {mode === "create" ? (
        <div className="relative mt-4">
          <label className="block">
            <span className="text-sm font-semibold text-clinic-ink">Search by name, phone number, or patient ID</span>
            <input
              value={query}
              onChange={(event) => onQuery(event.target.value)}
              placeholder="Start typing patient name or mobile number"
              className="mt-2 min-h-12 w-full rounded border border-clinic-line px-3 text-base"
            />
          </label>
          {matches.length > 0 ? (
            <div className="absolute z-20 mt-1 max-h-72 w-full overflow-y-auto rounded border border-clinic-line bg-white shadow-soft">
              {matches.map((patient) => (
                <button key={patient.id} type="button" onClick={() => onSelect(patient)} className="block w-full px-3 py-3 text-left hover:bg-clinic-wash">
                  <span className="block font-semibold text-clinic-ink">{patientName(patient)}</span>
                  <span className="block text-sm text-clinic-muted">
                    {patient.phone ?? "No mobile"} - {patient.patient_id} - Last Visit: {patient.last_visit_at ? new Date(patient.last_visit_at).toLocaleDateString() : "No previous visit"}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <SmallInput label="Patient ID" value={form.patient_id || "Auto generated"} onChange={() => undefined} disabled />
        <SmallInput label="First Name" value={form.first_name} onChange={(value) => onChange("first_name", value)} />
        <SmallInput label="Last Name" value={form.last_name} onChange={(value) => onChange("last_name", value)} />
        <SmallInput label="Age" type="number" value={form.age} onChange={(value) => onChange("age", value)} />
        <SmallInput label="Date of Birth" type="date" required={false} value={form.date_of_birth} onChange={(value) => onChange("date_of_birth", value)} />
        <SmallSelect label="Sex" value={form.gender} onChange={(value) => onChange("gender", value)} options={["Male", "Female", "Other"]} />
        <SmallInput label="Mobile Number" required={false} value={form.phone} onChange={(value) => onChange("phone", value)} />
        <SmallInput label="Occupation" required={false} value={form.occupation} onChange={(value) => onChange("occupation", value)} />
      </div>
      <label className="mt-3 block">
        <span className="text-sm font-semibold text-clinic-ink">Address</span>
        <textarea value={form.address} onChange={(event) => onChange("address", event.target.value)} rows={2} className="mt-2 w-full rounded border border-clinic-line px-3 py-2 text-base" />
      </label>
    </div>
  );
}

function PatientHistoryPanel({ history, loading }: { history: PatientHistory | null; loading: boolean }) {
  if (loading) return <LoadingState label="Loading patient history" />;
  if (!history) return null;
  return (
    <section className="rounded border border-clinic-line bg-white p-4 shadow-soft sm:p-5">
      <h2 className="font-semibold text-clinic-ink">Previous History</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <HistoryList
          title="Consultations"
          empty="No previous consultations"
          items={history.consultations.slice(0, 5).map((visit) => ({
            id: visit.id,
            primary: visit.diagnosis || visit.chief_complaint || "Consultation",
            secondary: new Date(visit.visit_date).toLocaleDateString()
          }))}
        />
        <HistoryList
          title="Operations"
          empty="No previous operations"
          items={history.operations.slice(0, 5).map((operation) => ({
            id: operation.id,
            primary: operation.operation_type?.name ?? "Operation",
            secondary: `${operation.operation_date} - ${operation.status.replace("_", " ")}`
          }))}
        />
        <HistoryList
          title="Follow-ups"
          empty="No follow-up history"
          items={history.followups.slice(0, 5).map((followup) => ({
            id: followup.id,
            primary: followup.notes || followup.follow_up_type.replaceAll("_", " "),
            secondary: `${followup.follow_up_date} - ${followup.status}`
          }))}
        />
      </div>
    </section>
  );
}

function HistoryList({ title, empty, items }: { title: string; empty: string; items: Array<{ id: number; primary: string; secondary: string }> }) {
  return (
    <div className="rounded border border-clinic-line">
      <h3 className="border-b border-clinic-line bg-clinic-wash px-3 py-2 text-sm font-semibold text-clinic-ink">{title}</h3>
      <div className="divide-y divide-clinic-line">
        {items.map((item) => (
          <div key={item.id} className="px-3 py-2">
            <p className="text-sm font-semibold text-clinic-ink">{item.primary}</p>
            <p className="text-xs text-clinic-muted">{item.secondary}</p>
          </div>
        ))}
        {items.length === 0 ? <p className="px-3 py-3 text-sm text-clinic-muted">{empty}</p> : null}
      </div>
    </div>
  );
}

function ReadOnlyPatientDetails({ patient }: { patient: Patient | null }) {
  const items = [
    ["Patient ID", patient?.patient_id ?? "-"],
    ["Age", patient ? String(patient.age) : "-"],
    ["Sex", patient?.gender ?? "-"],
    ["Mobile Number", patient?.phone ?? "-"]
  ];
  return (
    <dl className="mt-4 grid gap-px overflow-hidden rounded border border-clinic-line bg-clinic-line sm:grid-cols-2 lg:grid-cols-4">
      {items.map(([label, value]) => (
        <div key={label} className="bg-clinic-wash px-3 py-3">
          <dt className="text-xs font-semibold uppercase tracking-wide text-clinic-muted">{label}</dt>
          <dd className="mt-1 font-semibold text-clinic-ink">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function PrescriptionSection({
  payload,
  update
}: {
  payload: VisitPayload;
  update: <K extends keyof VisitPayload>(key: K, value: VisitPayload[K]) => void;
}) {
  return (
    <section className="rounded border border-clinic-line bg-white shadow-soft">
      <div className="border-b border-clinic-line px-4 py-3 sm:px-5">
        <h2 className="font-semibold text-clinic-ink">Refraction / Glass Prescription</h2>
      </div>
      <div className="space-y-4 p-4 sm:p-5">
        <label className="flex min-h-11 items-center gap-3">
          <input
            type="checkbox"
            checked={payload.distance_prescription_enabled}
            onChange={(event) => update("distance_prescription_enabled", event.target.checked)}
            className="h-5 w-5 accent-clinic-teal"
          />
          <span className="font-semibold text-clinic-ink">Distance Prescription</span>
        </label>
        {payload.distance_prescription_enabled ? <PrescriptionTable prefix="distance" vaOptions={DISTANCE_VA_OPTIONS} payload={payload} update={update} /> : null}

        <label className="flex min-h-11 items-center gap-3">
          <input
            type="checkbox"
            checked={payload.near_prescription_enabled}
            onChange={(event) => update("near_prescription_enabled", event.target.checked)}
            className="h-5 w-5 accent-clinic-teal"
          />
          <span className="font-semibold text-clinic-ink">Near Prescription</span>
        </label>
        {payload.near_prescription_enabled ? <PrescriptionTable prefix="near" vaOptions={NEAR_VA_OPTIONS} payload={payload} update={update} /> : null}
      </div>
    </section>
  );
}

function PrescriptionTable({
  prefix,
  vaOptions,
  payload,
  update
}: {
  prefix: "distance" | "near";
  vaOptions: string[];
  payload: VisitPayload;
  update: <K extends keyof VisitPayload>(key: K, value: VisitPayload[K]) => void;
}) {
  const keys = {
    rightSphere: `${prefix}_right_sphere` as keyof VisitPayload,
    rightCylinder: `${prefix}_right_cylinder` as keyof VisitPayload,
    rightAxis: `${prefix}_right_axis` as keyof VisitPayload,
    rightVa: `${prefix}_right_va` as keyof VisitPayload,
    leftSphere: `${prefix}_left_sphere` as keyof VisitPayload,
    leftCylinder: `${prefix}_left_cylinder` as keyof VisitPayload,
    leftAxis: `${prefix}_left_axis` as keyof VisitPayload,
    leftVa: `${prefix}_left_va` as keyof VisitPayload,
    add: `${prefix}_add` as keyof VisitPayload
  };

  return (
    <div className="overflow-x-auto rounded border border-clinic-line">
      <table className="w-full min-w-[760px] border-collapse text-left">
        <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
          <tr>
            <th className="border-b border-clinic-line px-4 py-3">Eye</th>
            <th className="border-b border-clinic-line px-4 py-3">Sphere</th>
            <th className="border-b border-clinic-line px-4 py-3">Cylinder</th>
            <th className="border-b border-clinic-line px-4 py-3">Axis</th>
            <th className="border-b border-clinic-line px-4 py-3">VA</th>
            <th className="border-b border-clinic-line px-4 py-3">Add</th>
          </tr>
        </thead>
        <tbody>
          <PrescriptionRow
            label="RIGHT EYE"
            sphere={(payload[keys.rightSphere] as string | null) ?? ""}
            cylinder={(payload[keys.rightCylinder] as string | null) ?? ""}
            axis={(payload[keys.rightAxis] as number | null) ?? null}
            va={(payload[keys.rightVa] as string | null) ?? ""}
            add={(payload[keys.add] as string | null) ?? ""}
            vaOptions={vaOptions}
            onSphere={(value) => update(keys.rightSphere, value as never)}
            onCylinder={(value) => update(keys.rightCylinder, value as never)}
            onAxis={(value) => update(keys.rightAxis, value as never)}
            onVa={(value) => update(keys.rightVa, value as never)}
            onAdd={(value) => update(keys.add, value as never)}
          />
          <PrescriptionRow
            label="LEFT EYE"
            sphere={(payload[keys.leftSphere] as string | null) ?? ""}
            cylinder={(payload[keys.leftCylinder] as string | null) ?? ""}
            axis={(payload[keys.leftAxis] as number | null) ?? null}
            va={(payload[keys.leftVa] as string | null) ?? ""}
            add={(payload[keys.add] as string | null) ?? ""}
            vaOptions={vaOptions}
            onSphere={(value) => update(keys.leftSphere, value as never)}
            onCylinder={(value) => update(keys.leftCylinder, value as never)}
            onAxis={(value) => update(keys.leftAxis, value as never)}
            onVa={(value) => update(keys.leftVa, value as never)}
            onAdd={(value) => update(keys.add, value as never)}
          />
        </tbody>
      </table>
    </div>
  );
}

function PrescriptionRow({
  label,
  sphere,
  cylinder,
  axis,
  va,
  add,
  vaOptions,
  onSphere,
  onCylinder,
  onAxis,
  onVa,
  onAdd
}: {
  label: string;
  sphere: string;
  cylinder: string;
  axis: number | null;
  va: string;
  add: string;
  vaOptions: string[];
  onSphere: (value: string) => void;
  onCylinder: (value: string) => void;
  onAxis: (value: number | null) => void;
  onVa: (value: string) => void;
  onAdd: (value: string) => void;
}) {
  const cellClass = "border-b border-clinic-line px-3 py-3";
  return (
    <tr>
      <td className={`${cellClass} font-semibold text-clinic-ink`}>{label}</td>
      <td className={cellClass}><PowerSelect value={sphere} onChange={onSphere} /></td>
      <td className={cellClass}><PowerSelect value={cylinder} onChange={onCylinder} /></td>
      <td className={cellClass}><AxisSelect value={axis} onChange={onAxis} /></td>
      <td className={cellClass}><OptionSelect value={va} options={vaOptions} onChange={onVa} /></td>
      <td className={cellClass}><PowerSelect value={add} onChange={onAdd} /></td>
    </tr>
  );
}

function PowerSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <OptionSelect value={value} options={POWER_VALUES} onChange={onChange} placeholder="0.00" />;
}

function AxisSelect({ value, onChange }: { value: number | null; onChange: (value: number | null) => void }) {
  return (
    <select value={value ?? ""} onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)} className="min-h-11 w-full rounded border border-clinic-line bg-white px-2 text-base">
      <option value="">Axis</option>
      {AXIS_VALUES.map((axis) => <option key={axis} value={axis}>{axis}</option>)}
    </select>
  );
}

function OptionSelect({ value, options, onChange, placeholder = "Select" }: { value: string; options: string[]; onChange: (value: string) => void; placeholder?: string }) {
  return (
    <select value={value} onChange={(event) => onChange(event.target.value)} className="min-h-11 w-full rounded border border-clinic-line bg-white px-2 text-base">
      <option value="">{placeholder}</option>
      {options.map((option) => <option key={option} value={option}>{option}</option>)}
    </select>
  );
}

function ExaminationTable({
  payload,
  update
}: {
  payload: VisitPayload;
  update: <K extends keyof VisitPayload>(key: K, value: VisitPayload[K]) => void;
}) {
  return (
    <section className="rounded border border-clinic-line bg-white shadow-soft">
      <div className="border-b border-clinic-line px-4 py-3 sm:px-5">
        <h2 className="font-semibold text-clinic-ink">Ophthalmic Examination</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left">
          <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
            <tr>
              <th className="border-b border-clinic-line px-4 py-3">Finding</th>
              <th className="border-b border-clinic-line px-4 py-3">RIGHT EYE</th>
              <th className="border-b border-clinic-line px-4 py-3">LEFT EYE</th>
            </tr>
          </thead>
          <tbody>
            {examRows.map(([label, rightKey, leftKey]) => (
              <tr key={label}>
                <td className="border-b border-clinic-line px-4 py-3 font-semibold text-clinic-ink">{label}</td>
                <td className="border-b border-clinic-line px-3 py-3">
                  <ExamCell value={(payload[rightKey] as string | null) ?? ""} onChange={(value) => update(rightKey, value as never)} />
                </td>
                <td className="border-b border-clinic-line px-3 py-3">
                  <ExamCell value={(payload[leftKey] as string | null) ?? ""} onChange={(value) => update(leftKey, value as never)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ExamCell({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const isCustom = value !== "" && !EXAM_OPTIONS.includes(value);
  const [custom, setCustom] = useState(isCustom);
  return (
    <div className="space-y-2">
      <select
        value={custom ? "Other" : value}
        onChange={(event) => {
          if (event.target.value === "Other") {
            setCustom(true);
            onChange("");
          } else {
            setCustom(false);
            onChange(event.target.value);
          }
        }}
        className="min-h-11 w-full rounded border border-clinic-line bg-white px-2 text-base"
      >
        <option value="">Select finding</option>
        {EXAM_OPTIONS.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
      {custom ? (
        <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={2} className="w-full rounded border border-clinic-line px-3 py-2 text-base" />
      ) : null}
    </div>
  );
}

function IopSection({
  payload,
  update
}: {
  payload: VisitPayload;
  update: <K extends keyof VisitPayload>(key: K, value: VisitPayload[K]) => void;
}) {
  const rows: Array<{ label: string; key: "iop_right" | "iop_left"; value?: number | null }> = [
    { label: "Right", key: "iop_right", value: payload.iop_right },
    { label: "Left", key: "iop_left", value: payload.iop_left }
  ];

  return (
    <section className="rounded border border-clinic-line bg-white p-4 shadow-soft sm:p-5">
      <label className="flex min-h-11 items-center gap-3">
        <input type="checkbox" checked={payload.iop_enabled} onChange={(event) => update("iop_enabled", event.target.checked)} className="h-5 w-5 accent-clinic-teal" />
        <span className="font-semibold text-clinic-ink">Intraocular Pressure</span>
      </label>
      {payload.iop_enabled ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[420px] border-collapse text-left">
            <thead className="bg-clinic-wash text-xs uppercase tracking-wide text-clinic-muted">
              <tr>
                <th className="border-b border-clinic-line px-4 py-3">Eye</th>
                <th className="border-b border-clinic-line px-4 py-3">Pressure</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ label, key, value }) => (
                <tr key={label}>
                  <td className="border-b border-clinic-line px-4 py-3 font-semibold">{label}</td>
                  <td className="border-b border-clinic-line px-4 py-3">
                    <input
                      type="number"
                      min={0}
                      max={80}
                      value={value ?? ""}
                      onChange={(event) => update(key, event.target.value ? Number(event.target.value) : null)}
                      className="min-h-11 w-full rounded border border-clinic-line px-3 text-base"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function LargeText({ label, fieldName, value, onChange }: { label: string; fieldName: SuggestionFieldName; value: string; onChange: (value: string) => void }) {
  return (
    <section className="rounded border border-clinic-line bg-white p-4 shadow-soft sm:p-5">
      <label className="block">
        <span className="text-sm font-semibold text-clinic-ink">{label}</span>
        <SuggestingTextarea fieldName={fieldName} value={value} onChange={onChange} rows={6} />
      </label>
    </section>
  );
}

function SuggestingTextarea({
  fieldName,
  value,
  onChange,
  rows,
  required = false
}: {
  fieldName: SuggestionFieldName;
  value: string;
  onChange: (value: string) => void;
  rows: number;
  required?: boolean;
}) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let active = true;
    const query = value.trim();
    if (query.length < 2) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    const timer = window.setTimeout(() => {
      api.suggestions(fieldName, query)
        .then((items) => {
          if (!active) return;
          setSuggestions(items);
          setActiveIndex(0);
          setOpen(items.length > 0);
        })
        .catch(() => {
          if (active) {
            setSuggestions([]);
            setOpen(false);
          }
        });
    }, 120);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [fieldName, value]);

  function choose(suggestion: Suggestion) {
    onChange(suggestion.suggestion_text);
    setOpen(false);
  }

  return (
    <div className="relative mt-2">
      <textarea
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (!open || suggestions.length === 0) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActiveIndex((current) => Math.min(current + 1, suggestions.length - 1));
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActiveIndex((current) => Math.max(current - 1, 0));
          } else if (event.key === "Enter" || event.key === "Tab") {
            event.preventDefault();
            choose(suggestions[activeIndex]);
          } else if (event.key === "Escape") {
            setOpen(false);
          }
        }}
        onBlur={() => window.setTimeout(() => setOpen(false), 120)}
        onFocus={() => setOpen(suggestions.length > 0)}
        rows={rows}
        className="w-full rounded border border-clinic-line px-3 py-2 text-base"
      />
      {open ? (
        <div className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded border border-clinic-line bg-white shadow-soft">
          {suggestions.map((suggestion, index) => (
            <button
              type="button"
              key={suggestion.id}
              onMouseDown={(event) => {
                event.preventDefault();
                choose(suggestion);
              }}
              className={`block w-full px-3 py-2 text-left text-sm ${index === activeIndex ? "bg-clinic-mint" : "bg-white hover:bg-clinic-wash"}`}
            >
              <span className="font-semibold text-clinic-ink">{suggestion.suggestion_text}</span>
              <span className="ml-2 text-xs text-clinic-muted">Used {suggestion.usage_count}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function SmallInput({
  label,
  value,
  onChange,
  type = "text",
  required = true,
  disabled = false
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-semibold text-clinic-ink">{label}</span>
      <input
        required={required}
        disabled={disabled}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 min-h-11 w-full rounded border border-clinic-line px-3 text-base disabled:bg-clinic-wash"
      />
    </label>
  );
}

function SmallSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-sm font-semibold text-clinic-ink">{label}</span>
      <select required value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded border border-clinic-line bg-white px-3 text-base">
        <option value="">Select</option>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </label>
  );
}

function patientToForm(patient: Patient): PatientFormState {
  return {
    patient_id: patient.patient_id,
    first_name: patient.first_name,
    last_name: patient.last_name,
    age: String(patient.age),
    gender: patient.gender,
    phone: patient.phone ?? "",
    address: patient.address ?? "",
    occupation: patient.occupation ?? "",
    date_of_birth: patient.date_of_birth ?? ""
  };
}

function toPatientPayload(form: PatientFormState): PatientPayload {
  return {
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim(),
    age: Number(form.age),
    gender: form.gender,
    phone: form.phone.trim() || null,
    address: form.address.trim() || null,
    occupation: form.occupation.trim() || null,
    date_of_birth: form.date_of_birth || null
  };
}

function toConsultationStartPayload(payload: VisitPayload, patientForm: PatientFormState, includeComplaint: boolean): ConsultationStartPayload {
  return {
    patient_id: payload.patient_id || null,
    patient: toPatientPayload(patientForm),
    doctor_id: payload.doctor_id || null,
    chief_complaint: includeComplaint ? payload.chief_complaint || null : null
  };
}

function toPayload(visit: Visit): VisitPayload {
  return {
    ...emptyPayload,
    ...visit,
    diagnosis: visit.diagnosis ?? "",
    prescription: visit.prescription ?? "",
    notes: visit.notes ?? "",
    follow_up_date: visit.follow_up_date ?? null,
    distance_prescription_enabled: visit.distance_prescription_enabled || Boolean(visit.right_eye_sph || visit.left_eye_sph),
    distance_right_sphere: visit.distance_right_sphere ?? visit.right_eye_sph ?? "",
    distance_right_cylinder: visit.distance_right_cylinder ?? visit.right_eye_cyl ?? "",
    distance_right_axis: visit.distance_right_axis ?? visit.right_eye_axis ?? null,
    distance_right_va: visit.distance_right_va ?? visit.right_eye_va ?? "",
    distance_left_sphere: visit.distance_left_sphere ?? visit.left_eye_sph ?? "",
    distance_left_cylinder: visit.distance_left_cylinder ?? visit.left_eye_cyl ?? "",
    distance_left_axis: visit.distance_left_axis ?? visit.left_eye_axis ?? null,
    distance_left_va: visit.distance_left_va ?? visit.left_eye_va ?? "",
    near_prescription_enabled: visit.near_prescription_enabled,
    additional_notes: visit.additional_notes ?? "",
    advice: visit.advice ?? "",
    tests_prescribed: visit.tests_prescribed ?? ""
  };
}

function normalizePayload(payload: VisitPayload): VisitPayload {
  const distanceRightSphere = payload.distance_prescription_enabled ? payload.distance_right_sphere || null : null;
  const distanceRightCylinder = payload.distance_prescription_enabled ? payload.distance_right_cylinder || null : null;
  const distanceLeftSphere = payload.distance_prescription_enabled ? payload.distance_left_sphere || null : null;
  const distanceLeftCylinder = payload.distance_prescription_enabled ? payload.distance_left_cylinder || null : null;
  return {
    ...payload,
    prescription: payload.prescription || null,
    notes: payload.additional_notes || payload.notes || null,
    diagnosis: payload.diagnosis || null,
    follow_up_date: payload.follow_up_date || null,
    right_eye_sph: distanceRightSphere,
    right_eye_cyl: distanceRightCylinder,
    right_eye_axis: payload.distance_prescription_enabled ? payload.distance_right_axis : null,
    right_eye_va: payload.distance_prescription_enabled ? payload.distance_right_va || null : null,
    left_eye_sph: distanceLeftSphere,
    left_eye_cyl: distanceLeftCylinder,
    left_eye_axis: payload.distance_prescription_enabled ? payload.distance_left_axis : null,
    left_eye_va: payload.distance_prescription_enabled ? payload.distance_left_va || null : null,
    slit_lamp_enabled: false,
    slit_lamp_findings: null,
    fundus_enabled: false,
    fundus_findings: null,
    general_findings_enabled: false,
    general_findings: null,
    iop_right: payload.iop_enabled ? payload.iop_right : null,
    iop_left: payload.iop_enabled ? payload.iop_left : null,
    additional_notes: payload.additional_notes || null,
    advice: payload.advice || null,
    tests_prescribed: payload.tests_prescribed || null
  };
}
