from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.calculos.carga_admissivel import (
    ErroPerfilCalculo, EstacaCalculo, LeituraSPT, calcular_carga_admissivel,
)
from app.calculos.coeficientes_estacas import (
    FS_GLOBAL, FS_LATERAL_DQ, FS_PONTA_DQ, KN_POR_TF, SOLOS, chave_solo,
)
from app.models.estaca import Estaca
from app.models.obra import Obra
from app.models.sondagem import LeituraSondagem, Sondagem
from app.schemas.carga_admissivel import CargaAdmissivelRequest, CargaAdmissivelResponse


# A tela de sondagens salva a cota derivada com duas casas decimais.
TOLERANCIA_COTA_M = Decimal("0.005")


def _cota_da_leitura(leitura: LeituraSondagem, cota_boca: Decimal) -> Decimal:
    cota, profundidade = leitura.cota, leitura.profundidade
    if any(valor is not None and not valor.is_finite() for valor in (cota, profundidade)):
        raise ErroPerfilCalculo("leitura_sem_cota_valida", f"Revise a cota e a profundidade da leitura {leitura.id}.")
    if profundidade is not None:
        cota_calculada = cota_boca - profundidade
        if cota is not None and abs(cota - cota_calculada) > TOLERANCIA_COTA_M:
            raise ErroPerfilCalculo(
                "cota_leitura_inconsistente",
                f"A cota informada na leitura {leitura.id} difere da cota de boca menos a profundidade.",
            )
        return cota_calculada
    if cota is None:
        raise ErroPerfilCalculo(
            "leitura_sem_cota_valida", f"Informe a profundidade ou a cota da leitura {leitura.id}.",
        )
    return cota


def _leituras_para_calculo(sondagem: Sondagem, cota_boca: Decimal) -> list[LeituraSPT]:
    profundidade_final = sondagem.profundidade_final
    if profundidade_final is not None and not profundidade_final.is_finite():
        raise ErroPerfilCalculo("profundidade_final_invalida", "Revise a profundidade final da sondagem.")
    leituras = []
    for leitura in sondagem.leituras:
        if leitura.nspt is None:
            continue
        cota = _cota_da_leitura(leitura, cota_boca)
        profundidade = cota_boca - cota
        if profundidade < 0 or (profundidade_final is not None and profundidade > profundidade_final):
            raise ErroPerfilCalculo(
                "leitura_fora_da_sondagem",
                f"A leitura {leitura.id} está fora do intervalo entre a boca e a profundidade final da sondagem.",
            )
        solo = SOLOS.get(chave_solo(leitura.solo or ""))
        if solo is None:
            raise ErroPerfilCalculo(
                "solo_invalido", f"Selecione um tipo de solo disponível no cadastro para a leitura {leitura.id}.",
            )
        leituras.append(LeituraSPT(id=leitura.id, cota_m=cota, nspt=leitura.nspt, solo=solo))
    if not leituras:
        raise ErroPerfilCalculo("sem_leituras_spt", "A sondagem selecionada precisa ter leituras com NSPT.")
    return leituras


def calcular_carga_admissivel_service(
    db: Session,
    obra_id: int,
    estaca_id: int,
    usuario_id: int,
    payload: CargaAdmissivelRequest,
) -> CargaAdmissivelResponse:
    # Uma instrução lê estaca, cabeçalho e leituras no mesmo snapshot do banco.
    consulta = (
        select(Estaca, Sondagem)
        .join(Obra, Obra.id == Estaca.obra_id)
        .outerjoin(Sondagem, (
            (Sondagem.obra_id == Obra.id)
            & (Sondagem.usuario_id == Obra.usuario_id)
            & (Sondagem.id == payload.sondagem_id)
        ))
        .options(joinedload(Sondagem.leituras))
        .where(
            Obra.id == obra_id,
            Obra.usuario_id == usuario_id,
            Estaca.id == estaca_id,
            Estaca.usuario_id == usuario_id,
        )
    )
    dados = db.execute(consulta).unique().one_or_none()
    if dados is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estaca não encontrada nesta obra.")
    estaca, sondagem = dados
    if sondagem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sondagem não encontrada nesta obra.")

    geometria = EstacaCalculo(
        tipo=estaca.tipo,
        diametro_m=float(estaca.diametro_cm / 100),
        cota_arrasamento_m=estaca.cota_arrasamento,
        capacidade_estrutural_tf=float(estaca.capacidade_estrutural_tf),
    )
    opcoes = payload.opcoes
    cota_boca = sondagem.cota_boca
    try:
        if cota_boca is None or not cota_boca.is_finite():
            raise ErroPerfilCalculo("cota_boca_invalida", "Informe a cota de boca da sondagem.")
        leituras = _leituras_para_calculo(sondagem, cota_boca)
        curva, memorial = calcular_carga_admissivel(geometria, leituras, opcoes, payload.cota_ponta_m)
    except ErroPerfilCalculo as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"codigo": exc.codigo, "mensagem": str(exc)},
        ) from exc

    avisos = []
    if estaca.tipo in ("helice_continua", "escavada_fluido") and opcoes.tratamento_ponta != "sem_contato":
        avisos.append("verificar_contato_ponta")
    return CargaAdmissivelResponse(
        obra_id=obra_id,
        estaca_id=estaca.id,
        sondagem_id=sondagem.id,
        nome_estaca=estaca.nome,
        nome_sondagem=sondagem.nome,
        tipo_estaca=geometria.tipo,
        diametro_cm=float(estaca.diametro_cm),
        cota_boca_m=float(cota_boca),
        cota_arrasamento_m=float(geometria.cota_arrasamento_m),
        cota_arrasamento_grade_m=geometria.cota_arrasamento_grade_m,
        area_ponta_m2=geometria.area_ponta_m2,
        perimetro_m=geometria.perimetro_m,
        capacidade_estrutural_tf=geometria.capacidade_estrutural_tf,
        capacidade_estrutural_kn=geometria.capacidade_estrutural_kn,
        carga_prevista_tf=float(estaca.carga_prevista_tf),
        kn_por_tf=KN_POR_TF,
        fs_global=FS_GLOBAL,
        fs_lateral_decourt_quaresma=FS_LATERAL_DQ,
        fs_ponta_decourt_quaresma=FS_PONTA_DQ,
        fator_redutor_ponta=geometria.fator_redutor_ponta(opcoes),
        opcoes=opcoes,
        avisos=avisos,
        curva=curva,
        memorial=memorial,
    )
