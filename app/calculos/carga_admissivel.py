from dataclasses import dataclass
from decimal import Decimal
from math import ceil, floor, pi

from app.calculos.coeficientes_estacas import (
    ALFA_DQ_MODIFICADO, BETA_DQ, FS_GLOBAL, FS_LATERAL_DQ, FS_PONTA_DQ,
    KN_POR_TF, REDUTOR_PONTA, Solo,
)
from app.schemas.carga_admissivel import (
    AmostraGrade, AmostraPonta, AtritoAokiVelloso, AtritoDecourtQuaresma,
    CamadaAtrito, CargaPorMetodo, CotaPontaResultado, MemorialCargaAdmissivel,
    OpcoesCargaAdmissivel, PontaAokiVelloso, PontaDecourtQuaresma, TrechoSemSPT,
)
from app.schemas.estacas import TipoEstaca


JANELA_SPT_M = Decimal("0.5")


class ErroPerfilCalculo(ValueError):
    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo


@dataclass(frozen=True)
class LeituraSPT:
    id: int
    cota_m: Decimal
    nspt: int
    solo: Solo


@dataclass(frozen=True)
class EstacaCalculo:
    tipo: TipoEstaca
    diametro_m: float
    cota_arrasamento_m: Decimal
    capacidade_estrutural_tf: float

    @property
    def cota_arrasamento_grade_m(self) -> int:
        return floor(self.cota_arrasamento_m)

    @property
    def area_ponta_m2(self) -> float:
        return pi * self.diametro_m**2 / 4

    @property
    def perimetro_m(self) -> float:
        return pi * self.diametro_m

    @property
    def capacidade_estrutural_kn(self) -> float:
        return self.capacidade_estrutural_tf * KN_POR_TF

    def fator_redutor_ponta(self, opcoes: OpcoesCargaAdmissivel) -> float:
        return REDUTOR_PONTA[self.tipo] if opcoes.aplica_redutor_ponta else 1.0


def _compatibilizar_leituras(leituras: list[LeituraSPT]) -> dict[int, LeituraSPT]:
    grade: dict[int, LeituraSPT] = {}
    for leitura in leituras:
        for cota in range(ceil(leitura.cota_m - JANELA_SPT_M), floor(leitura.cota_m + JANELA_SPT_M) + 1):
            anterior = grade.get(cota)
            # A ordem de cadastro resolve empates entre leituras equidistantes.
            if anterior is None or abs(leitura.cota_m - cota) < abs(anterior.cota_m - cota):
                grade[cota] = leitura
    return grade


def _amostra(cota: int, leitura: LeituraSPT) -> AmostraGrade:
    return AmostraGrade(
        leitura_id=leitura.id,
        cota_grade_m=cota,
        cota_leitura_m=float(leitura.cota_m),
        nspt_medido=leitura.nspt,
        solo=leitura.solo.nome,
        familia=leitura.solo.familia,
    )


def _nspt_usado(nspt: int, minimo: int = 1) -> int:
    return min(50, max(minimo, nspt))


def _atrito_lateral(
    cota: int, leitura: LeituraSPT, tipo: TipoEstaca, perimetro_m: float, f2: float,
) -> CamadaAtrito:
    solo = leitura.solo
    beta = BETA_DQ[tipo][solo.familia]
    nl_dq = _nspt_usado(leitura.nspt, minimo=3)
    nl_av = _nspt_usado(leitura.nspt)
    tensao_dq = beta * 10 * (nl_dq / 3 + 1)
    tensao_av = solo.alfa_av_percentual / 100 * solo.k_av_kpa * nl_av / f2

    # Cada amostra na cota superior representa um metro de fuste.
    return CamadaAtrito(
        amostra=_amostra(cota, leitura),
        cota_base_m=cota - 1,
        decourt_quaresma=AtritoDecourtQuaresma(
            nspt_usado=nl_dq, beta=beta, tensao_kpa=tensao_dq,
            resistencia_kn=tensao_dq * perimetro_m,
        ),
        aoki_velloso=AtritoAokiVelloso(
            nspt_usado=nl_av, k_kpa=solo.k_av_kpa, alfa_percentual=solo.alfa_av_percentual,
            f2=f2, tensao_kpa=tensao_av, resistencia_kn=tensao_av * perimetro_m,
        ),
    )


