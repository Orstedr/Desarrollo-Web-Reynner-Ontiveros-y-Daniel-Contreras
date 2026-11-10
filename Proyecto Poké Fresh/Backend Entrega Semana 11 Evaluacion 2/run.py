import json
import math
import shutil
import socket
import os
import signal
import subprocess
import sys
import time
from getpass import getpass
from pathlib import Path

import httpx
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

from accounts import HASHER, STAFF_MAIL
from common import MONGO_HOST, PORTS, VAULT_ADDR, db, mongo, opaque, uid


def wait_for(action, label, process=None):
    for _ in range(45):
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"{label} terminó con código {process.returncode}")
        try:
            return action()
        except (httpx.HTTPError, PyMongoError):
            time.sleep(1)
    raise RuntimeError(f"No fue posible iniciar {label}")


def seed():
    db.users.create_index("email", unique=True)
    db.users.create_index("run", unique=True, sparse=True)
    db.users.create_index("verify.digest", sparse=True)
    db.users.create_index("reset.digest", sparse=True)
    db.sessions.create_index("expires_at", expireAfterSeconds=0)
    db.outbox.create_index("expires_at", expireAfterSeconds=0)
    db.outbox.create_index([("recipient_id", 1), ("created_at", -1)])
    db.orders.create_index([("client_id", 1), ("_id", 1)])
    db.orders.create_index([("client_id", 1), ("checkout_key", 1)], unique=True)
    db.orders.create_index([("state", 1), ("paid_at", 1), ("_id", 1)])
    db.sales.create_index("sold_at")
    db.payment_outbox.create_index([("recipient_id", 1), ("created_at", -1)])
    catalog = json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))
    for group in ("products", "specials", "base", "proteina", "topping", "salsa"):
        for position, item in enumerate(catalog[group]):
            key = item["id"]
            data = {name: value for name, value in item.items() if name != "id"}
            if group in ("products", "specials"):
                data.update(kind="product", stock=40)
                if group == "specials":
                    data["categoria"] = "especiales"
            else:
                data.update(kind="ingredient", grupo=group, orden=position,
                            stock=None if key == "ninguno" else 60)
            db.inventory.update_one({"_id": key}, {"$setOnInsert": {**data, "habilitado": True}},
                                    upsert=True)
    db.config.update_one({"_id": "bowl"}, {"$setOnInsert": catalog["bowl"]}, upsert=True)
    if not db.users.find_one({"email": STAFF_MAIL}):
        password = os.environ.get("ADMIN_PASSWORD") or getpass("Clave inicial de admin (12 a 128 caracteres): ")
        if not 12 <= len(password) <= 128:
            raise RuntimeError("Defina ADMIN_PASSWORD de 12 a 128 caracteres")
        db.users.update_one({"email": STAFF_MAIL}, {"$setOnInsert": {
            "_id": uid(), "nombre": "Administración Demo", "role": "admin", "active": True,
            "verified": True, "version": 0, "password_hash": HASHER.hash(password)}}, upsert=True)


def mongo_setup(process):
    with MongoClient(f"mongodb://{MONGO_HOST}/?directConnection=true",
                     serverSelectionTimeoutMS=1000) as direct:
        wait_for(lambda: direct.admin.command("ping"), "MongoDB", process)
        try:
            direct.admin.command("replSetGetStatus")
        except OperationFailure as exc:
            if exc.code != 94:
                raise
            direct.admin.command("replSetInitiate", {"_id": "pf",
                                                     "members": [{"_id": 0, "host": MONGO_HOST}]})
    def check_primary():
        if not mongo.admin.command("hello")["isWritablePrimary"]:
            raise OperationFailure("MongoDB todavía no tiene un primario")
    wait_for(check_primary, "primario de MongoDB", process)


def vault_bootstrap(root_token, process):
    components = {service: {} for service in PORTS}
    links = [("gateway", target) for target in PORTS if target != "gateway"]
    links += [("graphql", "orders"), ("graphql", "payments"),
              ("clients", "auth"), ("clients", "orders"), ("orders", "clients"), ("orders", "inventory"),
              ("orders", "payments"), ("payments", "orders"), ("payments", "clients")]
    for caller, target in links:
        key = opaque()
        components[caller][f"to_{target}"] = key
        components[target][f"from_{caller}"] = key

    with httpx.Client(base_url=VAULT_ADDR, timeout=2, trust_env=False,
                      headers={"X-Vault-Token": root_token}) as client:
        wait_for(lambda: client.get("/v1/sys/health").raise_for_status(), "Vault", process)
        tokens = {}
        for service, settings in components.items():
            path = f"secret/data/pokefresh/{service}"
            client.post(f"/v1/{path}", json={"data": settings}).raise_for_status()
            client.put(f"/v1/sys/policies/acl/pf-{service}", json={
                "policy": f'path "{path}" {{ capabilities = ["read"] }}'
            }).raise_for_status()
            tokens[service] = client.post("/v1/auth/token/create", json={
                "policies": [f"pf-{service}"], "no_default_policy": True, "ttl": "20m"
            }).raise_for_status().json()["auth"]["client_token"]
        return tokens


