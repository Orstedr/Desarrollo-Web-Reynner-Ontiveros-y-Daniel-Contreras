from collections import Counter
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import Field, StrictBool, StringConstraints, model_validator
from pymongo.errors import DuplicateKeyError

from accounts import Model
from common import BASE, PrivateRoute, db, fetch, policy, public_id, transaction

inventory = APIRouter(route_class=PrivateRoute)
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{0,47}$")]
Money = Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
Quantity = Annotated[int, Field(strict=True, ge=1, le=30)]
Category = Literal["clasicos", "proteicos", "veggie", "especiales"]
Group = Literal["base", "proteina", "topping", "salsa"]
GROUPS = ("base", "proteina", "topping", "salsa")


class Product(Model):
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    categoria: Category
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=250)]
    precio: Money
    precioNormal: Money | None = None
    titulo: Annotated[str, StringConstraints(max_length=60)] | None = None
    imagenEmoji: Annotated[str, StringConstraints(max_length=16)] = ""
    habilitado: StrictBool = True

    @model_validator(mode="after")
    def promotion(self):
        if self.categoria == "especiales":
            if self.precioNormal is None or self.precioNormal <= self.precio:
                raise ValueError("La oferta exige un precio normal superior")
        elif self.precioNormal is not None or self.titulo is not None:
            raise ValueError("Los datos de oferta requieren categoría especiales")
        return self


class NewProduct(Product):
    id: Identifier
    stock: Annotated[int, Field(strict=True, ge=0, le=1_000_000)]


class Availability(Model):
    habilitado: StrictBool


class Stock(Model):
    delta: Annotated[int, Field(strict=True, ge=-100_000, le=100_000)]


class CatalogLine(Model):
    tipo: Literal["producto"]
    id: Identifier
    cantidad: Quantity


class BowlLine(Model):
    tipo: Literal["bowl"]
    base: Identifier
    proteina: Identifier
    toppings: list[Identifier] = Field(default_factory=list, max_length=6)
    salsa: Identifier
    cantidad: Quantity

    @model_validator(mode="after")
    def combinations(self):
        if len(set(self.toppings)) != len(self.toppings):
            raise ValueError("Toppings repetidos")
        if "ninguno" in self.toppings and self.toppings != ["ninguno"]:
            raise ValueError("Ninguno excluye los demás toppings")
        return self


Lines = Annotated[list[Annotated[CatalogLine | BowlLine, Field(discriminator="tipo")]],
                  Field(min_length=1, max_length=30)]


def available(doc):
    return doc["habilitado"] and (doc["stock"] is None or doc["stock"] > 0)


def item_view(doc, internal=False):
    omit = ("kind",) if internal else ("kind", "stock", "habilitado")
    return {**public_id(doc, omit), "disponible": available(doc)}


@inventory.get(BASE + "/catalog")
@policy()
def catalog(categoria: Category | None = None, available_only: bool = True):
    filters = {"kind": "product"}
    if categoria:
        filters["categoria"] = categoria
    if available_only:
        filters.update(habilitado=True, stock={"$gt": 0})
    return {"moneda": "CLP", "products": [item_view(doc) for doc in db.inventory.find(
        filters).sort("_id").limit(200)]}


@inventory.get(BASE + "/bowl-options")
@policy()
def bowl_options():
    config = fetch(db.config, "bowl")
    options = {group: [] for group in GROUPS}
    for doc in db.inventory.find({"kind": "ingredient"}).sort("orden"):
        options[doc["grupo"]].append(item_view(doc))
    return {"precioBase": config["precioBase"], "moneda": config["moneda"], "options": options}


@inventory.get(BASE + "/admin/inventory")
@policy("admin", "dueno")
def admin_inventory(after: str = "", limit: int = Query(100, ge=1, le=200)):
    return [item_view(doc, internal=True) for doc in db.inventory.find(
        {"_id": {"$gt": after}}).sort("_id").limit(limit)]


@inventory.post(BASE + "/admin/products", status_code=201)
@policy("admin", "dueno")
def create_product(body: NewProduct):
    doc = {"_id": body.id, "kind": "product", **body.model_dump(exclude={"id"}, exclude_none=True)}
    try:
        db.inventory.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "ID de inventario en uso") from None
    return item_view(doc, internal=True)


@inventory.put(BASE + "/admin/products/{item_id}")
@policy("admin", "dueno")
def update_product(item_id: Identifier, body: Product):
    doc = db.inventory.find_one_and_update({"_id": item_id, "kind": "product"},
        {"$set": body.model_dump()}, return_document=True)
    if not doc:
        raise HTTPException(404, "Producto no encontrado")
    return item_view(doc, internal=True)


@inventory.put(BASE + "/admin/inventory/{item_id}/availability")
@policy("admin", "dueno")
def set_availability(item_id: Identifier, body: Availability):
    doc = db.inventory.find_one_and_update({"_id": item_id},
        {"$set": body.model_dump()}, return_document=True)
    if not doc:
        raise HTTPException(404, "Ítem de inventario no encontrado")
    return item_view(doc, internal=True)


