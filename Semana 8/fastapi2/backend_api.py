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
    return {"status": "OK", "service": "Backend API 2"}


@app.get("/productos", dependencies=[Depends(verify_gateway)])
def productos(x_authenticated_client: str | None = Header(default=None)):
    return {
        "authenticated_client": x_authenticated_client,
        "productos": [
            {"id": 1, "nombre": "Notebook", "precio": 900000},
            {"id": 2, "nombre": "Monitor", "precio": 250000}
        ]
    }


@app.get("/ordenes", dependencies=[Depends(verify_gateway)])
def ordenes(x_authenticated_client: str | None = Header(default=None)):
    return {
        "authenticated_client": x_authenticated_client,
        "ordenes": [
            {"id": 1001, "estado": "paid"},
            {"id": 1002, "estado": "pending"}
        ]
    }
