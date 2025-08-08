from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings
import jwt as pyjwt

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()

# Password hashing

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT utilities

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to get current user/org from token

def get_current_org(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    token = credentials.credentials
    payload = decode_access_token(token)
    org_id: str = payload.get("org_id")
    if org_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return org_id

# Supabase JWT verification

def decode_supabase_jwt(supabase_token: str) -> dict:
    """Verify a Supabase JWT using the project's JWT secret and return the decoded claims.

    Supabase JWTs are signed with HS256 using the JWT secret.
    Raises HTTP 401 on failure.
    """
    try:
        # Supabase uses HS256 with dedicated JWT secret
        claims = pyjwt.decode(
            supabase_token,
            settings.SUPABASE_JWT_SECRET,  # Use dedicated JWT secret
            algorithms=["HS256"],
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
            options={"require": ["exp", "iss", "sub"], "verify_aud": False},  # Don't verify audience
        )
        return claims
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) 