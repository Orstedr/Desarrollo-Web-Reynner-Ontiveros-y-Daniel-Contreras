import json
import re
from collections import deque
from time import monotonic
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.security import HTTPBearer
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool

from accounts import auth, clients
from commerce import orders, payments
from common import (AUTHENTICATED, PORTS, SERVICE, PrivateRoute, mongo, policy,
                    standard_app, upstream, upstream_json, vault_settings)
from graph import graphql
from inventory import inventory

ROUTERS = dict(auth=auth, clients=clients, orders=orders, payments=payments,
               graphql=graphql, inventory=inventory)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")
LIMITED_AUTH_ROUTES = {"/auth/login", "/auth/verify", "/auth/resend", "/auth/recovery",
                       "/auth/reset", "/api/v1/clients"}
AUTH_CALLS = deque()


def limit_auth():
    current = monotonic()
    while AUTH_CALLS and AUTH_CALLS[0] <= current - 60:
        AUTH_CALLS.popleft()
    if len(AUTH_CALLS) >= 40:
        raise HTTPException(429, "Demasiadas solicitudes de cuenta; espere un minuto",
                            headers={"Retry-After": "60"})
    AUTH_CALLS.append(current)


@asynccontextmanager
async def lifespan(_app):
    await run_in_threadpool(vault_settings)
    yield
    mongo.close()


def private_app():
    app = standard_app(f"Poké Fresh {SERVICE}", lifespan=lifespan)
    app.include_router(ROUTERS[SERVICE])
    health = APIRouter(route_class=PrivateRoute)

    @health.get("/internal/health")
    @policy(private=True)
    def check():
        if SERVICE != "graphql":
            mongo.admin.command("ping")
        return {"service": SERVICE, "status": "ok"}

    app.include_router(health)
    return app


bearer = HTTPBearer(auto_error=False)


async def identify(request):
    credentials = await bearer(request)
    if credentials is None or not TOKEN_PATTERN.fullmatch(credentials.credentials):
        raise HTTPException(401, "Se requiere token Bearer válido",
                            headers={"WWW-Authenticate": "Bearer"})
    token = credentials.credentials
    user = await run_in_threadpool(upstream_json, "auth", "POST", "/auth/introspect",
                                   correlation=request.state.correlation, json={"token": token})
    return user, token


async def limited_body(request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 32_768:
            raise HTTPException(413, "Cuerpo mayor a 32 KiB")
    return bytes(body)


class ProxyRoute(APIRoute):
    def get_route_handler(self):
        endpoint = self.endpoint
        roles = getattr(endpoint, "roles", ())

        async def forward(request):
            if self.path in LIMITED_AUTH_ROUTES:
                limit_auth()
            user = token = None
            if roles:
                user, token = await identify(request)
                if user["role"] not in roles:
                    raise HTTPException(403, "Rol no autorizado")
            target = TARGETS[endpoint]
            body = await limited_body(request)
            if self.path == "/auth/logout":
                body = json.dumps({"token": token}).encode()
            media = request.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if body and self.path != "/auth/logout" and media != "application/json":
                raise HTTPException(415, "Use application/json")
            response = await run_in_threadpool(
                upstream, target, request.method, request.scope["raw_path"].decode("ascii"),
                identity=user, correlation=request.state.correlation,
                params=list(request.query_params.multi_items()), content=body,
                checkout_key=request.headers.get("Idempotency-Key") if self.path == "/api/v1/orders" else None
            )
            headers = {key: response.headers[key] for key in ("content-type", "content-disposition")
                       if key in response.headers}
            return Response(response.content, status_code=response.status_code, headers=headers)

        return forward


TARGETS = {route.endpoint: target for target, router in ROUTERS.items()
           for route in router.routes if not getattr(route.endpoint, "private", False)}


def gateway_app():
    app = standard_app("Poké Fresh API Gateway", private=False, lifespan=lifespan)
    for router in ROUTERS.values():
        for route in router.routes:
            if route.endpoint not in TARGETS:
                continue
            roles = getattr(route.endpoint, "roles", ())
            extra = {"security": [{"Bearer": []}]} if roles else {}
            app.router.add_api_route(route.path, route.endpoint, methods=route.methods,
                                     route_class_override=ProxyRoute, status_code=route.status_code,
                                     response_class=route.response_class, responses=route.responses,
                                     tags=[TARGETS[route.endpoint]], openapi_extra=extra)

    @app.get("/auth/me", openapi_extra={"security": [{"Bearer": []}]}, tags=["auth"])
    async def me(request: Request):
        user, _token = await identify(request)
        return user

    @app.get("/health", tags=["infra"])
    def health(request: Request):
        checks = {}
        for target in PORTS:
            if target == "gateway":
                continue
            try:
                upstream_json(target, "GET", "/internal/health", correlation=request.state.correlation)
                checks[target] = "ok"
            except HTTPException:
                checks[target] = "unavailable"
        good = all(status == "ok" for status in checks.values())
        body = {"status": "ok" if good else "degraded", "services": checks}
        return Response(json.dumps(body), status_code=200 if good else 503, media_type="application/json")

    default_schema = app.openapi

    def schema():
        result = default_schema()
        result.setdefault("components", {}).setdefault("securitySchemes", {})["Bearer"] = {
            "type": "http", "scheme": "bearer"}
        return result

    app.openapi = schema
    return app


app = gateway_app() if SERVICE == "gateway" else private_app()
