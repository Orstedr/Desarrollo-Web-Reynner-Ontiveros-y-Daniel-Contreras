import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException


INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no esta configurado")

app = FastAPI(
    title="Protected Backend API 2",
    description="Segundo backend con rutas en español (puerto 9100)"
)

PRODUCTOS = [
    {"id": 1, "nombre": "Notebook", "precio": 900000},
    {"id": 2, "nombre": "Monitor", "precio": 250000},
]


def verify_gateway(x_gateway_secret: str = Header(default="")):
    valid = secrets.compare_digest(
        x_gateway_secret.encode(),
        INTERNAL_GATEWAY_SECRET.encode()
    )
    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Solicitud no autorizada desde Gateway"
        )


def get_identity(
    x_authenticated_user: str | None = Header(default=None),
    x_authenticated_username: str | None = Header(default=None),
    x_authenticated_roles: str | None = Header(default=None),
) -> dict:
    roles = [r.strip() for r in (x_authenticated_roles or "").split(",") if r.strip()]
    return {
        "user_id": x_authenticated_user,
        "username": x_authenticated_username,
        "roles": roles,
    }


def require_admin(identity: dict = Depends(get_identity)) -> dict:
    if "admin" not in identity["roles"]:
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return identity


@app.get("/health")
def health():
    return {"status": "OK", "service": "Backend API 2"}


@app.get("/productos", dependencies=[Depends(verify_gateway)])
def productos(identity: dict = Depends(get_identity)):
    return {
        "authenticated_user": identity["user_id"],
        "username": identity["username"],
        "productos": PRODUCTOS
    }


@app.get("/ordenes", dependencies=[Depends(verify_gateway)])
def ordenes(identity: dict = Depends(get_identity)):
    return {
        "authenticated_user": identity["user_id"],
        "username": identity["username"],
        "ordenes": [
            {"id": 1001, "estado": "paid"},
            {"id": 1002, "estado": "pending"}
        ]
    }


@app.delete("/productos/{producto_id}", dependencies=[Depends(verify_gateway)])
def eliminar_producto(producto_id: int, identity: dict = Depends(require_admin)):
    if not any(p["id"] == producto_id for p in PRODUCTOS):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"eliminado": producto_id, "eliminado_por": identity["username"]}
