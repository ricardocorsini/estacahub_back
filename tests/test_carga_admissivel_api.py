import os
import unittest
from decimal import Decimal

for chave, valor in {
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_DB": "test",
    "JWT_SECRET_KEY": "carga-admissivel-test-only-secret-key-000000",
}.items():
    os.environ.setdefault(chave, valor)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db, import_models
from app.core.security import criar_token_acesso, settings
from app.main import app
from app.models.estaca import Estaca
from app.models.obra import Obra
from app.models.sondagem import LeituraSondagem, Sondagem
from app.models.usuario import Usuario


class CargaAdmissivelApiTest(unittest.TestCase):
    rota = "/api/obras/1/estacas/11/carga-admissivel"

    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        ).execution_options(schema_translate_map={"app": None})
        self.addCleanup(engine.dispose)

        @event.listens_for(engine, "connect")
        def registrar_btrim(conexao, _):
            conexao.create_function("btrim", 1, str.strip, deterministic=True)

        import_models()
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        self.db.add_all([
            Usuario(id=1, nome="Usuário Um", email="um@example.test", senha_hash="teste"),
            Usuario(id=2, nome="Usuário Dois", email="dois@example.test", senha_hash="teste"),
            Obra(id=1, usuario_id=1, nome="Obra Um", sistema_coordenadas="local"),
            Obra(id=2, usuario_id=1, nome="Obra Dois", sistema_coordenadas="local"),
            Obra(id=3, usuario_id=2, nome="Obra Três", sistema_coordenadas="local"),
            Estaca(
                id=11, obra_id=1, usuario_id=1, nome="E-01", coord_x=0, coord_y=0,
                tipo="helice_continua", diametro_cm=40, capacidade_estrutural_tf=60,
                cota_arrasamento=Decimal("10.75"), carga_prevista_tf=25,
            ),
            Sondagem(
                id=21, obra_id=1, usuario_id=1, nome="SP-01", cota_boca=Decimal("10.495"),
                profundidade_final=6,
                leituras=[
                    LeituraSondagem(id=31, ordem=0, profundidade=1, cota=9.50, nspt=0, solo="Argila"),
                    LeituraSondagem(id=32, ordem=1, cota=8.49, nspt=10, solo="Silte"),
                    LeituraSondagem(id=33, ordem=2, profundidade=3, nspt=20, solo="Areia Silto–argilosa"),
                    LeituraSondagem(id=34, ordem=3, profundidade=4, solo="Areia"),
                ],
            ),
            Sondagem(id=22, obra_id=2, usuario_id=1, nome="SP-02"),
            Sondagem(id=23, obra_id=3, usuario_id=2, nome="SP-03"),
        ])
        self.db.commit()

        def banco_teste():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = banco_teste
        self.addCleanup(app.dependency_overrides.pop, get_db)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.client.cookies.set(settings.auth_cookie_name, criar_token_acesso(1))
        self.consultas = []

        @event.listens_for(engine, "before_cursor_execute")
        def capturar_consulta(_conexao, _cursor, consulta, _params, _contexto, _muitas):
            self.consultas.append(consulta)

    def test_curva_com_leituras_cadastradas_e_memorial_opcional(self):
        resposta = self.client.post(self.rota, json={"sondagemId": 21})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        dados = resposta.json()
        self.assertEqual(dados["cotaArrasamentoM"], 10.75)
        self.assertEqual(dados["cotaArrasamentoGradeM"], 10)
        self.assertEqual(dados["capacidadeEstruturalTf"], 60)
        self.assertEqual(dados["cargaPrevistaTf"], 25)
        self.assertEqual(dados["avisos"], ["verificar_contato_ponta"])
        self.assertEqual([c["cotaPontaM"] for c in dados["curva"]], [9, 8, 7])
        self.assertIsNone(dados["memorial"])

        resposta = self.client.post(self.rota, json={"sondagemId": 21, "cotaPontaM": 8})
        self.assertEqual(resposta.status_code, 200, resposta.text)
        detalhe = resposta.json()
        self.assertEqual(detalhe["curva"], dados["curva"])
        memorial = detalhe["memorial"]
        self.assertEqual(memorial["trechosSemSpt"], [{"cotaTopoM": 10, "cotaBaseM": 9}])
        self.assertEqual([l["nsptUsado"] for l in memorial["leiturasPonta"]], [1, 10, 20])
        self.assertEqual(memorial["leiturasPonta"][0]["cotaLeituraM"], 9.495)
        self.assertEqual(memorial["leiturasPonta"][-1]["familia"], "Granular")
        self.assertTrue(all(sql.lstrip().upper().startswith("SELECT") for sql in self.consultas))

    def test_exige_sessao_e_isola_estaca_e_sondagem_por_obra_e_usuario(self):
        for sondagem_id in (22, 23, 999):
            resposta = self.client.post(self.rota, json={"sondagemId": sondagem_id})
            self.assertEqual(resposta.status_code, 404)
        resposta = self.client.post(self.rota.replace("/obras/1/", "/obras/2/"), json={"sondagemId": 22})
        self.assertEqual(resposta.status_code, 404)

        self.client.cookies.set(settings.auth_cookie_name, criar_token_acesso(2))
        self.assertEqual(self.client.post(self.rota, json={"sondagemId": 21}).status_code, 404)
        self.client.cookies.clear()
        self.assertEqual(self.client.post(self.rota, json={"sondagemId": 21}).status_code, 401)

    def test_erros_de_entrada_e_perfil(self):
        for payload in (
            {"sondagemId": 0},
            {"sondagemId": 21, "cotaPontaM": 8.5},
            {"sondagemId": 21, "opcoes": {"tratamentoPonta": "qualquer"}},
            {"sondagemId": 21, "opcoes": {"aplicaRedutorPonta": "sim"}},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(self.rota, json=payload).status_code, 422)

        resposta = self.client.post(self.rota, json={"sondagemId": 21, "cotaPontaM": 6})
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["detail"]["codigo"], "cota_ponta_indisponivel")

        leitura = self.db.get(LeituraSondagem, 31)
        leitura.cota = Decimal("9.7")
        self.db.commit()
        resposta = self.client.post(self.rota, json={"sondagemId": 21})
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["detail"]["codigo"], "cota_leitura_inconsistente")

        leitura.cota = None
        leitura.solo = "Rocha"
        self.db.commit()
        resposta = self.client.post(self.rota, json={"sondagemId": 21})
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["detail"]["codigo"], "solo_invalido")
