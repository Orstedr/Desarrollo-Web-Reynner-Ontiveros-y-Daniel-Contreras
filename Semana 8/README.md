# Semana 8 – API Gateway + Vault + Backend securitizado

**Integrantes:**
- Daniel Contreras
- Reynner Ontiveros

```
Cliente → (Bearer token) → API Gateway → Vault → (X-Gateway-Secret) → Backend
```

- **client_token**: el cliente lo envía al Gateway (`Authorization: Bearer ...`). Si falta o es incorrecto → `401`.
- **backend_shared_secret**: el Gateway lo envía al backend (`X-Gateway-Secret`). Si alguien llama directo al backend sin él → `403`.
- Ambos secretos viven en **Vault** (`secret/gateway`), no en el código.

## Estructura

```
Semana 8/
├── fastapi/backend_api.py   # Backend protegido (puerto 9000)
├── gateway/gateway.py       # API Gateway (puerto 8000)
├── requirements.txt
└── README.md
```

## 1. Instalar

```bash
pip install -r requirements.txt
```

## 2. Levantar Vault (modo dev, sólo laboratorio)

```bash
docker run --name vault-dev -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=dev-only-token -d hashicorp/vault
```

> Alternativa sin Docker: descargar el binario de Vault desde hashicorp.com y ejecutar `vault server -dev -dev-root-token-id=dev-only-token`. El binario **no se sube al repositorio**.

## 3. Guardar los secretos

```bash
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway client_token="student-token-123" backend_shared_secret="gateway-api-secret-456"
```

## 4. Ejecutar (2 terminales, desde esta carpeta)

**Terminal 1 – Backend** (`INTERNAL_GATEWAY_SECRET` debe ser igual a `backend_shared_secret`)

```bash
cd fastapi
# Windows PowerShell:  $env:INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
export INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
uvicorn backend_api:app --host 0.0.0.0 --port 9000
```

**Terminal 2 – Gateway**

```bash
cd gateway
# Windows PowerShell:
#   $env:VAULT_ADDR="http://127.0.0.1:8200"
#   $env:VAULT_TOKEN="dev-only-token"
#   $env:BACKEND_URL="http://localhost:9000"
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="dev-only-token"
export BACKEND_URL="http://localhost:9000"
uvicorn gateway:app --host 0.0.0.0 --port 8000
```

## Endpoints

| Gateway | Backend |
|---|---|
| `GET :8000/api/products` | `:9000/products` |
| `GET :8000/api/orders` | `:9000/orders` |

## Pruebas

```bash
# Sin token -> 401
curl -i http://localhost:8000/api/products

# Token incorrecto -> 401
curl -i -H "Authorization: Bearer token-incorrecto" http://localhost:8000/api/products

# Token válido -> 200
curl -i -H "Authorization: Bearer student-token-123" http://localhost:8000/api/products
curl -i -H "Authorization: Bearer student-token-123" http://localhost:8000/api/orders

# Acceso directo al backend sin secreto -> 403
curl -i http://localhost:9000/products

# Backend con secreto interno -> 200 (sólo demostración)
curl -i -H "X-Gateway-Secret: gateway-api-secret-456" http://localhost:9000/products
```

## Rotar el token sin tocar código

```bash
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway client_token="nuevo-token-789" backend_shared_secret="gateway-api-secret-456"
```

Después de esto, `student-token-123` responde `401` y `nuevo-token-789` responde `200`.
