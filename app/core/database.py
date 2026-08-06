import importlib
import pkgutil
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def import_models() -> None:
    """
    Importa automaticamente todos os módulos Python
    existentes dentro de app.models.

    Exemplo:
        app/models/obra.py
        app/models/projeto.py
        app/models/material.py

    Todos serão carregados sem precisar registrá-los
    manualmente no __init__.py.
    """

    import app.models

    for module_info in pkgutil.iter_modules(
        app.models.__path__,
        prefix="app.models.",
    ):
        importlib.import_module(module_info.name)


def init_db() -> None:
    """
    Inicializa schema e tabelas da aplicação.
    """

    # Cria o schema PostgreSQL caso ainda não exista
    with engine.begin() as connection:
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS app")
        )

    # Descobre e importa automaticamente todos os models
    import_models()

    # Cria somente as tabelas inexistentes
    Base.metadata.create_all(
        bind=engine,
        checkfirst=True,
    )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()