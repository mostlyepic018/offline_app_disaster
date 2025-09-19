from fastapi import FastAPI
from .api.routes import router as api_router

app = FastAPI(title="Offline Disaster Alert API", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(api_router)
