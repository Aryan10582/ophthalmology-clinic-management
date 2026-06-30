from app.crud.base import CRUDBase
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


expense_crud = CRUDBase[Expense, ExpenseCreate, ExpenseUpdate](Expense)
