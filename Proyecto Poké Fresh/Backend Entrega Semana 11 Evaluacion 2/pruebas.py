"""Pruebas de integracion del backend local de Poke Fresh."""

import argparse
import json
import sys
from getpass import getpass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

GATEWAY = "http://127.0.0.1:8000"
API = "/api/v1"
PRODUCTO = "prod-001"
COMPRA = {
    "items": [{"tipo": "producto", "id": PRODUCTO, "cantidad": 1}],
    "destino_id": "cobertura-1",
}
SERVICIOS = {"auth", "inventory", "orders", "clients", "payments", "graphql"}


def comprobar(condicion, mensaje):
    if not condicion:
        raise RuntimeError(mensaje)
    print(f"OK: {mensaje}")


def solicitar(ruta, cuerpo=None, *, token=None, clave=None, esperado=200):
    metodo = "GET" if cuerpo is None else "POST"
    encabezados = {}
    if token:
        encabezados["Authorization"] = f"Bearer {token}"
    if clave:
        encabezados["Idempotency-Key"] = clave
    datos = None
    if cuerpo is not None:
        encabezados["Content-Type"] = "application/json"
        datos = json.dumps(cuerpo).encode("utf-8")
    solicitud = Request(GATEWAY + ruta, data=datos, headers=encabezados, method=metodo)
    try:
        respuesta = urlopen(solicitud, timeout=35)
    except HTTPError as error:
        respuesta = error
    with respuesta:
        estado = respuesta.getcode()
        if estado != esperado:
            raise RuntimeError(f"{metodo} {ruta}: HTTP {estado}, se esperaba {esperado}")
        print(f"OK: {metodo} {ruta} -> HTTP {estado}")
        return json.load(respuesta) if estado < 400 and estado != 204 else None


def pruebas_publicas():
    salud = solicitar("/health")
    comprobar(
        salud["status"] == "ok"
        and set(salud["services"]) == SERVICIOS
        and all(estado == "ok" for estado in salud["services"].values()),
        "Gateway y seis servicios disponibles",
    )
    catalogo = solicitar(f"{API}/catalog")
    comprobar(catalogo["moneda"] == "CLP" and bool(catalogo["products"]), "Catalogo disponible en CLP")
    opciones = solicitar(f"{API}/bowl-options")
    comprobar(opciones["precioBase"] > 0 and bool(opciones["options"]), "Opciones de bowl disponibles")
    cotizacion = solicitar(f"{API}/orders/quote", COMPRA)
    comprobar(cotizacion["total"] > 0 and cotizacion["currency"] == "CLP", "Cotizacion valida")
    solicitar(f"{API}/orders/quote", {**COMPRA, "items": []}, esperado=422)


def pruebas_cliente(correo):
    sesion = solicitar("/auth/login", {"email": correo, "password": getpass("Clave del cliente: ")})
    token = sesion["access_token"]
    pedido_id = None
    try:
        identidad = solicitar("/auth/me", token=token)
        comprobar(identidad["role"] == "cliente", "Cuenta autenticada con rol cliente")
        clave = uuid4().hex
        pedido = solicitar(f"{API}/orders", COMPRA, token=token, clave=clave, esperado=201)
        pedido_id = pedido["id"]
        comprobar(pedido["state"] == "pendiente_pago", "Pedido nuevo pendiente de pago")
        repetido = solicitar(f"{API}/orders", COMPRA, token=token, clave=clave, esperado=201)
        comprobar(repetido["id"] == pedido_id, "El reintento conserva el identificador del pedido")
        resultado = solicitar(f"{API}/graphql", {
            "query": "query Pedido($id: ID!) { pedido(id: $id) { id estado total } }",
            "variables": {"id": pedido_id},
        }, token=token)
        comprobar(not resultado.get("errors") and resultado["data"]["pedido"] == {
            "id": pedido_id, "estado": pedido["state"], "total": pedido["total"],
        }, "GraphQL devuelve el pedido propio")
    finally:
        try:
            if pedido_id:
                cancelado = solicitar(f"{API}/orders/{pedido_id}/cancel", {
                    "motivo": "Cierre de prueba reproducible",
                }, token=token)
                comprobar(cancelado["state"] == "anulado", "Pedido de prueba anulado")
        finally:
            solicitar("/auth/logout", {}, token=token, esperado=204)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cliente", metavar="CORREO", help="Cuenta de prueba existente y verificada")
    args = parser.parse_args()
    try:
        pruebas_publicas()
        if args.cliente:
            pruebas_cliente(args.cliente)
    except (RuntimeError, URLError, TimeoutError, ValueError, KeyError, TypeError) as error:
        print(f"FALLO: {error}", file=sys.stderr)
        return 1
    print("Pruebas completadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
