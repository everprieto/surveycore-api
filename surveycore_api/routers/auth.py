"""Authentication router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import User, Role
from ..schemas.auth import UserLogin, UserRegister, Token, UserResponse, MicrosoftToken
from ..auth.password import verify_password, get_password_hash
from ..auth.jwt_handler import create_access_token, decode_access_token
from ..auth.deps import get_current_user
from ..auth.microsoft import validate_microsoft_id_token
from ..auth.permissions import build_user_response

router = APIRouter(prefix="/auth", tags=["authentication"])
_security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    reg_role = db.query(Role).filter(Role.name == (user_data.role or "READ_ONLY")).first()
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role_id=reg_role.id if reg_role else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return build_user_response(new_user, db)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(data={"sub": str(user.id)}), "token_type": "bearer"}


@router.post("/microsoft", response_model=Token)
def microsoft_login(data: MicrosoftToken, db: Session = Depends(get_db)):
    try:
        claims = validate_microsoft_id_token(data.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Microsoft token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = claims.get("email") or claims.get("preferred_username", "")
    name: str = claims.get("name") or email

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email claim not found")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        default_role = db.query(Role).filter(Role.name == "DEFAULT").first()
        user = User(
            name=name,
            email=email,
            role_id=default_role.id if default_role else None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"access_token": create_access_token(data={"sub": str(user.id)}), "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)
    imp_by_id = payload.get("imp_by") if payload else None
    return build_user_response(current_user, db, imp_by_id=imp_by_id)
