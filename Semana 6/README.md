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
- `main.py`: instancia de FastAPI y endpoint `/health`.

> Los endpoints de `items` (CRUD) se agregan en un PR posterior.
