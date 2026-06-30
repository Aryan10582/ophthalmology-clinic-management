from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import distinct, extract, func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.operation import Operation, OperationType
from app.models.patient import Patient
from app.models.payment import PaymentStatus
from app.models.visit import Visit
from app.schemas.analytics import (
    AnalyticsMetricSet,
    AnalyticsSummary,
    ConsultationAnalytics,
    ExpenseCategoryAnalytics,
    MoneyBreakdown,
    MonthlyTrendPoint,
    OperationTypeAnalytics,
    PatientAnalytics,
)


def _money(value) -> Decimal:
    return Decimal(value or 0)


def _period_breakdown(db: Session, *, start: date, end: date) -> MoneyBreakdown:
    consultation_revenue = _money(
        db.query(func.coalesce(func.sum(Visit.consultation_fee), 0))
        .filter(func.date(Visit.completed_at) >= start, func.date(Visit.completed_at) <= end, Visit.payment_status == PaymentStatus.PAID)
        .scalar()
    )
    operation_revenue = _money(
        db.query(func.coalesce(func.sum(Operation.operation_charge), 0))
        .filter(Operation.operation_date >= start, Operation.operation_date <= end, Operation.payment_status == PaymentStatus.PAID)
        .scalar()
    )
    expenses = _money(
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.expense_date >= start, Expense.expense_date <= end)
        .scalar()
    )
    total_revenue = consultation_revenue + operation_revenue
    return MoneyBreakdown(
        consultation_revenue=consultation_revenue,
        operation_revenue=operation_revenue,
        total_revenue=total_revenue,
        total_expenses=expenses,
        net_profit=total_revenue - expenses,
    )


def analytics_summary(db: Session, *, today: date) -> AnalyticsSummary:
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    trailing_year_start = today - timedelta(days=365)

    finance = AnalyticsMetricSet(
        today=_period_breakdown(db, start=today, end=today),
        week=_period_breakdown(db, start=week_start, end=today),
        month=_period_breakdown(db, start=month_start, end=today),
        year=_period_breakdown(db, start=year_start, end=today),
    )

    daily_consultations = db.query(Visit).filter(func.date(Visit.completed_at) == today).count()
    weekly_consultations = db.query(Visit).filter(func.date(Visit.completed_at) >= week_start, func.date(Visit.completed_at) <= today).count()
    monthly_consultations = db.query(Visit).filter(func.date(Visit.completed_at) >= month_start, func.date(Visit.completed_at) <= today).count()
    total_consultations = db.query(Visit).count()

    new_patients = db.query(Patient).filter(func.date(Patient.created_at) >= month_start, func.date(Patient.created_at) <= today).count()
    returning_patients = (
        db.query(Visit.patient_id)
        .filter(func.date(Visit.completed_at) >= month_start, func.date(Visit.completed_at) <= today)
        .group_by(Visit.patient_id)
        .having(func.count(Visit.id) > 1)
        .count()
    )
    consultation_days = max((today - trailing_year_start).days, 1)
    consultations_year = db.query(Visit).filter(func.date(Visit.completed_at) >= trailing_year_start, func.date(Visit.completed_at) <= today).count()
    operations_year = db.query(Operation).filter(Operation.operation_date >= trailing_year_start, Operation.operation_date <= today).count()

    total_operations = db.query(Operation).filter(Operation.operation_date >= trailing_year_start, Operation.operation_date <= today).count()
    operation_rows = (
        db.query(OperationType.name, func.count(Operation.id))
        .join(OperationType, Operation.operation_type_id == OperationType.id)
        .filter(Operation.operation_date >= trailing_year_start, Operation.operation_date <= today)
        .group_by(OperationType.name)
        .order_by(func.count(Operation.id).desc())
        .all()
    )
    operation_types = [
        OperationTypeAnalytics(operation_type=name, total_count=count, percentage=(count / total_operations * 100) if total_operations else 0)
        for name, count in operation_rows
    ]

    monthly_trends: list[MonthlyTrendPoint] = []
    for offset in range(11, -1, -1):
        month = _add_months(today.replace(day=1), -offset)
        next_month = _add_months(month, 1)
        month_end = next_month - timedelta(days=1)
        breakdown = _period_breakdown(db, start=month, end=month_end)
        monthly_trends.append(
            MonthlyTrendPoint(
                month=month.strftime("%Y-%m"),
                consultations=db.query(Visit).filter(func.date(Visit.completed_at) >= month, func.date(Visit.completed_at) <= month_end).count(),
                operations=db.query(Operation).filter(Operation.operation_date >= month, Operation.operation_date <= month_end).count(),
                consultation_revenue=breakdown.consultation_revenue,
                operation_revenue=breakdown.operation_revenue,
                total_revenue=breakdown.total_revenue,
                expenses=breakdown.total_expenses,
                profit=breakdown.net_profit,
            )
        )

    expense_breakdown = [
        ExpenseCategoryAnalytics(category=category, amount=_money(amount))
        for category, amount in (
            db.query(Expense.category, func.coalesce(func.sum(Expense.amount), 0))
            .filter(Expense.expense_date >= year_start, Expense.expense_date <= today)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
            .all()
        )
    ]

    return AnalyticsSummary(
        generated_for=today,
        finance=finance,
        consultations=ConsultationAnalytics(
            daily_consultations=daily_consultations,
            weekly_consultations=weekly_consultations,
            monthly_consultations=monthly_consultations,
            total_consultations=total_consultations,
        ),
        patients=PatientAnalytics(
            new_patients=new_patients,
            returning_patients=returning_patients,
            average_consultations_per_day=round(consultations_year / consultation_days, 2),
            average_operations_per_month=round(operations_year / 12, 2),
        ),
        operation_types=operation_types,
        monthly_trends=monthly_trends,
        expense_breakdown=expense_breakdown,
    )


def _add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)
