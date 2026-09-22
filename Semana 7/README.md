## Cómo ejecutar

```bash
pip install -r requirements.txt

cd gateway
uvicorn gateway:app --host 0.0.0.0 --port 8000
```

## Endpoints

| Gateway | Backend |
|---|---|
| `GET :8000/api/products` | `:9000/products` |
| `GET :8000/api/orders` | `:9000/orders` |
| `GET :8000/api/productos` | `:9100/productos` |
| `GET :8000/api/ordenes` | `:9100/ordenes` |

## Probar

```bash
curl http://localhost:8000/api/products
curl http://localhost:8000/api/orders
curl http://localhost:8000/api/productos
curl http://localhost:8000/api/ordenes
```
