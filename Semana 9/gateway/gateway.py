import os

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


app = FastAPI(
    title="Secure Local API Gateway",
    description=(
        "API Gateway: valida la sesión con el Auth Service, autoriza por rol, "
        "enruta y propaga la identidad a los backends con un secreto compartido"
    )
)

security = HTTPBearer(auto_error=False)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9000")
BACKEND_URL2 = os.getenv("BACKEND_URL2", "http://localhost:9100")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8100")

COOKIE_NAME = "session_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no configurado")

ROUTES = {
    "products": BACKEND_URL,
    "orders": BACKEND_URL,
    "productos": BACKEND_URL2,
    "ordenes": BACKEND_URL2,
}

REQUIRED_ROLE = {
    ("DELETE", "products"): "admin",
    ("DELETE", "productos"): "admin",
}


class LoginRequest(BaseModel):
    username: str
    password: str


def http_client(timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout)


async def get_gateway_secrets() -> dict:
    url = f"{VAULT_ADDR}/v1/secret/data/gateway"
    try:
        async with http_client(5.0) as client:
            response = await client.get(
                url, headers={"X-Vault-Token": VAULT_TOKEN}
            )
    except httpx.RequestError:
        raise HTTPException(500, "No fue posible acceder a Vault")

    if response.status_code != 200:
        raise HTTPException(500, "No fue posible acceder a Vault")

    return response.json()["data"]["data"]


async def call_auth(path: str, payload: dict, introspection_secret: str) -> httpx.Response:
    try:
        async with http_client(5.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}{path}",
                json=payload,
                headers={"X-Gateway-Auth-Secret": introspection_secret},
            )
    except httpx.RequestError:
        raise HTTPException(503, "Authentication Service no disponible")

    if response.status_code != 200:
        raise HTTPException(502, "Error consultando Authentication Service")
    return response


def get_session_token(request: Request, credentials) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    if credentials is not None:
        return credentials.credentials
    return None


async def authenticate_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = get_session_token(request, credentials)
    if token is None:
        raise HTTPException(status_code=401, detail="Sesion requerida")

    gateway_secrets = await get_gateway_secrets()
    response = await call_auth(
        "/introspect", {"token": token}, gateway_secrets["auth_introspection_secret"]
    )

    identity = response.json()
    if not identity.get("active"):
        raise HTTPException(status_code=401, detail="Token invalido o expirado")

    return {
        "token": token,
        "user_id": identity["user_id"],
        "username": identity["username"],
        "roles": identity["roles"],
        "backend_secret": gateway_secrets["backend_shared_secret"],
    }


@app.get("/health")
def health():
    return {"status": "OK", "service": "API Gateway"}


# ---------------------------------------------------------------- /auth/*

@app.post("/auth/login")
async def auth_login(body: LoginRequest):
    try:
        async with http_client(5.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/login",
                json={"username": body.username, "password": body.password},
            )
    except httpx.RequestError:
        raise HTTPException(503, "Authentication Service no disponible")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if response.status_code != 200:
        raise HTTPException(502, "Error consultando Authentication Service")

    data = response.json()
    result = JSONResponse({"status": "logged_in", "expires_in": data["expires_in"]})
    result.set_cookie(
        key=COOKIE_NAME,
        value=data["access_token"],
        max_age=data["expires_in"],
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )
    return result


@app.get("/auth/me")
async def auth_me(auth=Depends(authenticate_session)):
    return {
        "user_id": auth["user_id"],
        "username": auth["username"],
        "roles": auth["roles"],
    }


@app.post("/auth/logout")
async def auth_logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = get_session_token(request, credentials)

    if token:
        gateway_secrets = await get_gateway_secrets()
        await call_auth(
            "/logout", {"token": token}, gateway_secrets["auth_introspection_secret"]
        )

    result = JSONResponse({"status": "logged_out"})
    result.delete_cookie(COOKIE_NAME, path="/")
    return result


# ------------------------------------------------------------------ /api/*

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request, auth=Depends(authenticate_session)):
    resource = path.split("/")[0]
    backend = ROUTES.get(resource)
    if backend is None:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    needed = REQUIRED_ROLE.get((request.method, resource))
    if needed and needed not in auth["roles"]:
        raise HTTPException(status_code=403, detail=f"Se requiere rol {needed}")

    target_url = f"{backend}/{path}"
    body = await request.body()

    gateway_headers = {
        "X-Gateway-Secret": auth["backend_secret"],
        "X-Authenticated-User": auth["user_id"],
        "X-Authenticated-Username": auth["username"],
        "X-Authenticated-Roles": ",".join(auth["roles"]),
    }
    content_type = request.headers.get("content-type")
    if content_type:
        gateway_headers["content-type"] = content_type

    try:
        async with http_client(10.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                content=body,
                headers=gateway_headers,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Backend no disponible")

    response_headers = {}
    if "content-type" in upstream.headers:
        response_headers["content-type"] = upstream.headers["content-type"]

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )
