from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(User).filter(User.email == email.lower()).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            full_name=obj_in.full_name,
            email=obj_in.email.lower(),
            password_hash=get_password_hash(obj_in.password),
            role=obj_in.role,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        if password := update_data.pop("password", None):
            update_data["password_hash"] = get_password_hash(password)
        if email := update_data.get("email"):
            update_data["email"] = email.lower()
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> User | None:
        user = self.get_by_email(db, email=email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user


user_crud = CRUDUser(User)
