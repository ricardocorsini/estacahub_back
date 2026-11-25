from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ObraExemplo(Base):
    __tablename__ = "obras_exemplo"
    __table_args__ = {"schema": "app"}

    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app.usuarios.id", ondelete="CASCADE"), primary_key=True,
    )
    exemplo: Mapped[str] = mapped_column(String(32), primary_key=True)
    obra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app.obras.id", ondelete="CASCADE"), nullable=False, unique=True,
    )