@inventory.post(BASE + "/admin/inventory/{item_id}/adjustments")
@policy("admin", "dueno")
def adjust_stock(item_id: Identifier, body: Stock):
    fetch(db.inventory, item_id)
    doc = db.inventory.find_one_and_update(
        {"_id": item_id, "stock": {"$gte": max(0, -body.delta), "$lte": 1_000_000 - body.delta}},
        {"$inc": {"stock": body.delta}}, return_document=True)
    if not doc:
        raise HTTPException(409, "Stock insuficiente o ajuste fuera de rango")
    return item_view(doc, internal=True)


def price_lines(lines, session):
    units = Counter()
    details = []
    bowl_price = None
    for line in lines:
        if isinstance(line, CatalogLine):
            doc = db.inventory.find_one({"_id": line.id, "kind": "product"}, session=session)
            if not doc:
                raise HTTPException(422, "ID de producto inválido")
            if not available(doc):
                raise HTTPException(409, f"Producto no disponible: {line.id}")
            unit_price = doc["precio"]
            name = doc["nombre"]
            units[line.id] += line.cantidad
            selection = {"product_id": line.id}
        else:
            if bowl_price is None:
                bowl_price = fetch(db.config, "bowl", session)["precioBase"]
            unit_price = bowl_price
            name = "Bowl personalizado"
            choices = [("base", line.base), ("proteina", line.proteina),
                       ("salsa", line.salsa), *(("topping", option) for option in line.toppings)]
            ingredients = []
            for group, option in choices:
                doc = db.inventory.find_one({"_id": option, "kind": "ingredient", "grupo": group},
                                            session=session)
                if not doc:
                    raise HTTPException(422, f"Ingrediente inválido para {group}: {option}")
                if not available(doc):
                    raise HTTPException(409, f"Ingrediente no disponible: {option}")
                unit_price += doc["precio"]
                if doc["stock"] is not None:
                    units[option] += line.cantidad
                ingredients.append({"id": option, "grupo": group, "nombre": doc["nombre"],
                                    "precio": doc["precio"]})
            selection = {"ingredientes": ingredients}
        details.append({"tipo": line.tipo, "nombre": name, "cantidad": line.cantidad,
                        "unit_price": unit_price, "subtotal": unit_price * line.cantidad, **selection})
    return details, dict(units)


def reserve(units, session, mutate):
    for item_id, quantity in sorted(units.items()):
        condition = {"_id": item_id, "habilitado": True, "stock": {"$gte": quantity}}
        if mutate:
            exists = db.inventory.update_one(condition, {"$inc": {"stock": -quantity}},
                                             session=session).matched_count
        else:
            exists = db.inventory.find_one(condition, {"_id": 1}, session=session)
        if not exists:
            raise HTTPException(409, f"Stock insuficiente: {item_id}")


def restore(units, session):
    for item_id, quantity in sorted(units.items()):
        db.inventory.update_one({"_id": item_id}, {"$inc": {"stock": quantity}}, session=session)


class Reservation(Model):
    items: Lines


class Release(Model):
    at: datetime
    legacy_units: dict[Identifier, int] | None = None


def priced_quote(body, session):
    details, units = price_lines(body.items, session)
    reserve(units, session, False)
    return {"items": details, "total": sum(line["subtotal"] for line in details)}


@inventory.post("/internal/quote")
@policy(private=True, callers=("orders",))
def internal_quote(body: Reservation):
    return transaction(lambda session: priced_quote(body, session))


@inventory.post("/internal/reservations/{order_id}")
@policy(private=True, callers=("orders",))
def reserve_order(order_id: str, body: Reservation):
    def apply(session):
        existing = db.reservations.find_one({"_id": order_id}, session=session)
        if existing:
            return existing["quote"]
        details, units = price_lines(body.items, session)
        reserve(units, session, True)
        quote = {"items": details, "total": sum(line["subtotal"] for line in details)}
        db.reservations.insert_one({"_id": order_id, "units": units, "quote": quote},
                                   session=session)
        return quote

    try:
        return transaction(apply)
    except DuplicateKeyError:
        return transaction(apply)


@inventory.post("/internal/reservations/{order_id}/release")
@policy(private=True, callers=("orders",))
def release_order(order_id: str, body: Release):
    def apply(session):
        record = db.reservations.find_one({"_id": order_id}, session=session)
        if record:
            if "released_at" not in record:
                restore(record["units"], session)
                db.reservations.update_one({"_id": order_id}, {"$set": {"released_at": body.at}},
                                           session=session)
        elif body.legacy_units is not None:
            restore(body.legacy_units, session)
            db.reservations.insert_one({"_id": order_id, "units": body.legacy_units,
                                        "released_at": body.at}, session=session)
        else:
            raise HTTPException(409, "No existe la reserva del pedido")
        return {"released": True}

    try:
        return transaction(apply)
    except DuplicateKeyError:
        return transaction(apply)
