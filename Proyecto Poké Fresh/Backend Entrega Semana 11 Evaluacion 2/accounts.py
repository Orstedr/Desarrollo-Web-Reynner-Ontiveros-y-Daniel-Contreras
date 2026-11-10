import re
from datetime import date, timedelta
from typing import Annotated, Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from common import (AUTHENTICATED, BASE, PrivateRoute, db, digest, fetch,
                    identity, now, opaque, policy, public_id, transaction, uid, upstream_json)

auth = APIRouter(route_class=PrivateRoute)
clients = APIRouter(route_class=PrivateRoute)
HASHER = PasswordHasher(type=Type.ID)
STAFF_MAIL = "admin@pokefresh.test"
Email = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True,
                 max_length=254, pattern=r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+$")]
Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Token = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{43}$")]
StaffRole = Literal["admin", "cajero", "despacho", "dueno"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Model):
    email: Email
    password: Password


class TokenBody(Model):
    token: Token


class EmailBody(Model):
    email: Email


class Reset(TokenBody):
    password: Password


class Profile(Model):
    nombre: Text
    direccion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=180)]
    comuna: Text
    provincia: Text
    region: Text
    nacimiento: date
    sexo: Literal["masculino", "femenino", "otro"]
    telefono: Annotated[str, StringConstraints(strip_whitespace=True, max_length=22)]

    @field_validator("nombre")
    @classmethod
    def full_name(cls, value):
        if len(value.split()) < 2 or not any(c.isalpha() for c in value):
            raise ValueError("Ingrese nombre completo")
        return value

    @field_validator("nacimiento")
    @classmethod
    def birth(cls, value):
        if not date(1900, 1, 1) <= value < date.today():
            raise ValueError("Fecha de nacimiento fuera de rango")
        return value

    @field_validator("telefono")
    @classmethod
    def phone(cls, value):
        value = re.sub(r"[ ()-]", "", value)
        if not re.fullmatch(r"\+56[2-9][0-9]{8}", value):
            raise ValueError("Teléfono chileno en formato +56")
        return value


class Registration(Profile, Login):
    run: Annotated[str, StringConstraints(max_length=16)]

    @field_validator("run")
    @classmethod
    def normalize_run(cls, value):
        normalized = value.replace(".", "").strip().upper()
        if not re.fullmatch(r"[1-9][0-9]{5,7}-[0-9K]", normalized):
            raise ValueError("Formato RUN inválido")
        body, dv = normalized.split("-")
        remainder = 11 - sum(int(d) * (2 + i % 6) for i, d in enumerate(reversed(body))) % 11
        expected = "K" if remainder == 10 else "0" if remainder == 11 else str(remainder)
        if dv != expected:
            raise ValueError("Dígito verificador inválido")
        return normalized


class StaffRegistration(Login):
    nombre: Text
    role: StaffRole


class StaffUpdate(Model):
    nombre: Text
    role: StaffRole
    active: bool


class Active(Model):
    active: bool


def client_view(doc):
    profile = db.client_profiles.find_one({"_id": doc["_id"]}, {"_id": 0})
    return {"id": doc["_id"], "email": doc["email"], "verified": doc["verified"],
            "active": doc["active"], **(profile if profile is not None else doc["profile"])}


def account_view(doc):
    return {"id": doc["_id"], "nombre": doc["nombre"], "role": doc["role"],
            "active": doc["active"], "verified": doc["verified"]}


def issue_mail(user, kind, session):
    code = opaque()
    expiry = now() + timedelta(minutes=30)
    db.users.update_one({"_id": user["_id"]}, {"$set": {
        kind: {"digest": digest(code), "expires_at": expiry}
    }}, session=session)
    db.outbox.delete_many({"recipient_id": user["_id"], "kind": kind}, session=session)
    db.outbox.insert_one({"_id": uid(), "recipient_id": user["_id"], "kind": kind,
                          "email": user["email"], "code": code, "adapter": "local",
                          "expires_at": expiry, "created_at": now()}, session=session)


def check_login(body):
    user = db.users.find_one({"email": body.email})
    try:
        valid = HASHER.verify(user["password_hash"] if user else DUMMY, body.password)
    except (VerificationError, InvalidHashError):
        valid = False
    if not valid or not user or not user["active"]:
        raise HTTPException(401, "Credenciales inválidas")
    return user


DUMMY = HASHER.hash(opaque())


