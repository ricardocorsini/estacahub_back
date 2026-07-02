import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.schemas.obras import ObraCreate, ObraUpdate


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OBRAS_FILE = DATA_DIR / "obras.json"


def _ensure_storage_exists() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not OBRAS_FILE.exists():
        OBRAS_FILE.write_text("[]", encoding="utf-8")


def _read_obras() -> list[dict[str, Any]]:
    _ensure_storage_exists()

    try:
        content = OBRAS_FILE.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError:
        return []


def _write_obras(obras: list[dict[str, Any]]) -> None:
    _ensure_storage_exists()

    OBRAS_FILE.write_text(
        json.dumps(obras, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id(obras: list[dict[str, Any]]) -> int:
    if not obras:
        return 1

    return max(obra["id"] for obra in obras) + 1


def _model_to_dict(model: Any, exclude_unset: bool = False) -> dict[str, Any]:
    """
    Compatível com Pydantic v1 e v2.
    """
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=exclude_unset)

    return model.dict(exclude_unset=exclude_unset)


def listar_obras_service() -> list[dict[str, Any]]:
    return _read_obras()


def obter_obra_service(obra_id: int) -> dict[str, Any]:
    obras = _read_obras()

    for obra in obras:
        if obra["id"] == obra_id:
            return obra

    raise HTTPException(
        status_code=404,
        detail="Obra não encontrada.",
    )


def criar_obra_service(payload: ObraCreate) -> dict[str, Any]:
    obras = _read_obras()

    now = _now_iso()

    nova_obra = {
        "id": _next_id(obras),
        **_model_to_dict(payload),
        "criadoEm": now,
        "atualizadoEm": now,
    }

    obras.append(nova_obra)
    _write_obras(obras)

    return nova_obra


def atualizar_obra_service(obra_id: int, payload: ObraCreate) -> dict[str, Any]:
    obras = _read_obras()

    for index, obra in enumerate(obras):
        if obra["id"] == obra_id:
            obra_atualizada = {
                "id": obra_id,
                **_model_to_dict(payload),
                "criadoEm": obra["criadoEm"],
                "atualizadoEm": _now_iso(),
            }

            obras[index] = obra_atualizada
            _write_obras(obras)

            return obra_atualizada

    raise HTTPException(
        status_code=404,
        detail="Obra não encontrada.",
    )


def atualizar_obra_parcial_service(
    obra_id: int,
    payload: ObraUpdate,
) -> dict[str, Any]:
    obras = _read_obras()

    dados_atualizacao = _model_to_dict(payload, exclude_unset=True)

    for index, obra in enumerate(obras):
        if obra["id"] == obra_id:
            obra_atualizada = {
                **obra,
                **dados_atualizacao,
                "atualizadoEm": _now_iso(),
            }

            obras[index] = obra_atualizada
            _write_obras(obras)

            return obra_atualizada

    raise HTTPException(
        status_code=404,
        detail="Obra não encontrada.",
    )


def remover_obra_service(obra_id: int) -> dict[str, Any]:
    obras = _read_obras()

    for obra in obras:
        if obra["id"] == obra_id:
            obras.remove(obra)
            _write_obras(obras)

            return {
                "message": "Obra removida com sucesso.",
                "id": obra_id,
            }

    raise HTTPException(
        status_code=404,
        detail="Obra não encontrada.",
    )