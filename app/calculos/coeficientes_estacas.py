import re
from dataclasses import dataclass
from typing import Literal
from unicodedata import combining, normalize

from app.schemas.estacas import TipoEstaca


FamiliaSolo = Literal["Granular", "Intermediário", "Coesivo"]

KN_POR_TF = 9.80665
FS_GLOBAL = 2.0
FS_LATERAL_DQ = 1.30
FS_PONTA_DQ = 4.0


@dataclass(frozen=True)
class Solo:
    nome: str
    familia: FamiliaSolo
    c_dq_kpa: int
    k_av_kpa: int
    alfa_av_percentual: float


def chave_solo(nome: str) -> str:
    sem_acentos = "".join(
        letra for letra in normalize("NFKD", nome.casefold()) if not combining(letra)
    )
    return re.sub(r"[-\s\u2010-\u2015]+", " ", sem_acentos).strip()


# Perfil de coeficientes do GEOSPT-STRUCT, identificado em docs/carga-admissivel.md.
SOLOS = {
    chave_solo(solo.nome): solo
    for solo in (
        Solo("Areia", "Granular", 400, 1000, 1.4),
        Solo("Areia Siltosa", "Granular", 400, 800, 2.0),
        Solo("Areia Silto-argilosa", "Granular", 400, 700, 2.4),
        Solo("Areia Argilo-siltosa", "Granular", 400, 500, 2.8),
        Solo("Areia Argilosa", "Granular", 400, 600, 3.0),
        Solo("Silte", "Intermediário", 200, 400, 3.0),
        Solo("Silte Arenoso", "Intermediário", 250, 550, 2.2),
        Solo("Silte Areno-argiloso", "Intermediário", 250, 450, 2.8),
        Solo("Silte Argilo-arenoso", "Intermediário", 200, 250, 3.0),
        Solo("Silte Argiloso", "Intermediário", 200, 230, 3.4),
        Solo("Argila", "Coesivo", 120, 200, 6.0),
        Solo("Argila Arenosa", "Coesivo", 120, 350, 2.4),
        Solo("Argila Areno-siltosa", "Coesivo", 120, 300, 2.8),
        Solo("Argila Silto-arenosa", "Coesivo", 120, 330, 3.0),
        Solo("Argila Siltosa", "Coesivo", 120, 220, 4.0),
    )
}

ALFA_DQ_MODIFICADO: dict[FamiliaSolo, float] = {
    "Granular": 0.50, "Intermediário": 0.60, "Coesivo": 0.85,
}
_BETA_UNITARIO = dict.fromkeys(ALFA_DQ_MODIFICADO, 1.0)
BETA_DQ: dict[TipoEstaca, dict[FamiliaSolo, float]] = {
    "helice_continua": _BETA_UNITARIO,
    "escavada_seco": {"Granular": 0.50, "Intermediário": 0.65, "Coesivo": 0.80},
    "escavada_fluido": {"Granular": 0.60, "Intermediário": 0.75, "Coesivo": 0.90},
    "pre_moldada_cravada": _BETA_UNITARIO,
    "raiz": dict.fromkeys(ALFA_DQ_MODIFICADO, 1.50),
}

REDUTOR_PONTA: dict[TipoEstaca, float] = {
    "helice_continua": 0.50,
    "escavada_seco": 0.50,
    "escavada_fluido": 0.60,
    "pre_moldada_cravada": 1.00,
    "raiz": 0.50,
}
