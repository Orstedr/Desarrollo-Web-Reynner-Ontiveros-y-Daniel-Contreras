import json
import math
import os
import re
from datetime import date, datetime, time, timedelta, timezone
from io import BytesIO
from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from pydantic import Field, StringConstraints
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen.canvas import Canvas
from pymongo.errors import DuplicateKeyError

from accounts import Model
from common import (BASE, PrivateRoute, db, digest, fetch, graphql_read, identity, now,
                    policy, public_id, role, transaction, uid, upstream_json)
from inventory import Lines

orders = APIRouter(route_class=PrivateRoute)
payments = APIRouter(route_class=PrivateRoute)
ORDER_ROLES = ("cliente", "admin", "cajero", "despacho", "dueno")
ORIGIN = (float(os.getenv("ORIGIN_LAT", "-33.6110")), float(os.getenv("ORIGIN_LON", "-70.5750")))
DESTINATIONS = {
    "cobertura-1": {"direccion": "Pasaje Demo 100", "comuna": "Puente Alto",
                    "lat": -33.6210, "lon": -70.5750},
    "fuera-1": {"direccion": "Pasaje Demo 900", "comuna": "Puente Alto",
                "lat": -33.6710, "lon": -70.5750},
}
PENDING = "pendiente_pago"
PAID = "pagado"
CANCELLED = "anulado"
RESERVING = "reserva_en_curso"
TRANSITIONS = {"preparando": PAID, "en_camino": "preparando", "entregado": "en_camino"}


class Checkout(Model):
    items: Lines
    destino_id: Literal["cobertura-1", "fuera-1"]


class Cancel(Model):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=300)]


class Move(Model):
    estado: Literal["preparando", "en_camino", "entregado"]


class StartPayment(Model):
    metodo: Literal["webpay", "transferencia"]
    escenario_local: Literal["aprobado", "rechazado"] = "aprobado"


class ConfirmPayment(Model):
    referencia: Annotated[str, StringConstraints(pattern=r"^local-[a-f0-9]{32}$")]


def delivery(key):
    destination = DESTINATIONS[key]
    lat, lon, end_lat, end_lon = map(math.radians, (*ORIGIN, destination["lat"], destination["lon"]))
    angle = math.sin((end_lat - lat) / 2) ** 2 + (
        math.cos(lat) * math.cos(end_lat) * math.sin((end_lon - lon) / 2) ** 2)
    distance = 6371.0088 * 2 * math.asin(math.sqrt(min(1, max(0, angle))))
    return {"destino_id": key, **destination, "distance_km": round(distance, 4),
            "in_coverage": distance <= 3, "shipping": 0 if distance <= 3 else None}


@orders.get(BASE + "/delivery/zones")
@policy()
def zones():
    return {"origin": {"lat": ORIGIN[0], "lon": ORIGIN[1]}, "radius_km": 3,
            "adapter": "local", "destinos": [delivery(key) for key in DESTINATIONS]}


def delivery_for_checkout(body):
    destination = delivery(body.destino_id)
    if not destination["in_coverage"]:
        raise HTTPException(422, "Dirección fuera del radio de 3 km")
    return destination


@orders.post(BASE + "/orders/quote")
@policy()
def quote(body: Checkout, request: Request):
    destination = delivery_for_checkout(body)
    priced = upstream_json("inventory", "POST", "/internal/quote",
                           json={"items": body.model_dump(mode="json")["items"]},
                           correlation=request.state.correlation)
    return {**priced, "currency": "CLP", "shipping": 0, "delivery": destination}

def order_access(order, request):
    if order["state"] == RESERVING:
        raise HTTPException(404, "Pedido no encontrado")
    if role(request) == "cliente" and order["client_id"] != identity(request)["id"]:
        raise HTTPException(404, "Pedido no encontrado")
    if role(request) == "despacho" and order["state"] not in (PAID, *TRANSITIONS):
        raise HTTPException(404, "Pedido no disponible para despacho")
    return order


def order_view(order, request):
    omit = ["stock_units", "client_id", "client_name", "client_phone", "checkout_key",
            "checkout_hash", "payment_revision", "confirming", "cancelling"]
    if role(request) in ("dueno", "cajero"):
        omit.extend(["delivery", "cancellation"])
    return public_id(order, omit)


