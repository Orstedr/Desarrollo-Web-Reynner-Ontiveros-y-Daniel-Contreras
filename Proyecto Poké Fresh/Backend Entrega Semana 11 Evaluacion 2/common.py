import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pymongo import MongoClient
from pymongo.errors import PyMongoError

PORTS = dict(gateway=8000, auth=8100, inventory=9000, orders=9100,
             clients=9200, payments=9300, graphql=9400)
BASE = "/api/v1"
STAFF = ("admin", "cajero", "despacho", "dueno")
AUTHENTICATED = ("cliente", *STAFF)
LOG = logging.getLogger("uvicorn.error")
SERVICE = os.getenv("PF_SERVICE", "")
SECRETS = {}
HTTP = httpx.Client(timeout=4, trust_env=False)
MONGO_HOST = "localhost:27017"
VAULT_ADDR = "http://127.0.0.1:8200"
mongo = MongoClient(f"mongodb://{MONGO_HOST}/?replicaSet=pf",
                    serverSelectionTimeoutMS=2500, tz_aware=True, connect=False)
db = mongo.pokefresh


def now():
    return datetime.now(timezone.utc)


def uid():
    return uuid4().hex


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def opaque():
    return secrets.token_urlsafe(32)


def policy(*roles, private=False, callers=()):
    def decorate(fn):
        fn.roles = roles
        fn.private = private
        fn.callers = callers
        return fn
    return decorate


def vault_settings():
    response = HTTP.get(
        f"{VAULT_ADDR}/v1/secret/data/pokefresh/{SERVICE}",
        headers={"X-Vault-Token": os.environ["PF_VAULT_TOKEN"]},
    )
    response.raise_for_status()
    SECRETS.update(response.json()["data"]["data"])


def upstream(target, method, path, identity=None, correlation=None, checkout_key=None, **kwargs):
    headers = {"X-PF-Caller": SERVICE, "X-PF-Secret": SECRETS[f"to_{target}"],
               "X-Request-ID": correlation or uid()}
    if kwargs.get("content") or "json" in kwargs:
        headers["Content-Type"] = "application/json"
    if checkout_key is not None:
        headers["Idempotency-Key"] = checkout_key
    if identity:
        headers.update({"X-PF-User": identity["id"], "X-PF-Role": identity["role"]})
    try:
        return HTTP.request(method, f"http://127.0.0.1:{PORTS[target]}{path}",
                            headers=headers, timeout=20 if SERVICE == "gateway" and target == "orders" else 4,
                            **kwargs)
    except httpx.RequestError:
        raise HTTPException(503, "Dependencia privada no disponible") from None


def upstream_json(target, method, path, **kwargs):
    response = upstream(target, method, path, **kwargs)
    if response.status_code >= 400:
        detail = response.json().get("detail") if response.status_code < 500 else "Dependencia privada no disponible"
        raise HTTPException(response.status_code if response.status_code < 500 else 503, detail)
    return response.json()


def identity(request):
    return request.state.identity


def role(request):
    return (identity(request) or {}).get("role")


class PrivateRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        endpoint = self.endpoint

        async def handle(request):
            caller = request.headers.get("X-PF-Caller", "")
            expected = SECRETS.get(f"from_{caller}")
            offered = request.headers.get("X-PF-Secret", "")
            if not expected or not secrets.compare_digest(offered.encode(), expected.encode()):
                raise HTTPException(403, "Credencial interna requerida")
            callers = getattr(endpoint, "callers", ())
            allowed = (caller in callers if callers else
                       caller == "gateway" or
                       (caller == "graphql" and getattr(endpoint, "graphql_read", False)))
            if not allowed:
                raise HTTPException(403, "Operación interna no autorizada")
            user = request.headers.get("X-PF-User")
            verified_role = request.headers.get("X-PF-Role")
            request.state.identity = {"id": user, "role": verified_role} if user and verified_role else None
            roles = getattr(endpoint, "roles", ())
            if roles and role(request) not in roles:
                raise HTTPException(403, "Rol no autorizado")
            return await original(request)

        return handle


def graphql_read(fn):
    fn.graphql_read = True
    return fn


def standard_app(title, private=True, lifespan=None):
    app = FastAPI(title=title, lifespan=lifespan,
                  docs_url=None if private else "/docs",
                  redoc_url=None, openapi_url=None if private else "/openapi.json")

    @app.exception_handler(RequestValidationError)
    async def invalid(_request, exc):
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": error["loc"], "type": error["type"]} for error in exc.errors()
        ]})

    @app.exception_handler(PyMongoError)
    async def database_error(_request, _exc):
        return JSONResponse(status_code=503, content={"detail": "Persistencia no disponible"})

    @app.middleware("http")
    async def trace(request, call_next):
        supplied = request.headers.get("X-Request-ID", "") if private else ""
        request.state.correlation = supplied if re.fullmatch(r"[a-f0-9]{32}", supplied) else uid()
        try:
            response = await call_next(request)
        except Exception:
            LOG.error("%s rid=%s error interno", title, request.state.correlation)
            response = JSONResponse(status_code=500, content={"detail": "Error interno"})
        response.headers["X-Request-ID"] = request.state.correlation
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        route = request.scope.get("route")
        LOG.info("%s rid=%s %s %s %s", title, request.state.correlation,
                 request.method, getattr(route, "path", "-"), response.status_code)
        return response

    return app


def transaction(fn):
    with mongo.start_session() as session:
        return session.with_transaction(fn)


def fetch(collection, record_id, session=None):
    doc = collection.find_one({"_id": record_id}, session=session)
    if doc is None:
        raise HTTPException(404, "Recurso no encontrado")
    return doc


def public_id(doc, omit=()):
    return {"id": doc["_id"], **{key: value for key, value in doc.items()
                                  if key != "_id" and key not in omit}}
