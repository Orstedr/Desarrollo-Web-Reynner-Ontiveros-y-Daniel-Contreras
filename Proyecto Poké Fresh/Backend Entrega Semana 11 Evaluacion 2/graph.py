from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from graphql import GraphQLError, build_schema, execute_sync, parse, validate
from graphql.language.ast import FieldNode, OperationDefinitionNode, OperationType
from pydantic import Field, StringConstraints

from accounts import Model
from commerce import ORDER_ROLES
from common import BASE, PrivateRoute, identity, policy, upstream_json

graphql = APIRouter(route_class=PrivateRoute)
SDL = """
type Query { pedido(id: ID!): Pedido }
type Pedido { id: ID!, estado: String!, total: Int!, moneda: String!, pago: Pago }
type Pago { estado: String!, monto: Int, metodo: String, referencia: String }
"""
schema = build_schema(SDL)


class GraphBody(Model):
    query: Annotated[str, StringConstraints(min_length=1, max_length=2500)]
    variables: dict[str, Annotated[str, StringConstraints(max_length=64)]] = Field(
        default_factory=dict, max_length=5)


def call(request, target, path):
    try:
        return upstream_json(target, "GET", path, identity=identity(request),
                             correlation=request.state.correlation)
    except HTTPException as exc:
        message = {403: "Campo no autorizado", 404: "Pedido no encontrado"}.get(
            exc.status_code, "Dependencia privada no disponible")
        raise GraphQLError(message) from None


def resolve_order(_parent, info, id):
    if len(id) != 32 or any(character not in "0123456789abcdef" for character in id):
        raise GraphQLError("ID de pedido inválido")
    request = info.context
    order = call(request, "orders", f"{BASE}/orders/{id}")
    return {"id": order["id"], "estado": order["state"],
            "total": order["total"], "moneda": order["currency"]}


def resolve_payment(parent, info):
    request = info.context
    if identity(request)["role"] == "despacho":
        raise GraphQLError("Campo pago no autorizado")
    payment = call(request, "payments", f"{BASE}/orders/{parent['id']}/payment")
    return {"estado": payment["status"], "monto": payment.get("amount"),
            "metodo": payment.get("metodo"), "referencia": payment.get("referencia")}


def resolve_reference(parent, info):
    if identity(info.context)["role"] != "cajero":
        raise GraphQLError("Campo referencia no autorizado")
    return parent["referencia"]


schema.query_type.fields["pedido"].resolve = resolve_order
schema.get_type("Pedido").fields["pago"].resolve = resolve_payment
schema.get_type("Pago").fields["referencia"].resolve = resolve_reference


def permitted_document(document):
    if len(document.definitions) != 1:
        return False
    operation = document.definitions[0]
    if (not isinstance(operation, OperationDefinitionNode) or operation.operation != OperationType.QUERY
            or operation.directives or len(operation.selection_set.selections) != 1):
        return False
    count = 0

    def within(selection, depth):
        nonlocal count
        if depth > 4:
            return False
        for field in selection.selections:
            count += 1
            if (count > 24 or not isinstance(field, FieldNode) or field.alias or field.directives
                    or field.name.value.startswith("__")):
                return False
            if field.selection_set and not within(field.selection_set, depth + 1):
                return False
        return True

    return within(operation.selection_set, 1)


@graphql.post(BASE + "/graphql")
@policy(*ORDER_ROLES)
def execute(body: GraphBody, request: Request):
    try:
        document = parse(body.query, max_tokens=160)
    except (GraphQLError, RecursionError):
        raise HTTPException(400, "Consulta GraphQL inválida o superior al límite") from None
    if not permitted_document(document):
        raise HTTPException(400, "Consulta excede las operaciones o límites permitidos")
    errors = validate(schema, document, max_errors=5)
    if errors:
        raise HTTPException(400, "La consulta no coincide con el esquema permitido")
    result = execute_sync(schema, document, context_value=request, variable_values=body.variables)
    output = {"data": result.data}
    if result.errors:
        output["errors"] = [error.formatted if isinstance(error.original_error, GraphQLError)
                            or error.original_error is None else {"message": "Error de ejecución"}
                            for error in result.errors]
    return output
