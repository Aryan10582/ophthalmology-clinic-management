from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MoneyBreakdown(BaseModel):
    consultation_revenue: Decimal
    operation_revenue: Decimal
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal


class AnalyticsMetricSet(BaseModel):
    today: MoneyBreakdown
    week: MoneyBreakdown
    month: MoneyBreakdown
    year: MoneyBreakdown


class ConsultationAnalytics(BaseModel):
    daily_consultations: int
    weekly_consultations: int
    monthly_consultations: int
    total_consultations: int


class PatientAnalytics(BaseModel):
    new_patients: int
    returning_patients: int
    average_consultations_per_day: float
    average_operations_per_month: float


class OperationTypeAnalytics(BaseModel):
    operation_type: str
    total_count: int
    percentage: float


class MonthlyTrendPoint(BaseModel):
    month: str
    consultations: int = 0
    operations: int = 0
    consultation_revenue: Decimal = Decimal("0")
    operation_revenue: Decimal = Decimal("0")
    total_revenue: Decimal = Decimal("0")
    expenses: Decimal = Decimal("0")
    profit: Decimal = Decimal("0")


class ExpenseCategoryAnalytics(BaseModel):
    category: str
    amount: Decimal


class AnalyticsSummary(BaseModel):
    generated_for: date
    finance: AnalyticsMetricSet
    consultations: ConsultationAnalytics
    patients: PatientAnalytics
    operation_types: list[OperationTypeAnalytics]
    monthly_trends: list[MonthlyTrendPoint]
    expense_breakdown: list[ExpenseCategoryAnalytics]