def _carga_por_metodo(
    rl: float,
    rp_bruta: float,
    fator_redutor: float,
    limite_estrutural_kn: float,
    opcoes: OpcoesCargaAdmissivel,
    *,
    decourt_quaresma: bool,
) -> CargaPorMetodo:
    rp = rp_bruta * fator_redutor
    limita_ponta = opcoes.limita_ponta_por_atrito or opcoes.tratamento_ponta == "contato_com_ressalva"
    ponta_limitada = False
    if opcoes.tratamento_ponta == "sem_contato":
        rp = 0.0
    elif limita_ponta and rp > rl:
        rp = rl
        ponta_limitada = True

    ruptura = rl + rp
    global_kn = ruptura / FS_GLOBAL
    parcial_kn = None
    geotecnica_kn = global_kn
    criterio = "geotecnico_global"
    if decourt_quaresma and opcoes.tratamento_ponta != "sem_contato":
        parcial_kn = rl / FS_LATERAL_DQ + rp / FS_PONTA_DQ
        if parcial_kn <= global_kn:
            geotecnica_kn = parcial_kn
            criterio = "geotecnico_parcial"

    final_kn = min(geotecnica_kn, limite_estrutural_kn)
    if limite_estrutural_kn < geotecnica_kn:
        criterio = "estrutural"

    return CargaPorMetodo(
        resistencia_lateral_kn=rl,
        resistencia_ponta_bruta_kn=rp_bruta,
        resistencia_ponta_kn=rp,
        resistencia_ruptura_kn=ruptura,
        carga_admissivel_global_kn=global_kn,
        carga_admissivel_parcial_kn=parcial_kn,
        carga_admissivel_geotecnica_kn=geotecnica_kn,
        carga_admissivel_geotecnica_tf=geotecnica_kn / KN_POR_TF,
        carga_admissivel_final_kn=final_kn,
        carga_admissivel_final_tf=final_kn / KN_POR_TF,
        criterio_governante=criterio,
        ponta_limitada_por_atrito=ponta_limitada,
    )


def _trechos_sem_spt(
    cota_arrasamento: int, cota_ponta: int, camadas: list[CamadaAtrito],
) -> list[TrechoSemSPT]:
    trechos = []
    topo = cota_arrasamento
    for camada in camadas:
        cota_amostra = camada.amostra.cota_grade_m
        if topo > cota_amostra:
            trechos.append(TrechoSemSPT(cota_topo_m=topo, cota_base_m=cota_amostra))
        topo = camada.cota_base_m
    if topo > cota_ponta:
        trechos.append(TrechoSemSPT(cota_topo_m=topo, cota_base_m=cota_ponta))
    return trechos


