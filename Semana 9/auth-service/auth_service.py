import os
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


AUTH_INTROSPECTION_SECRET = os.getenv("AUTH_INTROSPECTION_SECRET")

if not AUTH_INTROSPECTION_SECRET:
    raise RuntimeError("AUTH_INTROSPECTION_SECRET no esta configurado")

TOKEN_LIFETIME_MINUTES = 15

app = FastAPI(
    title="Authentication Service",
    description="Servicio simple de autenticación y emisión de tokens"
)

hasher = PasswordHasher()

USERS = {
    "ana": {
        "user_id": "USR-001",
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$ppHSfoE5knwjguhmRpFsXQ$++gF1nTtqCVsM8jAkKA3xWXs3HMzn7vXMDjkkpwzPPI",
        "roles": ["user"],
    },
    "pedro": {
        "user_id": "USR-002",
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$8nm3WDeWEU8ez6Muteqq7w$oaTHB66K6O00TvW3ZN+59id3kMYnkBCcs2YlTp80PhI",
        "roles": ["user"],
    },
    "ernesto": {
        "user_id": "USR-003",
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$hvImccogHtEngmJxWSuQCQ$SOyz7m12FzYmdhiiP5sGf/Wa8hIYXgs5t0J7XTABFLk",
        "roles": ["user", "admin"],
    },
}


DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$cl7ZcJbdjN/ka9gFEBTP9g$fDcjRi0spGIsEL/1FcT8i6cX8um7zidVbLSLYVJeSi4"

SESSIONS: dict[str, dict] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class IntrospectionRequest(BaseModel):
    token: str


def verify_gateway(x_gateway_auth_secret: str):
    """403 si quien llama no presenta el secreto del Gateway."""
    valid = secrets.compare_digest(
        x_gateway_auth_secret.encode(),
        AUTH_INTROSPECTION_SECRET.encode(),
    )
    if not valid:
        raise HTTPException(status_code=403, detail="Gateway no autorizado")


def _password_ok(stored_hash: str, password: str) -> bool:
    try:
        return hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


@app.get("/health")
def health():
    return {"status": "OK", "service": "Authentication Service"}


@app.post("/login")
def login(request: LoginRequest):
    user = USERS.get(request.username)

    if user is None:
        _password_ok(DUMMY_HASH, request.password)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not _password_ok(user["password_hash"], request.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    access_token = secrets.token_urlsafe(32)
    expiration = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_LIFETIME_MINUTES)

    SESSIONS[access_token] = {
        "user_id": user["user_id"],
        "username": request.username,
        "roles": list(user["roles"]),
        "expires_at": expiration,
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": TOKEN_LIFETIME_MINUTES * 60,
    }


@app.post("/introspect")
def introspect(
    request: IntrospectionRequest,
    x_gateway_auth_secret: str = Header(default=""),
):
    verify_gateway(x_gateway_auth_secret)

    session = SESSIONS.get(request.token)
    if session is None:
        return {"active": False}

    if datetime.now(timezone.utc) > session["expires_at"]:
        SESSIONS.pop(request.token, None)
        return {"active": False}

    return {
        "active": True,
        "user_id": session["user_id"],
        "username": session["username"],
        "roles": session["roles"],
        "expires_at": session["expires_at"].isoformat(),
    }


@app.post("/logout")
def logout(
    request: IntrospectionRequest,
    x_gateway_auth_secret: str = Header(default=""),
):
    verify_gateway(x_gateway_auth_secret)
    SESSIONS.pop(request.token, None)
    return {"active": False, "message": "Sesion finalizada"}