@auth.post("/auth/login")
@policy()
def login(body: Login):
    user = check_login(body)
    if not user["verified"]:
        raise HTTPException(403, "Correo pendiente de verificación")
    token = opaque()
    expires_at = now() + timedelta(minutes=15)
    db.sessions.insert_one({"_id": digest(token), "user_id": user["_id"],
                            "version": user["version"], "expires_at": expires_at})
    return {"access_token": token, "token_type": "bearer", "expires_in": 900}


@auth.post("/auth/introspect")
@policy(private=True)
def introspect(body: TokenBody):
    session = db.sessions.find_one({"_id": digest(body.token), "expires_at": {"$gt": now()}})
    if not session:
        raise HTTPException(401, "Sesión inválida")
    user = db.users.find_one({"_id": session["user_id"], "active": True,
                             "verified": True, "version": session["version"]})
    if not user:
        raise HTTPException(401, "Sesión inválida")
    return {"id": user["_id"], "role": user["role"]}


@auth.post("/auth/logout", status_code=204)
@policy(*AUTHENTICATED)
async def logout(request: Request):
    body = TokenBody.model_validate(await request.json())
    await run_in_threadpool(db.sessions.delete_one, {"_id": digest(body.token),
                                                     "user_id": identity(request)["id"]})
    return Response(status_code=204)


@auth.post("/auth/verify")
@policy()
def verify(body: TokenBody):
    def apply(session):
        user = db.users.find_one_and_update(
            {"verify.digest": digest(body.token), "verify.expires_at": {"$gt": now()}, "active": True},
            {"$set": {"verified": True}, "$unset": {"verify": ""}}, session=session)
        if user is None:
            raise HTTPException(400, "Código inválido o vencido")
        db.outbox.delete_many({"recipient_id": user["_id"], "kind": "verify"}, session=session)
    transaction(apply)
    return {"verified": True, "adapter": "local"}


@auth.post("/auth/resend", status_code=202)
@policy()
def resend(body: Login):
    user = check_login(body)
    if not user["verified"]:
        def apply(session):
            current = db.users.find_one({"_id": user["_id"], "active": True, "verified": False},
                                        session=session)
            if current:
                issue_mail(current, "verify", session)
        transaction(apply)
    return {"accepted": True}


@auth.post("/auth/recovery", status_code=202)
@policy()
def recovery(body: EmailBody):
    def apply(session):
        user = db.users.find_one({"email": body.email, "active": True, "verified": True}, session=session)
        if user:
            issue_mail(user, "reset", session)
    transaction(apply)
    return {"accepted": True}


@auth.post("/auth/reset", status_code=204)
@policy()
def reset(body: Reset):
    new_hash = HASHER.hash(body.password)

    def apply(session):
        user = db.users.find_one_and_update(
            {"reset.digest": digest(body.token), "reset.expires_at": {"$gt": now()}, "active": True},
            {"$set": {"password_hash": new_hash}, "$inc": {"version": 1}, "$unset": {"reset": ""}},
            session=session)
        if not user:
            raise HTTPException(400, "Código inválido o vencido")
        db.outbox.delete_many({"recipient_id": user["_id"], "kind": "reset"}, session=session)
    transaction(apply)
    return Response(status_code=204)


@auth.post("/internal/clients")
@policy(private=True, callers=("clients",))
def register(body: Registration):
    profile = body.model_dump(mode="json", exclude={"email", "password"})
    user = {"_id": uid(), "nombre": body.nombre, "email": body.email, "run": body.run,
            "profile": profile, "password_hash": HASHER.hash(body.password),
            "role": "cliente", "active": True, "verified": False, "version": 0}
    def apply(session):
        db.users.insert_one(user, session=session)
        issue_mail(user, "verify", session)
    try:
        transaction(apply)
    except DuplicateKeyError:
        raise HTTPException(409, "Correo o RUN ya registrado") from None
    return {"id": user["_id"], "verification_pending": True, "adapter": "local"}


@clients.post(BASE + "/clients", status_code=201)
@policy()
def self_register(body: Registration):
    return upstream_json("auth", "POST", "/internal/clients", json=body.model_dump(mode="json"))


@clients.post(BASE + "/admin/clients", status_code=201)
@policy("admin")
def admin_register(body: Registration):
    return upstream_json("auth", "POST", "/internal/clients", json=body.model_dump(mode="json"))


@clients.get(BASE + "/clients/me")
@policy("cliente")
def me(request: Request):
    return client_view(fetch(db.users, identity(request)["id"]))


