from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, Index,
    Numeric, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Estaca(Base):
    __tablename__ = "estacas"
    __table_args__ = (
        CheckConstraint("length(btrim(nome)) > 0", name="ck_estacas_nome"),
        CheckConstraint(
            "tipo IN ('helice_continua', 'escavada_seco', 'escavada_fluido', "
            "'pre_moldada_cravada', 'raiz')",
            name="ck_estacas_tipo",
        ),
        CheckConstraint("coord_x BETWEEN -999999999 AND 999999999", name="ck_estacas_x"),
        CheckConstraint("coord_y BETWEEN -999999999 AND 999999999", name="ck_estacas_y"),
        CheckConstraint("diametro_cm > 0 AND diametro_cm <= 10000", name="ck_estacas_diametro"),
        CheckConstraint(
            "capacidade_estrutural_tf > 0 AND capacidade_estrutural_tf <= 999999999",
            name="ck_estacas_capacidade",
        ),
        CheckConstraint(
            "cota_arrasamento BETWEEN -999999999 AND 999999999",
            name="ck_estacas_cota",
        ),
        CheckConstraint("carga_prevista_tf BETWEEN 0 AND 999999999", name="ck_estacas_carga"),
        Index("ix_estacas_usuario_obra", "usuario_id", "obra_id"),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app.usuarios.id", ondelete="CASCADE"), nullable=False,
    )
    obra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app.obras.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    coord_x: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    coord_y: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    diametro_cm: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    capacidade_estrutural_tf: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    cota_arrasamento: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    carga_prevista_tf: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )


# Nomes únicos por obra, inclusive entre E-01/e-01 e sob concorrência.
Index("uq_estacas_obra_nome", Estaca.obra_id, func.lower(func.btrim(Estaca.nome)), unique=True)
