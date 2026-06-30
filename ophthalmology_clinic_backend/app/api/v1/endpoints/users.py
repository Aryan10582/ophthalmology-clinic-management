from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.users import user_crud
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()
admin_required = require_roles(UserRole.ADMIN)


@router.get("/me", response_model=UserRead, summary="Get current user")
def read_current_user(current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST))) -> User:
    return current_user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)], summary="Create user")
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if payload.role == UserRole.DOCTOR and db.query(User.id).filter(User.role == UserRole.DOCTOR).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A doctor account already exists")
    if payload.username and user_crud.get_by_username(db, username=payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    if payload.email and user_crud.get_by_email(db, email=payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return user_crud.create(db, obj_in=payload)


@router.get("", response_model=list[UserRead], dependencies=[Depends(admin_required)], summary="List users")
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[User]:
    return user_crud.get_multi(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(admin_required)], summary="Get user by ID")
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = user_crud.get(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead, dependencies=[Depends(admin_required)], summary="Update user")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = user_crud.get(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.role == UserRole.DOCTOR and user.role != UserRole.DOCTOR and db.query(User.id).filter(User.role == UserRole.DOCTOR).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A doctor account already exists")
    if payload.username:
        existing_username = user_crud.get_by_username(db, username=payload.username)
        if existing_username and existing_username.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    if payload.email and user_crud.get_by_email(db, email=payload.email) and payload.email.lower() != user.email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return user_crud.update(db, db_obj=user, obj_in=payload)


@router.delete("/{user_id}", response_model=UserRead, dependencies=[Depends(admin_required)], summary="Deactivate user")
def deactivate_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = user_crud.get(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_crud.update(db, db_obj=user, obj_in=UserUpdate(is_active=False))
