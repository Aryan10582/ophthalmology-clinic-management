from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.realtime import realtime_manager
from sqlalchemy import func

from app.crud.analytics import analytics_summary, _period_breakdown
from app.crud.expenses import expense_crud
from app.models.expense import Expense
from app.models.user import User, UserRole
from app.schemas.analytics import AnalyticsSummary
from app.schemas.expense import DEFAULT_EXPENSE_CATEGORIES, ExpenseCreate, ExpenseRead, ExpenseUpdate

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.get("/summary", response_model=AnalyticsSummary, summary="Analytics and finance summary")
def summary(db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> AnalyticsSummary:
    return analytics_summary(db, today=date.today(), is_demo_data=current_user.is_demo_account)


@router.get("/expenses/categories", response_model=list[str], summary="Expense categories")
def expense_categories(db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> list[str]:
    custom = [row[0] for row in db.query(Expense.category).filter(Expense.is_demo_data == current_user.is_demo_account).distinct().order_by(Expense.category.asc()).all()]
    return sorted(set(DEFAULT_EXPENSE_CATEGORIES + custom))


@router.get("/expenses", response_model=list[ExpenseRead], dependencies=[Depends(doctor_or_admin_required)], summary="Expense history")
def list_expenses(
    search: str | None = None,
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_or_admin_required),
) -> list[Expense]:
    query = db.query(Expense).filter(Expense.is_demo_data == current_user.is_demo_account)
    if search:
        query = query.filter(Expense.expense_name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    return list(query.order_by(Expense.expense_date.desc(), Expense.id.desc()).limit(1000).all())


@router.post("/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED, summary="Create expense")
def create_expense(payload: ExpenseCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Expense:
    payload = payload.model_copy(update={"is_demo_data": current_user.is_demo_account})
    expense = expense_crud.create(db, obj_in=payload)
    background_tasks.add_task(realtime_manager.broadcast, "finance.updated", {"expense_id": expense.id})
    return expense


@router.patch("/expenses/{expense_id}", response_model=ExpenseRead, summary="Update expense")
def update_expense(expense_id: int, payload: ExpenseUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Expense:
    expense = expense_crud.get(db, id=expense_id)
    if expense is None or expense.is_demo_data != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    expense = expense_crud.update(db, db_obj=expense, obj_in=payload)
    background_tasks.add_task(realtime_manager.broadcast, "finance.updated", {"expense_id": expense.id})
    return expense


@router.delete("/expenses/{expense_id}", response_model=ExpenseRead, summary="Delete expense")
def delete_expense(expense_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Expense:
    expense = expense_crud.get(db, id=expense_id)
    if expense is None or expense.is_demo_data != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    expense = expense_crud.remove(db, id=expense_id)
    background_tasks.add_task(realtime_manager.broadcast, "finance.updated", {"expense_id": expense.id})
    return expense


@router.get("/reports/export", summary="Export financial report")
def export_report(start_date: date = Query(...), end_date: date = Query(...), db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Response:
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="start_date must be before end_date")
    breakdown = _period_breakdown(db, start=start_date, end=end_date, is_demo_data=current_user.is_demo_account)
    expense_rows = (
        db.query(Expense.category, func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.expense_date >= start_date, Expense.expense_date <= end_date, Expense.is_demo_data == current_user.is_demo_account)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    lines = [
        "Ophthalmology Clinic Financial Report",
        f"Period: {start_date.isoformat()} to {end_date.isoformat()}",
        "",
        f"Total revenue: {breakdown.total_revenue}",
        f"Consultation revenue: {breakdown.consultation_revenue}",
        f"Operation revenue: {breakdown.operation_revenue}",
        f"Total expenses: {breakdown.total_expenses}",
        f"Net profit: {breakdown.net_profit}",
        "",
        "Expense breakdown:",
        *[f"{category}: {amount}" for category, amount in expense_rows],
    ]
    return Response("\n".join(lines), media_type="text/plain")
