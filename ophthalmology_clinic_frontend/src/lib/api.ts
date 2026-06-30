import type {
  AnalyticsSummary,
  CalendarEvent,
  ClinicSetupPayload,
  ClinicSetupResult,
  Expense,
  ExpensePayload,
  MedicalSupply,
  MedicalSupplyBatch,
  MedicalSupplyBatchPayload,
  MedicalSupplyPayload,
  Notification,
  Operation,
  OperationPayload,
  OperationTest,
  OperationTestReport,
  OperationType,
  PaymentSetting,
  PaymentUpdate,
  Patient,
  QueueEntry,
  QueueEntryPayload,
  ReceptionistPayload,
  ReceptionistUpdatePayload,
  PrescriptionTemplate,
  RealtimeEvent,
  SetupStatus,
  Suggestion,
  SuggestionFieldName,
  TodayIncome,
  TokenResponse,
  User,
  UserRole,
  Visit,
  VisitPayload
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const ACCESS_TOKEN_KEY = "clinic_access_token";
const REFRESH_TOKEN_KEY = "clinic_refresh_token";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setTokens(tokens: TokenResponse) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function subscribeRealtime(onEvent: (event: RealtimeEvent) => void) {
  const token = getAccessToken();
  if (!token || typeof window === "undefined") return () => undefined;
  const wsUrl = `${API_BASE_URL.replace(/^http/, "ws")}/realtime/ws?token=${encodeURIComponent(token)}`;
  const socket = new WebSocket(wsUrl);
  socket.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as RealtimeEvent);
    } catch {
      // Ignore malformed websocket frames.
    }
  };
  return () => socket.close();
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      message = response.statusText;
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function login(identifier: string, password: string, loginAs?: UserRole) {
  const body = new URLSearchParams();
  body.set("username", identifier);
  body.set("password", password);
  if (loginAs) body.set("login_as", loginAs);

  const tokens = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  }).then(async (response) => {
    if (!response.ok) {
      let message = "Invalid email or password";
      try {
        const body = await response.json();
        message = typeof body.detail === "string" ? body.detail : message;
      } catch {
        message = response.statusText || message;
      }
      throw new ApiError(message, response.status);
    }
    return response.json() as Promise<TokenResponse>;
  });

  setTokens(tokens);
  return tokens;
}

