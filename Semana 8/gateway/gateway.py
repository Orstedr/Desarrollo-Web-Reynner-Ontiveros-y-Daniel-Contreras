import os
import secrets

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


app = FastAPI(
    title="Secure Local API Gateway",
    description="API Gateway con Bearer Token y secreto compartido hacia los backends"
)

security = HTTPBearer(auto_error=False)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9000")
BACKEND_URL2 = os.getenv("BACKEND_URL2", "http://localhost:9100")

# Los secretos (client_token y backend_shared_secret) se leen desde Vault
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no configurado")

# Recurso -> backend que lo atiende
ROUTES = {
    "products": BACKEND_URL,
    "orders": BACKEND_URL,
    "productos": BACKEND_URL2,
    "ordenes": BACKEND_URL2,
}


async def get_gateway_secrets() -> dict:
    """Lee client_token y backend_shared_secret desde Vault."""
    url = f"{VAULT_ADDR}/v1/secret/data/gateway"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                url, headers={"X-Vault-Token": VAULT_TOKEN}
            )
    except httpx.RequestError:
        raise HTTPException(500, "No fue posible acceder a Vault")

    if response.status_code != 200:
        raise HTTPException(500, "No fue posible acceder a Vault")

    return response.json()["data"]["data"]


async def authenticate_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """401 si falta el token o es incorrecto."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token requerido")

    gateway_secrets = await get_gateway_secrets()

    valid = secrets.compare_digest(
        credentials.credentials.encode(),
        gateway_secrets["client_token"].encode(),
    )
    if not valid:
        raise HTTPException(status_code=401, detail="Token invalido")

    return {
        "client_id": "student-client",
        "backend_secret": gateway_secrets["backend_shared_secret"],
    }


@app.get("/health")
def health():
    return {"status": "OK", "service": "API Gateway"}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request, auth=Depends(authenticate_client)):
    resource = path.split("/")[0]
    backend = ROUTES.get(resource)
    if backend is None:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    target_url = f"{backend}/{path}"
    body = await request.body()

    # Se construyen headers nuevos: NO se reenvía el Authorization del cliente
    gateway_headers = {
        "X-Gateway-Secret": auth["backend_secret"],
        "X-Authenticated-Client": auth["client_id"],
    }
    content_type = request.headers.get("content-type")
    if content_type:
        gateway_headers["content-type"] = content_type

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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
