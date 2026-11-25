from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.estaca import Estaca
from app.models.obra import Obra
from app.models.obra_exemplo import ObraExemplo
from app.models.sondagem import Sondagem
from app.models.usuario import Usuario
from app.schemas.estacas import EstacaCreate
from app.schemas.obras import ObraCreate
from app.schemas.sondagens import SondagemCreate
from app.services.sondagens_service import aplicar_payload_sondagem


ARQUIVO_BALSAS = Path(__file__).resolve().parents[1] / "data" / "obra_exemplo_balsas.json"


class ModeloObraExemplo(BaseModel):
    obra: ObraCreate
    estacas: list[EstacaCreate]
    sondagens: list[SondagemCreate]


def abrir_exemplo_balsas(db: Session, usuario_id: int) -> Obra:
    try:
        # Serializa duas primeiras aberturas simultâneas da mesma conta no PostgreSQL.
        db.execute(select(Usuario.id).where(Usuario.id == usuario_id).with_for_update()).scalar_one()
        existente = db.scalar(
            select(Obra).join(ObraExemplo, ObraExemplo.obra_id == Obra.id).where(
                ObraExemplo.usuario_id == usuario_id, ObraExemplo.exemplo == "balsas",
                Obra.usuario_id == usuario_id,
            )
        )
        if existente is not None:
            return existente

        modelo = ModeloObraExemplo.model_validate_json(ARQUIVO_BALSAS.read_bytes())
        obra = Obra(
            usuario_id=usuario_id, data_cadastro=datetime.now(timezone.utc).date(),
            **modelo.obra.model_dump(exclude={"nome_arquivo_foto", "data_cadastro"}),
        )
        db.add(obra)
        db.flush()
        for payload in modelo.sondagens:
            sondagem = Sondagem(obra_id=obra.id, usuario_id=usuario_id)
            aplicar_payload_sondagem(sondagem, payload)
            db.add(sondagem)
        for estaca in modelo.estacas:
            db.add(Estaca(obra_id=obra.id, usuario_id=usuario_id, **estaca.model_dump()))
        db.add(ObraExemplo(usuario_id=usuario_id, exemplo="balsas", obra_id=obra.id))
        db.commit()
        return obra
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, "Não foi possível abrir a obra de exemplo.") from exc