@clients.get(BASE + "/admin/clients")
@policy("admin")
def list_clients(after: str = "", limit: Annotated[int, Field(ge=1, le=100)] = 50):
    records = db.users.find({"role": "cliente", "_id": {"$gt": after}}).sort("_id").limit(limit)
    records = list(records)
    counts = upstream_json("orders", "POST", "/internal/client-order-counts",
                           json={"ids": [doc["_id"] for doc in records]}) if records else {}
    return [{**{field: client[field] for field in ("id", "nombre", "email", "active", "verified")},
             "pedidos": counts.get(client["id"], 0)} for client in map(client_view, records)]


def get_client(client_id):
    doc = db.users.find_one({"_id": client_id, "role": "cliente"})
    if not doc:
        raise HTTPException(404, "Cliente no encontrado")
    return doc


@clients.get(BASE + "/admin/clients/{client_id}")
@policy("admin")
def view_client(client_id: str):
    return client_view(get_client(client_id))


@clients.put(BASE + "/admin/clients/{client_id}")
@policy("admin")
def update_client(client_id: str, body: Profile):
    previous = get_client(client_id)
    profile = {"run": previous["run"], **body.model_dump(mode="json")}
    db.client_profiles.replace_one({"_id": client_id}, {"_id": client_id, **profile}, upsert=True)
    return client_view(get_client(client_id))


@clients.put(BASE + "/admin/clients/{client_id}/active")
@policy("admin")
def active_client(client_id: str, body: Active):
    get_client(client_id)
    upstream_json("auth", "PUT", f"/internal/clients/{client_id}/active",
                  json=body.model_dump(mode="json"))
    return client_view(get_client(client_id))


@auth.put("/internal/clients/{client_id}/active")
@policy(private=True, callers=("clients",))
def set_client_active(client_id: str, body: Active):
    get_client(client_id)
    db.users.update_one({"_id": client_id, "active": {"$ne": body.active}},
                        {"$set": {"active": body.active}, "$inc": {"version": 1}})
    return {"updated": True}


@auth.post(BASE + "/admin/users", status_code=201)
@policy("admin")
def create_staff(body: StaffRegistration):
    user = {"_id": uid(), "nombre": body.nombre, "email": body.email,
            "password_hash": HASHER.hash(body.password), "role": body.role,
            "active": True, "verified": True, "version": 0}
    try:
        db.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(409, "Correo ya registrado") from None
    return account_view(user)


@auth.get(BASE + "/admin/users")
@policy("admin")
def list_staff(after: str = "", limit: Annotated[int, Field(ge=1, le=100)] = 50):
    return [account_view(doc) for doc in db.users.find(
        {"role": {"$ne": "cliente"}, "_id": {"$gt": after}}).sort("_id").limit(limit)]


@auth.put(BASE + "/admin/users/{user_id}")
@policy("admin")
def update_staff(user_id: str, body: StaffUpdate, request: Request):
    if user_id == identity(request)["id"] and (body.role != "admin" or not body.active):
        raise HTTPException(409, "El administrador actual debe permanecer activo")
    updated = db.users.find_one_and_update(
        {"_id": user_id, "role": {"$ne": "cliente"}},
        {"$set": body.model_dump(), "$inc": {"version": 1}}, return_document=True)
    if not updated:
        raise HTTPException(404, "Usuario no encontrado")
    return account_view(updated)


@clients.get(BASE + "/admin/mail/{recipient_id}")
@policy("admin")
def local_mail(recipient_id: str):
    criteria = {
        "recipient_id": recipient_id,
        "$or": [{"expires_at": {"$gt": now()}}, {"expires_at": {"$exists": False}}]
    }
    notices = [doc for collection in (db.outbox, db.payment_outbox)
               for doc in collection.find(criteria).sort("created_at", -1).limit(50)]
    return [public_id(doc) for doc in sorted(notices, key=lambda doc: doc["created_at"],
                                           reverse=True)[:50]]


@clients.get("/internal/clients/{client_id}/checkout")
@policy(private=True, callers=("orders",))
def checkout_client(client_id: str):
    client = client_view(get_client(client_id))
    if not client["active"] or not client["verified"]:
        raise HTTPException(403, "Cliente debe estar activo y verificado")
    return {"nombre": client["nombre"], "telefono": client["telefono"]}


@clients.get("/internal/clients/{client_id}/receipt-contact")
@policy(private=True, callers=("payments",))
def receipt_contact(client_id: str):
    return {"email": get_client(client_id)["email"]}

