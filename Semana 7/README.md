# PR 1 — Backends FastAPI

Primer PR: los dos backends que consume el API Gateway. No dependen de nada más.

- `fastapi/backend_api.py` — Backend 1, rutas en inglés (puerto 9000)
- `fastapi2/backend_api.py` — Backend 2, rutas en español (puerto 9100)

## Cómo ejecutar

```bash
pip install -r requirements.txt

# Terminal 1
cd fastapi
uvicorn backend_api:app --host 0.0.0.0 --port 9000

# Terminal 2
cd fastapi2
uvicorn backend_api:app --host 0.0.0.0 --port 9100
```

## Probar

```bash
curl http://localhost:9000/products
curl http://localhost:9000/orders
curl http://localhost:9100/productos
curl http://localhost:9100/ordenes
```
