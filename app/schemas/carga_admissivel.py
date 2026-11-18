from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.calculos.coeficientes_estacas import FamiliaSolo
from app.schemas.estacas import TipoEstaca


class ModeloCalculo(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, allow_inf_nan=False, extra="forbid",
    )


class OpcoesCargaAdmissivel(ModeloCalculo):
    despreza_ultimo_metro_atrito: bool = Field(default=True, strict=True)
    aplica_redutor_ponta: bool = Field(default=False, strict=True)
    tratamento_ponta: Literal["calculado", "contato_com_ressalva", "sem_contato"] = "calculado"
    limita_ponta_por_atrito: bool = Field(default=False, strict=True)


class CargaAdmissivelRequest(ModeloCalculo):
    sondagem_id: int = Field(gt=0, le=2**63 - 1, strict=True)
    cota_ponta_m: int | None = Field(
        default=None,
        strict=True,
        description="Cota inteira para o memorial detalhado de um ponto da curva.",
    )
    opcoes: OpcoesCargaAdmissivel = Field(default_factory=OpcoesCargaAdmissivel)


class CargaPorMetodo(ModeloCalculo):
    resistencia_lateral_kn: float
    resistencia_ponta_bruta_kn: float
    resistencia_ponta_kn: float
    resistencia_ruptura_kn: float
    carga_admissivel_global_kn: float
    carga_admissivel_parcial_kn: float | None
    carga_admissivel_geotecnica_kn: float
    carga_admissivel_geotecnica_tf: float
    carga_admissivel_final_kn: float
    carga_admissivel_final_tf: float
    criterio_governante: Literal["geotecnico_global", "geotecnico_parcial", "estrutural"]
    ponta_limitada_por_atrito: bool


class CotaPontaResultado(ModeloCalculo):
    cota_ponta_m: int
    comprimento_na_grade_m: int
    nspt_ponta: int
    quantidade_leituras_ponta: int
    comprimento_fuste_sem_spt_m: int
    ultimo_metro_desprezado: bool
    decourt_quaresma: CargaPorMetodo
    aoki_velloso: CargaPorMetodo


class AmostraGrade(ModeloCalculo):
    leitura_id: int
    cota_grade_m: int
    cota_leitura_m: float
    nspt_medido: int
    solo: str
    familia: FamiliaSolo


class AmostraPonta(AmostraGrade):
    nspt_usado: int


class AtritoLateral(ModeloCalculo):
    nspt_usado: int
    tensao_kpa: float
    resistencia_kn: float


class AtritoDecourtQuaresma(AtritoLateral):
    beta: float


class AtritoAokiVelloso(AtritoLateral):
    k_kpa: float
    alfa_percentual: float
    f2: float


class CamadaAtrito(ModeloCalculo):
    amostra: AmostraGrade
    cota_base_m: int
    desprezada: bool = False
    decourt_quaresma: AtritoDecourtQuaresma
    aoki_velloso: AtritoAokiVelloso


class TrechoSemSPT(ModeloCalculo):
    cota_topo_m: int
    cota_base_m: int


class PontaDecourtQuaresma(ModeloCalculo):
    c_kpa: float
    alfa: float
    tensao_kpa: float


class PontaAokiVelloso(ModeloCalculo):
    k_kpa: float
    f1: float
    tensao_kpa: float


class MemorialCargaAdmissivel(ModeloCalculo):
    cota_ponta_m: int
    leituras_ponta: list[AmostraPonta]
    camadas_atrito: list[CamadaAtrito]
    trechos_sem_spt: list[TrechoSemSPT]
    ponta_decourt_quaresma: PontaDecourtQuaresma
    ponta_aoki_velloso: PontaAokiVelloso


class CargaAdmissivelResponse(ModeloCalculo):
    obra_id: int
    estaca_id: int
    sondagem_id: int
    nome_estaca: str
    nome_sondagem: str
    tipo_estaca: TipoEstaca
    diametro_cm: float
    cota_boca_m: float
    cota_arrasamento_m: float
    cota_arrasamento_grade_m: int
    area_ponta_m2: float
    perimetro_m: float
    capacidade_estrutural_tf: float
    capacidade_estrutural_kn: float
    carga_prevista_tf: float
    kn_por_tf: float
    fs_global: float
    fs_lateral_decourt_quaresma: float
    fs_ponta_decourt_quaresma: float
    fator_redutor_ponta: float
    opcoes: OpcoesCargaAdmissivel
    avisos: list[Literal["verificar_contato_ponta"]]
    curva: list[CotaPontaResultado]
    memorial: MemorialCargaAdmissivel | None