@orders.post(BASE + "/orders", status_code=201)
@policy("cliente")
def create_order(body: Checkout, request: Request,
                 idempotency_key: Annotated[str, Header(pattern=r"^[A-Za-z0-9_-]{8,64}$")]):
    client_id = identity(request)["id"]
    correlation = request.state.correlation
    filters = {"client_id": client_id, "checkout_key": idempotency_key}
    payload = body.model_dump(mode="json")
    request_hash = digest(json.dumps(payload, sort_keys=True))
    client = upstream_json("clients", "GET", f"/internal/clients/{client_id}/checkout",
                           correlation=correlation)
    order = db.orders.find_one(filters)
    if order is None:
        destination = delivery_for_checkout(body)
        draft = {"_id": uid(), **filters, "checkout_hash": request_hash, "state": RESERVING,
                 "client_name": client["nombre"], "client_phone": client["telefono"],
                 "created_at": now(), "currency": "CLP", "shipping": 0, "delivery": destination}
        try:
            db.orders.insert_one(draft)
            order = draft
        except DuplicateKeyError:
            order = db.orders.find_one(filters)
            if order is None:
                raise
    if order["checkout_hash"] != request_hash:
        raise HTTPException(409, "Clave de idempotencia usada con otro pedido")
    if order["state"] != RESERVING:
        return order_view(order, request)

    order_id = order["_id"]
    priced = upstream_json("inventory", "POST", f"/internal/reservations/{order_id}",
                           correlation=correlation, json={"items": payload["items"]})
    db.orders.update_one({"_id": order_id, "state": RESERVING},
                         {"$set": {**priced, "state": PENDING}})
    return order_view(fetch(db.orders, order_id), request)

@orders.get(BASE + "/orders")
@policy("cliente", "admin")
def list_orders(request: Request, limit: int = Query(30, ge=1, le=100), after: str = ""):
    filters = {"_id": {"$gt": after}, "state": {"$ne": RESERVING}}
    if role(request) == "cliente":
        filters["client_id"] = identity(request)["id"]
    return [order_view(doc, request) for doc in db.orders.find(filters).sort("_id").limit(limit)]


@orders.get(BASE + "/orders/{order_id}")
@policy(*ORDER_ROLES)
@graphql_read
def get_order(order_id: str, request: Request):
    return order_view(order_access(fetch(db.orders, order_id), request), request)


@orders.post(BASE + "/orders/{order_id}/cancel")
@policy("cliente", "admin")
def cancel(order_id: str, body: Cancel, request: Request):
    def begin(session):
        order = order_access(fetch(db.orders, order_id, session), request)
        if order["state"] == CANCELLED or order.get("cancelling"):
            return order
        if order["state"] not in (PENDING, PAID) or order.get("confirming"):
            raise HTTPException(409, "Sólo se anula antes de preparar y fuera de una confirmación en curso")
        order["cancelling"] = {"motivo": body.motivo, "at": now(), "role": role(request)}
        db.orders.update_one({"_id": order_id}, {"$set": {"cancelling": order["cancelling"]}},
                             session=session)
        return order

    order = transaction(begin)
    if order["state"] == CANCELLED:
        return order_view(order, request)

    cancellation = order["cancelling"]
    correlation = request.state.correlation
    body = {"at": cancellation["at"].isoformat()}
    upstream_json("payments", "POST", f"/internal/payments/{order_id}/void",
                  correlation=correlation, json=body)
    upstream_json("inventory", "POST", f"/internal/reservations/{order_id}/release",
                  correlation=correlation, json={**body, "legacy_units": order.get("stock_units")})
    db.orders.update_one({"_id": order_id, "cancelling": {"$exists": True}},
                         {"$set": {"state": CANCELLED, "cancellation": cancellation},
                          "$unset": {"cancelling": ""}})
    return order_view(fetch(db.orders, order_id), request)

@orders.get(BASE + "/dispatch")
@policy("despacho", "admin")
def list_dispatch(request: Request, limit: int = Query(50, ge=1, le=100)):
    ready = db.orders.find({"state": {"$in": [PAID, "preparando", "en_camino"]},
                            "cancelling": {"$exists": False}}).sort(
        [("paid_at", 1), ("_id", 1)]).limit(limit)
    return [dict(order_view(doc, request), cliente=doc["client_name"]) for doc in ready]


@orders.put(BASE + "/dispatch/{order_id}/state")
@policy("despacho", "admin")
def update_dispatch(order_id: str, body: Move, request: Request):
    def apply(session):
        order = fetch(db.orders, order_id, session)
        if order["state"] == body.estado:
            return order_view(order, request)
        if (order["state"] != TRANSITIONS[body.estado] or not order.get("paid_at")
                or order.get("cancelling")):
            raise HTTPException(409, "Transición inválida o pago sin confirmar")
        order.update(state=body.estado, updated_at=now())
        db.orders.replace_one({"_id": order_id}, order, session=session)
        return order_view(order, request)
    return transaction(apply)


