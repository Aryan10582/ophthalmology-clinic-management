export type UserRole = "admin" | "doctor" | "receptionist";

export type User = {
  id: number;
  full_name: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_demo_account: boolean;
  created_at?: string;
};

export type SetupStatus = {
  needs_setup: boolean;
};

export type SetupReceptionistPayload = {
  username: string;
  password: string;
  confirm_password: string;
};

export type ClinicSetupPayload = {
  doctor: {
    doctor_name: string;
    username: string;
    password: string;
    confirm_password: string;
  };
  clinic: {
    clinic_name: string;
    doctor_qualifications: string;
    doctor_registration_number: string;
    clinic_address: string;
    clinic_phone: string;
    email: string;
    clinic_timings: string;
    website?: string | null;
  };
  receptionists: SetupReceptionistPayload[];
};

export type ClinicSetupResult = {
  doctor_id: number;
  receptionist_count: number;
};

export type ReceptionistPayload = SetupReceptionistPayload;

export type ReceptionistUpdatePayload = {
  username?: string;
  password?: string;
  confirm_password?: string;
  is_active?: boolean;
};

export type Patient = {
  id: number;
  patient_id: string;
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  phone?: string | null;
  address?: string | null;
  date_of_birth?: string | null;
  created_at: string;
  last_visit_at?: string | null;
};

export type PaymentStatus = "not_paid" | "paid";
export type PaymentMethod = "cash" | "upi_qr";

export type PaymentUpdate = {
  payment_status: PaymentStatus;
  payment_method?: PaymentMethod | null;
};

export type VisitPayload = {
  patient_id: number;
  doctor_id: number;
  chief_complaint: string;
  diagnosis?: string | null;
  prescription?: string | null;
  notes?: string | null;
  follow_up_date?: string | null;
  right_eye_sph?: string | null;
  right_eye_cyl?: string | null;
  right_eye_axis?: number | null;
  right_eye_va?: string | null;
  left_eye_sph?: string | null;
  left_eye_cyl?: string | null;
  left_eye_axis?: number | null;
  left_eye_va?: string | null;
  slit_lamp_enabled: boolean;
  slit_lamp_findings?: string | null;
  fundus_enabled: boolean;
  fundus_findings?: string | null;
  general_findings_enabled: boolean;
  general_findings?: string | null;
  iop_enabled: boolean;
  iop_right?: number | null;
  iop_left?: number | null;
  additional_notes?: string | null;
  distance_prescription_enabled: boolean;
  distance_right_sphere?: string | null;
  distance_right_cylinder?: string | null;
  distance_right_axis?: number | null;
  distance_right_va?: string | null;
  distance_left_sphere?: string | null;
  distance_left_cylinder?: string | null;
  distance_left_axis?: number | null;
  distance_left_va?: string | null;
  distance_add?: string | null;
  near_prescription_enabled: boolean;
  near_right_sphere?: string | null;
  near_right_cylinder?: string | null;
  near_right_axis?: number | null;
  near_right_va?: string | null;
  near_left_sphere?: string | null;
  near_left_cylinder?: string | null;
  near_left_axis?: number | null;
  near_left_va?: string | null;
  near_add?: string | null;
  eyelids_adnexa_right?: string | null;
  eyelids_adnexa_left?: string | null;
  extra_ocular_movements_right?: string | null;
  extra_ocular_movements_left?: string | null;
  cornea_right?: string | null;
  cornea_left?: string | null;
  anterior_chamber_right?: string | null;
  anterior_chamber_left?: string | null;
  conjunctiva_right?: string | null;
  conjunctiva_left?: string | null;
  pupil_right?: string | null;
  pupil_left?: string | null;
  lens_right?: string | null;
  lens_left?: string | null;
  fundus_right?: string | null;
  fundus_left?: string | null;
  advice?: string | null;
  tests_prescribed?: string | null;
  payment_status?: PaymentStatus;
  payment_method?: PaymentMethod | null;
};

