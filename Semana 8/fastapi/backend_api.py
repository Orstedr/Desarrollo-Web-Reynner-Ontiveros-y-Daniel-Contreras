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


def verify_gateway(x_gateway_secret: str = Header(default="")):
    """Sólo acepta llamadas que traigan el secreto interno del Gateway."""
    valid = secrets.compare_digest(
        x_gateway_secret.encode(),
        INTERNAL_GATEWAY_SECRET.encode()
    )
    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Solicitud no autorizada desde Gateway"
        )


@app.get("/health")
def health():
    return {"status": "OK", "service": "Backend API"}


@app.get("/products", dependencies=[Depends(verify_gateway)])
def products(x_authenticated_client: str | None = Header(default=None)):
    return {
        "authenticated_client": x_authenticated_client,
        "products": [
            {"id": 1, "name": "Notebook", "price": 900000},
            {"id": 2, "name": "Monitor", "price": 250000}
        ]
    }


@app.get("/orders", dependencies=[Depends(verify_gateway)])
def orders(x_authenticated_client: str | None = Header(default=None)):
    return {
        "authenticated_client": x_authenticated_client,
        "orders": [
            {"id": 1001, "status": "paid"},
            {"id": 1002, "status": "pending"}
        ]
    }