def pdf_document(title, lines, name):
    buffer = BytesIO()
    page = Canvas(buffer, pagesize=A4)
    page.setTitle(title)
    height = A4[1] - 52
    page.setFont("Helvetica-Bold", 15)
    page.drawString(45, height, title)
    height -= 30
    page.setFont("Helvetica", 10)
    for line in lines:
        for part in simpleSplit(line, "Helvetica", 10, A4[0] - 90):
            if height < 48:
                page.showPage()
                page.setFont("Helvetica", 10)
                height = A4[1] - 52
            page.drawString(45, height, part)
            height -= 15
    page.save()
    return Response(buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}.pdf"'})


@orders.get(BASE + "/dispatch/{order_id}/print", response_class=Response,
            responses={200: {"content": {"application/pdf": {}}}})
@policy("despacho", "admin")
def print_dispatch(order_id: str):
    order = fetch(db.orders, order_id)
    if order["state"] not in (PAID, "preparando", "en_camino", "entregado") or order.get("cancelling"):
        raise HTTPException(409, "Orden de despacho no disponible")
    address = order["delivery"]
    lines = [f"Pedido {order_id}", f"Estado: {order['state']}", f"Pago: {order['paid_at'].isoformat()}",
             f"Cliente: {order['client_name']}", f"Contacto: {order['client_phone']}",
             f"Entrega: {address['direccion']}, {address['comuna']}", "Detalle:"]
    for item in order["items"]:
        names = ", ".join(entry["nombre"] for entry in item.get("ingredientes", []))
        lines.append(f"{item['cantidad']} x {item['nombre']}" + (f" ({names})" if names else ""))
    return pdf_document("Poké Fresh - Orden de despacho", lines, f"despacho-{order_id}")


