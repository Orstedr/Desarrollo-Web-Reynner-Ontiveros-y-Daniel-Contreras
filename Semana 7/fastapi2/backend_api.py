from fastapi import FastAPI

app = FastAPI(
    title="Backend API 2",
    description="Segundo backend con rutas en español (puerto 9100)"
)

@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "Backend API 2"
    }


@app.get("/productos")
def productos():
    return {
        "productos": [
            {"id": 1, "nombre": "Notebook", "precio": 900000},
            {"id": 2, "nombre": "Monitor", "precio": 250000}
        ]
    }


@app.get("/ordenes")
def ordenes():
    return {
        "ordenes": [
            {"id": 1001, "estado": "paid"},
            {"id": 1002, "estado": "pending"}
        ]
    }
