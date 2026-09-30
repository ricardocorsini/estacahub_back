from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Obra(Base):
    __tablename__ = "obras"
    __table_args__ = (
        CheckConstraint(
            "sistema_coordenadas IN ('local', 'utm')",
            name="ck_obras_sistema_coordenadas",
        ),
        Index(
            "ix_obras_usuario_id",
            "usuario_id",
        ),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "app.usuarios.id",
            name="fk_obras_usuario_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    numero: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    localizacao: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    data_cadastro: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    sistema_coordenadas: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="local",
        server_default="local",
    )
    responsavel_tecnico: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    observacoes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    foto_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    legenda_foto: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
