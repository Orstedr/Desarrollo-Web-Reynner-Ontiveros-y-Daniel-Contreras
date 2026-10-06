# Semana 9 – API Gateway + Vault + Backends securitizados + Auth Service

**Integrantes:**
- Daniel Contreras
- Reynner Ontiveros

```
Cliente → API Gateway → Auth Service   (¿el token es válido? ¿quién es? ¿qué roles tiene?)
              │  └────► Vault          (secretos entre servicios)
              └─(X-Gateway-Secret + identidad)─► Backend 1 (:9000) / Backend 2 (:9100)
```

| Componente | Puerto | Responsabilidad |
|---|---|---|
| **API Gateway** | 8000 | Valida sesión, autoriza por rol, enruta y propaga identidad |
| **Auth Service** | 8100 | Verifica credenciales (Argon2), emite tokens, introspection, logout |
| **Vault** | 8200 | Guarda los secretos entre servicios (`secret/gateway`) |
| **Backend 1** | 9000 | Rutas en inglés (`/products`, `/orders`) |
| **Backend 2** | 9100 | Rutas en español (`/productos`, `/ordenes`) |

## Cómo funciona

- **Auth Service** (`auth-service/`): `POST /login`, `POST /introspect`, `POST /logout`. Hash Argon2id, tokens opacos, sesión de 15 min.
- **auth_introspection_secret**: el Gateway lo lee de Vault y lo manda al Auth Service en el header `X-Gateway-Auth-Secret` (`/introspect` y `/logout`). El Auth Service recibe el mismo valor por la variable de entorno `AUTH_INTROSPECTION_SECRET`. Si no coincide → `403`.
- **Gateway**: valida el token contra el Auth Service. Expone `POST /auth/login`, `GET /auth/me` y `POST /auth/logout`. El token queda en una cookie `HttpOnly`; también se acepta `Authorization: Bearer <access_token>`.
- **Roles**: `DELETE /api/products/{id}` y `DELETE /api/productos/{id}` exigen `admin` (se comprueba en el Gateway y en el backend).
- **Identidad** que el Gateway manda al backend: `X-Authenticated-User`, `X-Authenticated-Username`, `X-Authenticated-Roles`.
- **Vault**: los secretos (`secret/gateway`) se leen en cada request, nunca están en el código. Guarda `backend_shared_secret` y `auth_introspection_secret`.

## Estructura

```
.
├── auth-service/auth_service.py  # Auth Service (puerto 8100)
├── fastapi/backend_api.py        # Backend 1 protegido (puerto 9000, rutas en inglés)
├── fastapi2/backend_api.py       # Backend 2 protegido (puerto 9100, rutas en español)
├── gateway/gateway.py            # API Gateway (puerto 8000)
├── requirements.txt
└── README.md
```

## Usuarios de prueba

| Usuario | Contraseña | Roles |
|---|---|---|
| `ana` | `1234` | `user` |
| `pedro` | `5678` | `user` |
| `ernesto` | `admin123` | `user`, `admin` |

## 1. Instalar (Python 3.10 o superior)

```bash
pip install -r requirements.txt
```

## 2. Levantar Vault (modo dev, sólo laboratorio)

```bash
docker run --name vault-dev -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=dev-only-token -d hashicorp/vault
```

> Alternativa sin Docker: descargar el binario de Vault desde hashicorp.com (no se sube al repo, pesa ~380 MB) y ejecutar `vault server -dev -dev-root-token-id=dev-only-token`.

## 3. Guardar los secretos

```bash
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway backend_shared_secret="gateway-api-secret-456" auth_introspection_secret="gateway-auth-secret-789"
```

## 4. Ejecutar (4 terminales, desde esta carpeta)

**Terminal 1 – Backend 1** (`INTERNAL_GATEWAY_SECRET` debe ser igual a `backend_shared_secret`)

```bash
cd fastapi
# Windows PowerShell:  $env:INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
export INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
uvicorn backend_api:app --host 0.0.0.0 --port 9000
```

**Terminal 2 – Backend 2**

```bash
cd fastapi2
# Windows PowerShell:  $env:INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
export INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
uvicorn backend_api:app --host 0.0.0.0 --port 9100
```

**Terminal 3 – Auth Service**

