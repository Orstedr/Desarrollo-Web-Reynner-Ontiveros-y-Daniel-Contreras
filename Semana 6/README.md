# FastAPI + MongoDB - PR Semana

Implementación de una API REST con FastAPI y MongoDB para administrar `items`.

## Requisitos
- Python
- MongoDB funcionando localmente
- MongoDB disponible en `mongodb://localhost:27017`

## Instalación
```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Ejecutar
```powershell
python -m uvicorn main:app --reload
```

Abrir:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Base de datos
- Base: `bdunab2`
- Colección: `items`

## Estructura del proyecto
- `database.py`: conexión a MongoDB y ciclo de vida de la app.
- `models.py`: modelos Pydantic de `Item`.
- `routers/items.py`: endpoints CRUD de `items`.
- `main.py`: instancia de FastAPI y registro de rutas.

## Endpoints
- GET `/health`
- GET `/items`
- POST `/items`
- GET `/items/{item_id}`
- PUT `/items/{item_id}`
- DELETE `/items/{item_id}`

`GET /items` admite `q`, `skip` y `limit`.

## Ejemplo de POST
```json
{
  "nombre": "Teclado",
  "precio": 19990,
  "tags": ["computacion", "perifericos"],
  "activo": true
}
```

## Errores
- 400: ID inválido.
- 404: item no encontrado.
- 422: datos que no cumplen las validaciones.