export type Visit = VisitPayload & {
  id: number;
  visit_date: string;
  completed_at?: string | null;
  consultation_fee?: string | number | null;
  patient?: Patient | null;
  doctor?: User | null;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type QueueStatus = "waiting" | "in_consultation" | "completed";

export type QueueEntryPayload = {
  patient_id?: number | null;
  first_name?: string | null;
  last_name?: string | null;
  age?: number | null;
  gender?: string | null;
  phone?: string | null;
  address?: string | null;
  queue_date?: string | null;
  reason?: string | null;
};

export type QueueEntry = {
  id: number;
  patient_id: number;
  receptionist_id?: number | null;
  doctor_id?: number | null;
  queue_date: string;
  status: QueueStatus;
  reason?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  completed_visit_id?: number | null;
  payment_status?: PaymentStatus | null;
  payment_method?: PaymentMethod | null;
  consultation_fee?: string | number | null;
  patient?: Patient | null;
  receptionist?: User | null;
  doctor?: User | null;
};

export type OperationStatus = "planned" | "scheduled" | "completed" | "cancelled";
export type TestStatus = "pending" | "done";
export type FitnessStatus = "pending" | "fit" | "not_fit";

export type OperationType = {
  id: number;
  name: string;
  price: string | number;
  is_active: boolean;
  created_at: string;
};

export type OperationTestReport = {
  id: number;
  operation_test_id: number;
  original_filename: string;
  stored_filename: string;
  content_type?: string | null;
  uploaded_at: string;
};

export type OperationTest = {
  id: number;
  operation_id: number;
  test_name: string;
  status: TestStatus;
  test_date?: string | null;
  result?: string | null;
  remarks?: string | null;
  fitness_status?: FitnessStatus | null;
  reports: OperationTestReport[];
};

export type OperationPayload = {
  patient_id: number;
  doctor_id: number;
  operation_type_id: number;
  operation_date: string;
  status: OperationStatus;
  remarks?: string | null;
};

export type Operation = OperationPayload & {
  id: number;
  created_at: string;
  patient?: Patient | null;
  doctor?: User | null;
  operation_type?: OperationType | null;
  tests: OperationTest[];
  ready_for_surgery: boolean;
  payment_status: PaymentStatus;
  payment_method?: PaymentMethod | null;
  operation_charge?: string | number | null;
};

export type FollowUpType = "normal" | "operation_next_day" | "operation_one_week";
export type FollowUpStatus = "scheduled" | "completed" | "cancelled";

export type FollowUp = {
  id: number;
  patient_id: number;
  doctor_id?: number | null;
  operation_id?: number | null;
  follow_up_date: string;
  follow_up_type: FollowUpType;
  status: FollowUpStatus;
  notes?: string | null;
  created_at: string;
  patient?: Patient | null;
  doctor?: User | null;
};

export type CalendarEvent = {
  id: string;
  date: string;
  title: string;
  category: string;
  color: string;
  patient_name: string;
  source_id: number;
};

export type PaymentSetting = {
  id: number;
  setting_key: string;
  amount: string | number;
  updated_at: string;
};

export type TodayIncome = {
  date: string;
  consultation_income: string | number;
  operation_income: string | number;
  total_income: string | number;
};

export type SupplyCategory = "emergency" | "operation" | "general";

export type MedicalSupply = {
  id: number;
  category: SupplyCategory;
  name: string;
  current_stock: number;
  unit: string;
  minimum_stock: number;
  expiry_date?: string | null;
  notes?: string | null;
  updated_at: string;
  is_low_stock: boolean;
  expiry_status: "not_tracked" | "safe" | "expiring_soon" | "expired";
  days_to_expiry?: number | null;
  batches: MedicalSupplyBatch[];
};

export type MedicalSupplyBatch = {
  id: number;
  supply_id: number;
  batch_code: string;
  quantity_initial: number;
  quantity_remaining: number;
  expiry_date: string;
  purchase_date: string;
  notes?: string | null;
  created_at: string;
  expiry_status: "safe" | "expiring_soon" | "expired";
  days_to_expiry?: number | null;
};

export type MedicalSupplyBatchPayload = {
  batch_code: string;
  quantity: number;
  expiry_date: string;
  purchase_date: string;
  notes?: string | null;
};

export type MedicalSupplyPayload = {
  category: SupplyCategory;
  name: string;
  current_stock: number;
  unit: string;
  minimum_stock: number;
  expiry_date?: string | null;
  notes?: string | null;
};

export type Notification = {
  id: number;
  notification_type: "low_stock";
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type Suggestion = {
  id: number;
  doctor_id: number;
  field_name: SuggestionFieldName;
  suggestion_text: string;
  usage_count: number;
  last_used_at: string;
  created_at: string;
};

export type SuggestionFieldName = "chief_complaint" | "diagnosis" | "advice" | "tests_prescribed" | "clinical_notes";

export type Expense = {
  id: number;
  expense_name: string;
  category: string;
  amount: string | number;
  expense_date: string;
  notes?: string | null;
  created_at: string;
};

export type ExpensePayload = {
  expense_name: string;
  category: string;
  amount: number;
  expense_date: string;
  notes?: string | null;
};

export type MoneyBreakdown = {
  consultation_revenue: string | number;
  operation_revenue: string | number;
  total_revenue: string | number;
  total_expenses: string | number;
  net_profit: string | number;
};

export type MonthlyTrendPoint = {
  month: string;
  consultations: number;
  operations: number;
  consultation_revenue: string | number;
  operation_revenue: string | number;
  total_revenue: string | number;
  expenses: string | number;
  profit: string | number;
};

export type AnalyticsSummary = {
  generated_for: string;
  finance: {
    today: MoneyBreakdown;
    week: MoneyBreakdown;
    month: MoneyBreakdown;
    year: MoneyBreakdown;
  };
  consultations: {
    daily_consultations: number;
    weekly_consultations: number;
    monthly_consultations: number;
    total_consultations: number;
  };
  patients: {
    new_patients: number;
    returning_patients: number;
    average_consultations_per_day: number;
    average_operations_per_month: number;
  };
  operation_types: Array<{ operation_type: string; total_count: number; percentage: number }>;
  monthly_trends: MonthlyTrendPoint[];
  expense_breakdown: Array<{ category: string; amount: string | number }>;
};

export type RealtimeEvent = {
  type: string;
  payload: Record<string, unknown>;
};

export type PrescriptionTemplate = {
  id: number;
  doctor_id: number;
  template_name: string;
  clinic_logo?: string | null;
  doctor_signature?: string | null;
  doctor_name?: string | null;
  doctor_qualifications?: string | null;
  doctor_registration_number?: string | null;
  clinic_name?: string | null;
  clinic_address?: string | null;
  clinic_phone?: string | null;
  clinic_timings?: string | null;
  website?: string | null;
  email?: string | null;
  footer_text?: string | null;
  header_background_color: string;
  header_font_color: string;
  footer_background_color: string;
  footer_font_color: string;
  accent_color: string;
  border_color: string;
  font_style: string;
  header_alignment: string;
  logo_position: string;
  updated_at: string;
};
