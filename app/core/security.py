import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from jose import JWTError
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
from app.api.v1.auth.repository import UserRepository
from app.core.config import settings
from app.core.db import get_db
from app.models.user import UserORM
from sqlalchemy.orm import Session

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail= "No autenticado",
    headers= {
        "WWW-Authenticate":"Bearer"
    }
)

def raise_expired_token():
    return HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail= "Token expirado",
    headers= {
        "WWW-Authenticate":"Bearer"
        }
    )
    
def raise_forbidden():
    return HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail= "No tienes permisos suficientes"
    )
    
def invalid_credentials():
    return HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail= "Credenciales invalidas"
    )

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp":expire})
#     token = jwt.encode(payload = to_encode, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
#     return token
def create_access_token(sub:str, minutes: int | None = None) -> str :
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes = minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub":sub, "exp": expire}, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    payload = jwt.decode(jwt = token, key=settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return payload

def get_current_user(db:Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> UserORM:
    
    try:
        payload = decode_token(token)
        sub: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        if not sub or not username:
            raise credentials_exc
        user_id = int(sub)
        
    except ExpiredSignatureError:
        raise_expired_token()
        
    except InvalidTokenError:
        raise credentials_exc
    except PyJWTError:
        raise invalid_credentials()
        
    user = db.get(UserORM, user_id)
    if not user or not user.is_active:
        raise credentials_exc
   
    return user
    
    
def hash_password(plain:str) -> str:
    return password_hash.hash(plain)

def verify_password(plain:str, hashed:str) -> bool:
    return password_hash.verify(plain,hashed)

def require_role(min_role:Literal["user","editor", "admin"]):
    order= {
        "user":0,
        "editor":1,
        "admin":2
    }

    def evaluation(user:UserORM = Depends(get_current_user)) -> UserORM:
        if order[user.role] < order[min_role]:
            raise raise_forbidden()
        return user
    
    return evaluation


async def oauth2_token(form:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    repository = UserRepository(db)
    user = repository.get_by_email(form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise invalid_credentials()
    token = create_access_token(sub = str(user.id))
    return {"acces_token": token, "token_type": "bearer"}
    
        
    
    


require_user = require_role("user")
require_editor = require_role("editor")
require_admin = require_role("admin")

        

