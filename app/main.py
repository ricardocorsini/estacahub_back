from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router

app = FastAPI(
    title="Backend Padrão",
    description="Estrutura inicial de backend em Python com FastAPI.",
    version="0.1.0",
)

# =====================
# Middlewares
# =====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# Include routers
# =====================

app.include_router(health_router, 
                   prefix="/api",
                   )


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "message": "Backend rodando com sucesso.",
        "docs": "/docs",
        "health": "/health",
    }