def calcular_carga_admissivel(
    estaca: EstacaCalculo,
    leituras: list[LeituraSPT],
    opcoes: OpcoesCargaAdmissivel,
    cota_ponta_m: int | None = None,
) -> tuple[list[CotaPontaResultado], MemorialCargaAdmissivel | None]:
    """Calcula a curva de dois métodos em um furo e detalha a cota solicitada."""
    grade = _compatibilizar_leituras(leituras)
    arrasamento = estaca.cota_arrasamento_grade_m
    if not any(cota < arrasamento for cota in grade):
        raise ErroPerfilCalculo(
            "sem_cota_de_ponta", "A sondagem precisa ter leituras SPT abaixo do arrasamento na grade.",
        )
    if cota_ponta_m is not None and (cota_ponta_m >= arrasamento or cota_ponta_m not in grade):
        raise ErroPerfilCalculo(
            "cota_ponta_indisponivel", "Escolha uma cota de ponta presente na curva calculada.",
        )

    f1 = 2.0
    if estaca.tipo == "pre_moldada_cravada":
        f1 = 1 + estaca.diametro_m / 0.80
    f2 = 2 * f1
    area = estaca.area_ponta_m2
    perimetro = estaca.perimetro_m
    limite_estrutural = estaca.capacidade_estrutural_kn
    fator_redutor = estaca.fator_redutor_ponta(opcoes)

    curva = []
    memorial = None
    camadas: list[CamadaAtrito] = []
    acumulado_dq = acumulado_av = 0.0
    # Somente cotas amostradas são percorridas. O fuste cresce de cima para baixo.
    for cota in sorted((c for c in grade if c <= arrasamento), reverse=True):
        leitura = grade[cota]
        if cota < arrasamento:
            vizinhas = [c for c in (cota + 1, cota, cota - 1) if c in grade]
            nspts = [_nspt_usado(grade[c].nspt) for c in vizinhas]
            np = sum(nspts) // len(nspts)
            solo = leitura.solo
            alfa = 1.0 if estaca.tipo == "pre_moldada_cravada" else ALFA_DQ_MODIFICADO[solo.familia]
            qp_dq = solo.c_dq_kpa * np * alfa
            qp_av = solo.k_av_kpa * np / f1
            rl_dq, rl_av = acumulado_dq, acumulado_av
            desprezar = (
                opcoes.despreza_ultimo_metro_atrito
                and len(camadas) > 1
                and camadas[-1].cota_base_m == cota
            )
            if desprezar:
                rl_dq -= camadas[-1].decourt_quaresma.resistencia_kn
                rl_av -= camadas[-1].aoki_velloso.resistencia_kn

            curva.append(CotaPontaResultado(
                cota_ponta_m=cota,
                comprimento_na_grade_m=arrasamento - cota,
                nspt_ponta=np,
                quantidade_leituras_ponta=len(nspts),
                comprimento_fuste_sem_spt_m=arrasamento - cota - len(camadas),
                ultimo_metro_desprezado=desprezar,
                decourt_quaresma=_carga_por_metodo(
                    rl_dq, qp_dq * area, fator_redutor, limite_estrutural, opcoes,
                    decourt_quaresma=True,
                ),
                aoki_velloso=_carga_por_metodo(
                    rl_av, qp_av * area, fator_redutor, limite_estrutural, opcoes,
                    decourt_quaresma=False,
                ),
            ))
            if cota == cota_ponta_m:
                camadas_memorial = camadas.copy()
                if desprezar:
                    camadas_memorial[-1] = camadas[-1].model_copy(update={"desprezada": True})
                memorial = MemorialCargaAdmissivel(
                    cota_ponta_m=cota,
                    leituras_ponta=[
                        AmostraPonta(**_amostra(c, grade[c]).model_dump(), nspt_usado=n)
                        for c, n in zip(vizinhas, nspts, strict=True)
                    ],
                    camadas_atrito=camadas_memorial,
                    trechos_sem_spt=_trechos_sem_spt(arrasamento, cota, camadas),
                    ponta_decourt_quaresma=PontaDecourtQuaresma(
                        c_kpa=solo.c_dq_kpa, alfa=alfa, tensao_kpa=qp_dq,
                    ),
                    ponta_aoki_velloso=PontaAokiVelloso(k_kpa=solo.k_av_kpa, f1=f1, tensao_kpa=qp_av),
                )

        camada = _atrito_lateral(cota, leitura, estaca.tipo, perimetro, f2)
        camadas.append(camada)
        acumulado_dq += camada.decourt_quaresma.resistencia_kn
        acumulado_av += camada.aoki_velloso.resistencia_kn

    return curva, memorial