class ClientOrderCounts(Model):
    ids: list[Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{32}$")]] = Field(max_length=100)


class PaidOrder(ConfirmPayment):
    at: datetime


class VoidPayment(Model):
    at: datetime


def valid_order_id(order_id):
    if not re.fullmatch(r"[a-f0-9]{32}", order_id):
        raise HTTPException(404, "Pedido no encontrado")


@orders.post("/internal/client-order-counts")
@policy(private=True, callers=("clients",))
def client_order_counts(body: ClientOrderCounts):
    rows = db.orders.aggregate([
        {"$match": {"client_id": {"$in": body.ids}, "state": {"$ne": RESERVING}}},
        {"$group": {"_id": "$client_id", "count": {"$sum": 1}}},
    ])
    return {row["_id"]: row["count"] for row in rows}


@orders.get("/internal/orders/{order_id}/payment")
@policy("cliente", "admin", "cajero", "dueno", private=True, callers=("payments",))
def payment_order_snapshot(order_id: str, request: Request):
    order = order_access(fetch(db.orders, order_id), request)
    return {"state": order["state"], "total": order["total"], "items": order["items"],
            "client_id": order["client_id"], "cancelling": bool(order.get("cancelling"))}


@orders.put("/internal/orders/{order_id}/confirmation")
@policy(private=True, callers=("payments",))
def claim_confirmation(order_id: str, body: ConfirmPayment):
    def apply(session):
        order = fetch(db.orders, order_id, session)
        if order.get("confirming") == body.referencia:
            return {"claimed": True}
        if order.get("paid_at"):
            return {"claimed": False}
        if order["state"] != PENDING or order.get("cancelling") or order.get("confirming"):
            raise HTTPException(409, "El pedido no admite confirmación")
        db.orders.update_one({"_id": order_id}, {"$set": {"confirming": body.referencia}},
                             session=session)
        return {"claimed": True}
    return transaction(apply)


@orders.put("/internal/orders/{order_id}/paid")
@policy(private=True, callers=("payments",))
def finish_confirmation(order_id: str, body: PaidOrder):
    result = db.orders.update_one(
        {"_id": order_id, "state": PENDING, "confirming": body.referencia},
        {"$set": {"state": PAID, "paid_at": body.at}, "$unset": {"confirming": ""}},
    )
    if not result.matched_count and not fetch(db.orders, order_id).get("paid_at"):
        raise HTTPException(409, "El pedido carece de confirmación pendiente")
    return {"updated": True}


def order_for_payment(order_id, request):
    valid_order_id(order_id)
    return upstream_json("orders", "GET", f"/internal/orders/{order_id}/payment",
                         identity=identity(request), correlation=request.state.correlation)


@payments.post("/internal/payments/{order_id}/void")
@policy(private=True, callers=("orders",))
def void_payment(order_id: str, body: VoidPayment):
    def apply(session):
        payment = db.payments.find_one({"_id": order_id}, session=session)
        if payment is None:
            db.payments.insert_one({"_id": order_id, "status": "voided",
                                    "closed_at": body.at, "no_attempt": True}, session=session)
        elif payment["status"] not in ("voided", "refunded"):
            refunded = payment["status"] == "confirmed"
            db.payments.update_one({"_id": order_id}, {"$set": {
                "status": "refunded" if refunded else "voided", "closed_at": body.at,
            }}, session=session)
            if refunded:
                db.sales.update_one({"_id": order_id}, {"$set": {"voided_at": body.at}}, session=session)
                db.receipts.update_one({"_id": order_id}, {"$set": {"voided_at": body.at}}, session=session)
        return {"voided": True}

    try:
        return transaction(apply)
    except DuplicateKeyError:
        return transaction(apply)


def payment_view(doc, request):
    omit = ["provider_decision", "cashier_id"]
    if role(request) != "cajero":
        omit.append("referencia")
    return public_id(doc, omit)


@payments.post(BASE + "/orders/{order_id}/payment")
@policy("cliente")
def start_payment(order_id: str, body: StartPayment, request: Request):
    order = order_for_payment(order_id, request)
    if order["state"] != PENDING or order["cancelling"]:
        raise HTTPException(409, "El pedido no admite iniciar un pago")

    def apply(session):
        previous = db.payments.find_one({"_id": order_id}, session=session)
        if previous and previous["status"] in ("confirmed", "voided", "refunded"):
            raise HTTPException(409, "El pedido no admite iniciar un pago")
        if previous and previous["status"] == "authorized":
            if previous["metodo"] != body.metodo or body.escenario_local != "aprobado":
                raise HTTPException(409, "Ya existe una autorización para el pedido")
            return payment_view(previous, request)
        approved = body.escenario_local == "aprobado"
        payment = {"_id": order_id, "adapter": "local", "metodo": body.metodo,
                   "referencia": "local-" + uid(), "provider_decision": body.escenario_local,
                   "status": "authorized" if approved else "declined", "amount": order["total"],
                   "currency": "CLP", "attempt": (previous["attempt"] if previous else 0) + 1,
                   "created_at": now()}
        db.payments.replace_one({"_id": order_id}, payment, upsert=True, session=session)
        return payment_view(payment, request)

    try:
        return transaction(apply)
    except DuplicateKeyError:
        return transaction(apply)


@payments.get(BASE + "/orders/{order_id}/payment")
@policy("cliente", "admin", "cajero", "dueno")
@graphql_read
def get_payment(order_id: str, request: Request):
    order_for_payment(order_id, request)
    doc = db.payments.find_one({"_id": order_id})
    return payment_view(doc, request) if doc and not doc.get("no_attempt") else {
        "id": order_id, "status": "not_started"
    }


@payments.post(BASE + "/orders/{order_id}/payment/confirm")
@policy("cajero")
def confirm_payment(order_id: str, body: ConfirmPayment, request: Request):
    order = order_for_payment(order_id, request)
    payment = fetch(db.payments, order_id)
    if payment.get("no_attempt"):
        raise HTTPException(404, "Recurso no encontrado")
    if body.referencia != payment["referencia"]:
        raise HTTPException(409, "Referencia del adaptador inválida")
    if payment["status"] not in ("authorized", "confirmed", "refunded") or (
        payment["provider_decision"] != "aprobado" or payment["amount"] != order["total"]
        or payment["currency"] != "CLP"
    ):
        raise HTTPException(409, "El adaptador no confirma el pago de este pedido")

    correlation = request.state.correlation
    confirmation_path = f"/internal/orders/{order_id}"
    reference = body.model_dump(mode="json")
    contact = None
    if payment["status"] == "authorized":
        contact = upstream_json("clients", "GET", f"/internal/clients/{order['client_id']}/receipt-contact",
                                correlation=correlation)
    claimed = upstream_json("orders", "PUT", f"{confirmation_path}/confirmation",
                            correlation=correlation, json=reference)["claimed"]

    def apply(session):
        current = fetch(db.payments, order_id, session)
        if current["status"] in ("confirmed", "refunded"):
            sale = fetch(db.sales, order_id, session)
            return {"payment_status": current["status"], "sale_id": sale["_id"],
                    "receipt_id": sale["receipt_id"], "duplicate": True}, current["confirmed_at"]
        if not claimed or current["status"] != "authorized" or contact is None:
            raise HTTPException(409, "El adaptador no confirma el pago de este pedido")
        stamp = now()
        cashier_id = identity(request)["id"]
        receipt_id = "PF-" + order_id
        db.payments.update_one({"_id": order_id}, {"$set": {
            "status": "confirmed", "confirmed_at": stamp, "cashier_id": cashier_id
        }}, session=session)
        db.sales.insert_one({"_id": order_id, "receipt_id": receipt_id, "cashier_id": cashier_id,
                             "box": "CAJA-WEB", "total": current["amount"], "sold_at": stamp}, session=session)
        db.receipts.insert_one({"_id": order_id, "number": receipt_id, "order_id": order_id,
                               "items": order["items"], "total": current["amount"], "currency": "CLP",
                               "issued_at": stamp, "box": "CAJA-WEB", "document_type": "boleta_demo"},
                              session=session)
        db.payment_outbox.insert_one({"_id": uid(), "recipient_id": order["client_id"], "kind": "receipt",
                                      "email": contact["email"], "receipt_id": receipt_id, "order_id": order_id,
                                      "adapter": "local", "created_at": stamp}, session=session)
        return {"payment_status": "confirmed", "sale_id": order_id,
                "receipt_id": receipt_id, "duplicate": False}, stamp

    result, stamp = transaction(apply)
    if claimed:
        upstream_json("orders", "PUT", f"{confirmation_path}/paid",
                      correlation=correlation, json={**reference, "at": stamp.isoformat()})
    return result

@payments.get(BASE + "/orders/{order_id}/receipt")
@policy("cliente", "admin", "cajero")
def receipt(order_id: str, request: Request):
    order_for_payment(order_id, request)
    return public_id(fetch(db.receipts, order_id))


def sales_report(start, end):
    if start >= end or end - start > timedelta(days=366):
        raise HTTPException(422, "Período inválido; use hasta 366 días")
    dates = {"$gte": datetime.combine(start, time.min, timezone.utc),
             "$lt": datetime.combine(end, time.min, timezone.utc)}
    grouping = {"_id": None, "ventas_brutas": {"$sum": "$total"},
                "anuladas_clp": {"$sum": {"$cond": [
                    {"$ne": [{"$ifNull": ["$voided_at", None]}, None]}, "$total", 0]}},
                "cantidad_bruta": {"$sum": 1},
                "cantidad_anulada": {"$sum": {"$cond": [
                    {"$ne": [{"$ifNull": ["$voided_at", None]}, None]}, 1, 0]}}}
    rows = list(db.sales.aggregate([{"$match": {"sold_at": dates}}, {"$group": grouping}]))
    stats = public_id(rows[0]) if rows else {}
    gross, voided, count, void_count = (
        stats.get(key, 0) for key in ("ventas_brutas", "anuladas_clp", "cantidad_bruta", "cantidad_anulada")
    )
    net_count = count - void_count
    return {"from": start.isoformat(), "to_exclusive": end.isoformat(), "currency": "CLP",
            "gross": gross, "voided": voided, "net": gross - voided, "orders": net_count,
            "voided_orders": void_count, "average_ticket": (gross - voided) // net_count if net_count else 0}


@payments.get(BASE + "/reports/sales")
@policy("admin", "dueno")
def report(desde: date, hasta: date):
    return sales_report(desde, hasta)


@payments.get(BASE + "/reports/sales/print", response_class=Response,
              responses={200: {"content": {"application/pdf": {}}}})
@policy("admin", "dueno")
def report_pdf(desde: date, hasta: date):
    result = sales_report(desde, hasta)
    lines = [f"Período UTC: {desde} hasta {hasta} (exclusivo)",
             f"Ventas brutas: CLP {result['gross']}", f"Anulaciones: CLP {result['voided']}",
             f"Ventas netas: CLP {result['net']}", f"Pedidos netos: {result['orders']}",
             f"Ticket promedio: CLP {result['average_ticket']}"]
    return pdf_document("Poké Fresh - Reporte de ventas", lines, "ventas")
