import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException


INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no esta configurado")

app = FastAPI(
    title="Protected Backend API",
    description="API ubicada en un host diferente al API Gateway"
)

PRODUCTS = [
    {"id": 1, "name": "Notebook", "price": 900000},
    {"id": 2, "name": "Monitor", "price": 250000},
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
    return {"status": "OK", "service": "Backend API"}


@app.get("/products", dependencies=[Depends(verify_gateway)])
def products(identity: dict = Depends(get_identity)):
    return {
        "authenticated_user": identity["user_id"],
        "username": identity["username"],
        "products": PRODUCTS
    }


@app.get("/orders", dependencies=[Depends(verify_gateway)])
def orders(identity: dict = Depends(get_identity)):
    return {
        "authenticated_user": identity["user_id"],
        "username": identity["username"],
        "orders": [
            {"id": 1001, "status": "paid"},
            {"id": 1002, "status": "pending"}
        ]
    }


@app.delete("/products/{product_id}", dependencies=[Depends(verify_gateway)])
def delete_product(product_id: int, identity: dict = Depends(require_admin)):
    if not any(p["id"] == product_id for p in PRODUCTS):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"deleted": product_id, "deleted_by": identity["username"]}
