from fastapi import FastAPI

from database import lifespan

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
