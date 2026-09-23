from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Sondagem(Base):
    __tablename__ = "sondagens"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "obra_id",
            "nome",
            name="uq_sondagens_usuario_obra_nome",
        ),
        Index(
            "ix_sondagens_usuario_obra",
            "usuario_id",
            "obra_id",
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
        ForeignKey("app.usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    obra_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app.obras.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    cota_boca: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
    )
    profundidade_final: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    criterio: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    nivel_agua: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    coord_x: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    coord_y: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 3),
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

    leituras: Mapped[list[LeituraSondagem]] = relationship(
        back_populates="sondagem",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LeituraSondagem.ordem",
    )

    @property
    def dados_cabecalho(self) -> dict[str, Decimal | str | None]:
        return {
            "cota_boca": self.cota_boca,
            "profundidade_final": self.profundidade_final,
            "criterio": self.criterio,
            "nivel_agua": self.nivel_agua,
            "coord_x": self.coord_x,
            "coord_y": self.coord_y,
        }


class LeituraSondagem(Base):
    __tablename__ = "sondagem_leituras"
    __table_args__ = (
        CheckConstraint(
            "profundidade IS NULL OR profundidade >= 0",
            name="ck_sondagem_leituras_profundidade",
        ),
        CheckConstraint(
            "nspt IS NULL OR nspt >= 0",
            name="ck_sondagem_leituras_nspt",
        ),
        Index(
            "ix_sondagem_leituras_sondagem_ordem",
            "sondagem_id",
            "ordem",
        ),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    sondagem_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app.sondagens.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordem: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    profundidade: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    cota: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
    )
    nspt: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    solo: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    familia: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    sondagem: Mapped[Sondagem] = relationship(
        back_populates="leituras",
    )