```bash
cd auth-service
# Debe ser igual a auth_introspection_secret guardado en Vault
# Windows PowerShell:  $env:AUTH_INTROSPECTION_SECRET="gateway-auth-secret-789"
export AUTH_INTROSPECTION_SECRET="gateway-auth-secret-789"
uvicorn auth_service:app --host 0.0.0.0 --port 8100
```

**Terminal 4 – Gateway**

```bash
cd gateway
# Windows PowerShell:
#   $env:VAULT_ADDR="http://127.0.0.1:8200"
#   $env:VAULT_TOKEN="dev-only-token"
#   $env:BACKEND_URL="http://localhost:9000"
#   $env:BACKEND_URL2="http://localhost:9100"
#   $env:AUTH_SERVICE_URL="http://127.0.0.1:8100"
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="dev-only-token"
export BACKEND_URL="http://localhost:9000"
export BACKEND_URL2="http://localhost:9100"
export AUTH_SERVICE_URL="http://127.0.0.1:8100"
uvicorn gateway:app --host 0.0.0.0 --port 8000
```

## Endpoints

| Gateway | Destino | Protección |
|---|---|---|
| `POST :8000/auth/login` | Auth `:8100/login` | pública (200/401) |
| `GET :8000/auth/me` | Auth `/introspect` | sesión (200/401) |
| `POST :8000/auth/logout` | Auth `:8100/logout` | 200 |
| `GET :8000/api/products` | `:9000/products` | sesión |
| `GET :8000/api/orders` | `:9000/orders` | sesión |
| `GET :8000/api/productos` | `:9100/productos` | sesión |
| `GET :8000/api/ordenes` | `:9100/ordenes` | sesión |
| `DELETE :8000/api/products/{id}` | `:9000/products/{id}` | sesión + `admin` |
| `DELETE :8000/api/productos/{id}` | `:9100/productos/{id}` | sesión + `admin` |

## Pruebas

```bash
# Acceso directo a backends / Auth sin secreto -> 403
curl -i http://localhost:9000/products
curl -i http://localhost:9100/productos
curl -i -X POST http://localhost:8100/introspect -H "Content-Type: application/json" -d '{"token":"x"}'

# Auth /introspect con el secreto del Gateway -> 200 {"active": false}
curl -i -X POST http://localhost:8100/introspect -H "Content-Type: application/json" -H "X-Gateway-Auth-Secret: gateway-auth-secret-789" -d '{"token":"x"}'

# Sin sesión -> 401
curl -i http://localhost:8000/api/products

# Login incorrecto -> 401
curl -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"ana","password":"incorrecta"}'

# Login Ana -> 200 + cookie (queda en cookies.txt)
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"ana","password":"1234"}'

# Con sesión -> 200
curl -i -b cookies.txt http://localhost:8000/auth/me
curl -i -b cookies.txt http://localhost:8000/api/products
curl -i -b cookies.txt http://localhost:8000/api/orders
curl -i -b cookies.txt http://localhost:8000/api/productos
curl -i -b cookies.txt http://localhost:8000/api/ordenes

# Recurso que no existe en el Gateway -> 404
curl -i -b cookies.txt http://localhost:8000/api/foo

# Ana intenta eliminar -> 403
curl -i -b cookies.txt -X DELETE http://localhost:8000/api/products/1
curl -i -b cookies.txt -X DELETE http://localhost:8000/api/productos/1

# Ernesto (admin) elimina -> 200
curl -i -c admin.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"ernesto","password":"admin123"}'
curl -i -b admin.txt -X DELETE http://localhost:8000/api/products/1
curl -i -b admin.txt -X DELETE http://localhost:8000/api/productos/1

# Logout y comprobar que la sesión murió -> 401
curl -i -b cookies.txt -X POST http://localhost:8000/auth/logout
curl -i -b cookies.txt http://localhost:8000/auth/me
```

> En PowerShell usar `curl.exe` (no el alias `curl`) y comillas dobles escapadas para el JSON.

## Rotar secretos

```bash
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway backend_shared_secret="gateway-api-secret-456" auth_introspection_secret="nuevo-secreto-auth-999"
```

El Gateway lee ambos secretos desde Vault en cada request, así que toma el cambio sin reiniciar. Después hay que actualizar `AUTH_INTROSPECTION_SECRET` en el Auth Service (y `INTERNAL_GATEWAY_SECRET` en los backends si cambia `backend_shared_secret`) y reiniciarlos; mientras tanto el Gateway recibe `502` del Auth Service.