export const api = {
  setupStatus: () => apiFetch<SetupStatus>("/setup/status"),
  completeSetup: (payload: ClinicSetupPayload) =>
    apiFetch<ClinicSetupResult>("/setup", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  receptionists: () => apiFetch<User[]>("/setup/receptionists"),
  createReceptionist: (payload: ReceptionistPayload) =>
    apiFetch<User>("/setup/receptionists", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateReceptionist: (id: number, payload: ReceptionistUpdatePayload) =>
    apiFetch<User>(`/setup/receptionists/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  deleteReceptionist: (id: number) =>
    apiFetch<User>(`/setup/receptionists/${id}`, {
      method: "DELETE"
    }),
  me: () => apiFetch<User>("/users/me"),
  users: () => apiFetch<User[]>("/users"),
  patients: () => apiFetch<Patient[]>("/patients"),
  patient: (id: number) => apiFetch<Patient>(`/patients/${id}`),
  visits: () => apiFetch<Visit[]>("/visits"),
  patientVisits: (patientId: number) => apiFetch<Visit[]>(`/visits/patient/${patientId}`),
  visit: (id: number) => apiFetch<Visit>(`/visits/${id}`),
  createVisit: (payload: VisitPayload) =>
    apiFetch<Visit>("/visits", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  replaceVisit: (id: number, payload: VisitPayload) =>
    apiFetch<Visit>(`/visits/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    }),
  updateVisit: (id: number, payload: Partial<VisitPayload>) =>
    apiFetch<Visit>(`/visits/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  endVisit: (id: number) =>
    apiFetch<Visit>(`/visits/${id}/end`, {
      method: "POST"
    }),
  updateVisitPayment: (id: number, payload: PaymentUpdate) =>
    apiFetch<Visit>(`/visits/${id}/payment`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  queueToday: () => apiFetch<QueueEntry[]>("/queue/today"),
  completedQueueToday: () => apiFetch<QueueEntry[]>("/queue/completed-today"),
  addQueueEntry: (payload: QueueEntryPayload) =>
    apiFetch<QueueEntry>("/queue", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  startQueueEntry: (id: number) =>
    apiFetch<QueueEntry>(`/queue/${id}/start`, {
      method: "POST"
    }),
  completeQueueEntry: (id: number) =>
    apiFetch<QueueEntry>(`/queue/${id}/complete`, {
      method: "POST"
    }),
  operationTypes: (includeArchived = false) => apiFetch<OperationType[]>(`/operations/types${includeArchived ? "?include_archived=true" : ""}`),
  createOperationType: (name: string) =>
    apiFetch<OperationType>("/operations/types", {
      method: "POST",
      body: JSON.stringify({ name, is_active: true })
    }),
  archiveOperationType: (id: number) =>
    apiFetch<OperationType>(`/operations/types/${id}`, {
      method: "DELETE"
    }),
  operations: () => apiFetch<Operation[]>("/operations"),
  operation: (id: number) => apiFetch<Operation>(`/operations/${id}`),
  createOperation: (payload: OperationPayload) =>
    apiFetch<Operation>("/operations", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateOperationTest: (id: number, payload: Partial<OperationTest>) =>
    apiFetch<OperationTest>(`/operations/tests/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  addOperationTest: (operationId: number, payload: Partial<OperationTest> & { test_name: string }) =>
    apiFetch<OperationTest>(`/operations/${operationId}/tests`, {
      method: "POST",
      body: JSON.stringify({
        test_name: payload.test_name,
        status: payload.status ?? "pending",
        test_date: payload.test_date ?? null,
        result: payload.result ?? null,
        remarks: payload.remarks ?? null,
        fitness_status: payload.fitness_status ?? null
      })
    }),
  updateOperationPayment: (id: number, payload: PaymentUpdate) =>
    apiFetch<Operation>(`/operations/${id}/payment`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  uploadOperationReport: (testId: number, file: File) => {
    const body = new FormData();
    body.set("file", file);
    return apiFetch<OperationTestReport>(`/operations/tests/${testId}/reports`, {
      method: "POST",
      body
    });
  },
  deleteOperationReport: (reportId: number) =>
    apiFetch<OperationTestReport>(`/operations/reports/${reportId}`, {
      method: "DELETE"
    }),
  operationReportUrl: (reportId: number) => `${API_BASE_URL}/operations/reports/${reportId}/download`,
  paymentSettings: () => apiFetch<PaymentSetting[]>("/payments/settings"),
  updatePaymentSetting: (settingKey: string, amount: number) =>
    apiFetch<PaymentSetting>(`/payments/settings/${settingKey}`, {
      method: "PATCH",
      body: JSON.stringify({ amount })
    }),
  updateOperationTypePrice: (operationTypeId: number, amount: number) =>
    apiFetch<OperationType>(`/payments/operation-types/${operationTypeId}/price`, {
      method: "PATCH",
      body: JSON.stringify({ amount })
    }),
  todayIncome: () => apiFetch<TodayIncome>("/payments/today-income"),
  supplies: () => apiFetch<MedicalSupply[]>("/supplies"),
  createSupply: (payload: MedicalSupplyPayload) =>
    apiFetch<MedicalSupply>("/supplies", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateSupply: (id: number, payload: Partial<MedicalSupplyPayload>) =>
    apiFetch<MedicalSupply>(`/supplies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  addSupplyBatch: (id: number, payload: MedicalSupplyBatchPayload) =>
    apiFetch<MedicalSupplyBatch>(`/supplies/${id}/batches`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  deleteSupplyBatch: (id: number) =>
    apiFetch<MedicalSupplyBatch>(`/supplies/batches/${id}`, {
      method: "DELETE"
    }),
  consumeSupply: (id: number, quantity: number, notes?: string | null) =>
    apiFetch<MedicalSupply>(`/supplies/${id}/consume`, {
      method: "POST",
      body: JSON.stringify({ quantity, notes: notes ?? null })
    }),
  notifications: () => apiFetch<Notification[]>("/supplies/notifications"),
  analyticsSummary: () => apiFetch<AnalyticsSummary>("/analytics-finance/summary"),
  expenses: (query = "") => apiFetch<Expense[]>(`/analytics-finance/expenses${query}`),
  expenseCategories: () => apiFetch<string[]>("/analytics-finance/expenses/categories"),
  createExpense: (payload: ExpensePayload) =>
    apiFetch<Expense>("/analytics-finance/expenses", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateExpense: (id: number, payload: Partial<ExpensePayload>) =>
    apiFetch<Expense>(`/analytics-finance/expenses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  deleteExpense: (id: number) =>
    apiFetch<Expense>(`/analytics-finance/expenses/${id}`, {
      method: "DELETE"
    }),
  financialReportUrl: (startDate: string, endDate: string) => `${API_BASE_URL}/analytics-finance/reports/export?start_date=${startDate}&end_date=${endDate}`,
  suggestions: (fieldName: SuggestionFieldName, query: string) =>
    apiFetch<Suggestion[]>(`/suggestions/search?field_name=${fieldName}&q=${encodeURIComponent(query)}`),
  saveSuggestion: (fieldName: SuggestionFieldName, suggestionText: string) =>
    apiFetch<Suggestion>("/suggestions", {
      method: "POST",
      body: JSON.stringify({ field_name: fieldName, suggestion_text: suggestionText })
    }),
  prescriptionTemplate: () => apiFetch<PrescriptionTemplate>("/settings/prescription-template"),
  updatePrescriptionTemplate: (payload: PrescriptionTemplate) =>
    apiFetch<PrescriptionTemplate>("/settings/prescription-template", {
      method: "PUT",
      body: JSON.stringify(payload)
    }),
  calendarEvents: (filter = "all") => apiFetch<CalendarEvent[]>(`/calendar/events?filter=${filter}`)
};
