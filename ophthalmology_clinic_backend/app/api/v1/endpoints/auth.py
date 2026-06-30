from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token, create_refresh_token
from app.crud.users import user_crud
from app.models.user import UserRole
from app.schemas.token import Token, TokenPayload, TokenRefreshRequest
from app.schemas.user import PublicRegister, UserCreate, UserRead

router = APIRouter()


@router.post("/login", response_model=Token, summary="Login with email and password")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    login_as: UserRole | None = Form(default=None),
) -> Token:
    user = user_crud.authenticate(db, email=form_data.username, password=form_data.password)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if login_as is not None and user.role != login_as:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{user.role.value.title()} credentials cannot login as {login_as.value.title()}",
        )

    return Token(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Register a receptionist account")
def register(payload: PublicRegister, db: Session = Depends(get_db)) -> UserRead:
    if user_crud.get_by_email(db, email=payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_in = UserCreate(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    return user_crud.create(db, obj_in=user_in)


@router.post("/refresh", response_model=Token, summary="Refresh access token")
def refresh_token(payload: TokenRefreshRequest, db: Session = Depends(get_db)) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )
    try:
        decoded = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**decoded)
    except (JWTError, ValueError):
        raise credentials_exception from None

    if token_data.sub is None or token_data.type != "refresh":
        raise credentials_exception

    user = user_crud.get(db, id=int(token_data.sub))
    if user is None or not user.is_active:
        raise credentials_exception

    return Token(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )
