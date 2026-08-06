from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.routers.health import router as health_router
from app.routers.obras_routers import router as obras_router


settings = get_settings()


# ============================================================
# Lifecycle da API
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executa tarefas de inicialização antes da API começar
    a receber requisições.
    """

    init_db()

    yield


# ============================================================
# Aplicação FastAPI
# ============================================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "API local do projeto Engenharia Fullstack, "
        "com persistência em PostgreSQL."
    ),
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Routers
# ============================================================

app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    obras_router,
    prefix="/api",
)


# ============================================================
# Root
# ============================================================

@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "message": "Backend rodando com sucesso.",
        "docs": "/docs",
        "health": "/api/health",
        "obras": "/api/obras",
    }