def find_binary(variable, name):
    configured = os.getenv(variable, name)
    binary = shutil.which(configured)
    if binary is None:
        raise RuntimeError(f"No encuentro {name}. Agrégalo al PATH o define {variable}.")
    return binary


def check_ports():
    for port in (*PORTS.values(), 8200, 8201, 27017):
        with socket.socket() as probe:
            if os.name == "nt":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise RuntimeError(f"El puerto local {port} está ocupado") from None


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def shutdown_mongo(process):
    if process.poll() is not None:
        return
    with MongoClient(f"mongodb://{MONGO_HOST}/?directConnection=true",
                     serverSelectionTimeoutMS=1000, socketTimeoutMS=4000) as direct:
        try:
            direct.admin.command("shutdown", force=True, timeoutSecs=0)
        except PyMongoError:
            # El servidor puede cerrar la conexión antes de contestar.
            pass
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        stop_process(process)


def main():
    if sys.argv[1:] == ["seed"]:
        mongo.admin.command("ping")
        seed()
        print("Carga inicial aplicada", flush=True)
        return
    if sys.argv[1:]:
        raise SystemExit("Uso: python run.py [seed]")
    for env, low, high, default in (("ORIGIN_LAT", -90, 90, "-33.6110"),
                                    ("ORIGIN_LON", -180, 180, "-70.5750")):
        value = float(os.getenv(env, default))
        if not math.isfinite(value) or not low <= value <= high:
            raise RuntimeError(f"Coordenada inválida: {env}")

    mongod = find_binary("MONGOD_EXE", "mongod")
    vault = find_binary("VAULT_EXE", "vault")
    check_ports()
    root = Path(__file__).resolve().parent
    data = root / ".local" / "mongo"
    data.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items()
           if key not in ("ADMIN_PASSWORD", "VAULT_DEV_ROOT_TOKEN_ID")}
    root_token = opaque()
    group = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    children = {}
    mongo_process = None

    def interrupt(_number, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    try:
        mongo_args = [mongod, "--dbpath", str(data), "--bind_ip", "127.0.0.1",
                      "--port", "27017", "--replSet", "pf", "--logpath",
                      str(data.parent / "mongo.log"), "--logappend"]
        if os.name != "nt":
            mongo_args.extend(["--nounixsocket", "--setParameter", "diagnosticDataCollectionEnabled=false"])
        mongo_process = subprocess.Popen(mongo_args, env=env, creationflags=group)
        mongo_setup(mongo_process)
        seed()
        children["Vault"] = subprocess.Popen(
            [vault, "server", "-dev", "-dev-no-store-token",
             "-dev-listen-address=127.0.0.1:8200"],
            env={**env, "VAULT_DEV_ROOT_TOKEN_ID": root_token,
                 "VAULT_API_ADDR": VAULT_ADDR, "VAULT_CLUSTER_ADDR": "https://127.0.0.1:8201"},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=group)
        tokens = vault_bootstrap(root_token, children["Vault"])
        for service in [*list(PORTS)[1:], "gateway"]:
            environment = {**env, "PF_SERVICE": service, "PF_VAULT_TOKEN": tokens[service]}
            children[service] = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1",
                 "--port", str(PORTS[service]), "--no-access-log",
                 "--log-level", "info", "--limit-concurrency", "100",
                 "--timeout-graceful-shutdown", "3"], env=environment, cwd=root,
                creationflags=group)
        print("Iniciando API local: http://127.0.0.1:8000/docs (Ctrl+C para detener)", flush=True)
        while True:
            for name, child in {"MongoDB": mongo_process, **children}.items():
                if child.poll() is not None:
                    raise RuntimeError(f"{name} se detuvo con código {child.returncode}")
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        for child in reversed(children.values()):
            stop_process(child)
        if mongo_process is not None:
            shutdown_mongo(mongo_process)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, httpx.HTTPError, PyMongoError) as exc:
        raise SystemExit(f"Error de arranque: {exc}") from None
