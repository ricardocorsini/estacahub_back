import unittest
from decimal import Decimal
from math import pi

from app.calculos.carga_admissivel import (
    ErroPerfilCalculo, EstacaCalculo, LeituraSPT, calcular_carga_admissivel,
)
from app.calculos.coeficientes_estacas import SOLOS
from app.schemas.carga_admissivel import OpcoesCargaAdmissivel


class MotorCargaAdmissivelTest(unittest.TestCase):
    def setUp(self):
        self.estaca = EstacaCalculo("helice_continua", 0.40, Decimal("0.75"), 100)
        self.leituras = [
            LeituraSPT(1, Decimal("0"), 0, SOLOS["argila"]),
            LeituraSPT(2, Decimal("-1"), 12, SOLOS["silte arenoso"]),
            LeituraSPT(3, Decimal("-2"), 18, SOLOS["areia"]),
            LeituraSPT(4, Decimal("-3"), 62, SOLOS["argila"]),
        ]

    def test_formulas_admissiveis_e_memorial_por_cota(self):
        curva, memorial = calcular_carga_admissivel(
            self.estaca, self.leituras, OpcoesCargaAdmissivel(), cota_ponta_m=-2,
        )
        self.assertEqual([p.cota_ponta_m for p in curva], [-1, -2, -3])
        self.assertFalse(curva[0].ultimo_metro_desprezado)
        self.assertTrue(curva[1].ultimo_metro_desprezado)
        self.assertEqual(curva[1].nspt_ponta, 26)
        self.assertEqual(curva[2].quantidade_leituras_ponta, 2)

        area, perimetro = pi * 0.40**2 / 4, pi * 0.40
        dq = curva[1].decourt_quaresma
        self.assertAlmostEqual(dq.resistencia_lateral_kn, 20 * perimetro)
        self.assertAlmostEqual(dq.resistencia_ponta_kn, 400 * 26 * 0.50 * area)
        self.assertAlmostEqual(dq.carga_admissivel_final_kn, 20 * perimetro / 1.3 + 5200 * area / 4)
        self.assertEqual(dq.criterio_governante, "geotecnico_parcial")
        av = curva[1].aoki_velloso
        self.assertAlmostEqual(av.resistencia_lateral_kn, 3 * perimetro)
        self.assertAlmostEqual(av.resistencia_ponta_kn, 1000 * 26 / 2 * area)
        self.assertAlmostEqual(av.carga_admissivel_final_tf, (3 * perimetro + 13000 * area) / 2 / 9.80665)
        self.assertIsNone(av.carga_admissivel_parcial_kn)

        self.assertIsNotNone(memorial)
        self.assertEqual([l.nspt_medido for l in memorial.leituras_ponta], [12, 18, 62])
        self.assertEqual([l.nspt_usado for l in memorial.leituras_ponta], [12, 18, 50])
        self.assertEqual([c.desprezada for c in memorial.camadas_atrito], [False, True])
        camada = memorial.camadas_atrito[0]
        self.assertEqual(camada.amostra.nspt_medido, 0)
        self.assertEqual(camada.decourt_quaresma.nspt_usado, 3)
        self.assertEqual(camada.aoki_velloso.nspt_usado, 1)

    def test_tratamentos_da_ponta_e_limite_estrutural(self):
        for opcoes in (
            OpcoesCargaAdmissivel(tratamento_ponta="contato_com_ressalva", aplica_redutor_ponta=True),
            OpcoesCargaAdmissivel(limita_ponta_por_atrito=True),
        ):
            with self.subTest(opcoes=opcoes):
                curva, _ = calcular_carga_admissivel(self.estaca, self.leituras, opcoes)
                for resultado in (curva[1].decourt_quaresma, curva[1].aoki_velloso):
                    self.assertEqual(resultado.resistencia_ponta_kn, resultado.resistencia_lateral_kn)
                    self.assertTrue(resultado.ponta_limitada_por_atrito)
                    self.assertAlmostEqual(resultado.carga_admissivel_final_kn, resultado.resistencia_lateral_kn)
                    self.assertEqual(resultado.criterio_governante, "geotecnico_global")

        sem_contato = OpcoesCargaAdmissivel(tratamento_ponta="sem_contato")
        curva, _ = calcular_carga_admissivel(self.estaca, self.leituras, sem_contato)
        dq = curva[1].decourt_quaresma
        self.assertEqual(dq.resistencia_ponta_kn, 0)
        self.assertIsNone(dq.carga_admissivel_parcial_kn)
        self.assertEqual(dq.carga_admissivel_final_kn, dq.resistencia_lateral_kn / 2)
        self.assertEqual(dq.criterio_governante, "geotecnico_global")

        estaca = EstacaCalculo("pre_moldada_cravada", 0.40, Decimal("0.75"), 4)
        opcoes = OpcoesCargaAdmissivel(despreza_ultimo_metro_atrito=False)
        curva, memorial = calcular_carga_admissivel(estaca, self.leituras, opcoes, cota_ponta_m=-2)
        self.assertFalse(curva[1].ultimo_metro_desprezado)
        self.assertEqual(memorial.ponta_aoki_velloso.f1, 1.5)
        self.assertEqual(memorial.camadas_atrito[1].aoki_velloso.f2, 3)
        self.assertEqual(memorial.ponta_decourt_quaresma.alfa, 1)
        for resultado in (curva[1].decourt_quaresma, curva[1].aoki_velloso):
            self.assertEqual(resultado.criterio_governante, "estrutural")
            self.assertEqual(resultado.carga_admissivel_final_tf, 4)

    def test_redutor_da_ponta_isolado(self):
        curva, _ = calcular_carga_admissivel(
            self.estaca, self.leituras, OpcoesCargaAdmissivel(aplica_redutor_ponta=True),
        )
        for resultado in (curva[1].decourt_quaresma, curva[1].aoki_velloso):
            self.assertAlmostEqual(resultado.resistencia_ponta_kn, resultado.resistencia_ponta_bruta_kn / 2)

    def test_cotas_negativas_empates_na_grade_e_fuste_sem_spt(self):
        estaca = EstacaCalculo("raiz", 0.30, Decimal("-0.1"), 70)
        leituras = [
            LeituraSPT(1, Decimal("-1.50"), 4, SOLOS["argila"]),
            LeituraSPT(2, Decimal("-2.50"), 16, SOLOS["silte"]),
            LeituraSPT(3, Decimal("-900000000.25"), 30, SOLOS["areia"]),
        ]
        curva, memorial = calcular_carga_admissivel(
            estaca, leituras, OpcoesCargaAdmissivel(), cota_ponta_m=-900000000,
        )
        self.assertEqual([p.cota_ponta_m for p in curva], [-2, -3, -900000000])
        self.assertAlmostEqual(curva[0].nspt_ponta, 8)
        self.assertEqual(curva[-1].quantidade_leituras_ponta, 1)
        self.assertEqual(curva[-1].comprimento_fuste_sem_spt_m, 899999996)
        self.assertFalse(curva[-1].ultimo_metro_desprezado)
        self.assertEqual([c.amostra.leitura_id for c in memorial.camadas_atrito], [1, 1, 2])
        self.assertEqual(
            [(t.cota_topo_m, t.cota_base_m) for t in memorial.trechos_sem_spt],
            [(-4, -900000000)],
        )
        with self.assertRaises(ErroPerfilCalculo) as falha:
            calcular_carga_admissivel(estaca, leituras, OpcoesCargaAdmissivel(), cota_ponta_m=-4)
        self.assertEqual(falha.exception.codigo, "cota_ponta_indisponivel")

    def test_perfil_sem_cota_de_ponta_retorna_erro_explicito(self):
        with self.assertRaises(ErroPerfilCalculo) as falha:
            calcular_carga_admissivel(self.estaca, self.leituras[:1], OpcoesCargaAdmissivel())
        self.assertEqual(falha.exception.codigo, "sem_cota_de_ponta")
