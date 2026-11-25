import os
import unittest
from unittest.mock import patch

for chave, valor in {
    "POSTGRES_USER": "test", "POSTGRES_PASSWORD": "test", "POSTGRES_DB": "test",
    "JWT_SECRET_KEY": "obra-exemplo-test-only-secret-key-000000",
}.items():
    os.environ.setdefault(chave, valor)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db, import_models
from app.core.security import criar_token_acesso, settings
from app.main import app
from app.models.usuario import Usuario


class ObraExemploTest(unittest.TestCase):
    rota = "/api/obras/exemplos/balsas"

    def setUp(self):
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        engine = engine.execution_options(schema_translate_map={"app": None})
        self.addCleanup(engine.dispose)

        @event.listens_for(engine, "connect")
        def preparar_sqlite(conexao, _):
            conexao.create_function("btrim", 1, str.strip, deterministic=True)
            conexao.execute("PRAGMA foreign_keys=ON")

        @event.listens_for(engine, "before_cursor_execute", retval=True)
        def ids_autoincrementais(_conn, _cursor, sql, params, _contexto, _muitos):
            if sql.lstrip().startswith("CREATE TABLE"):
                sql = sql.replace("BIGINT", "INTEGER")
            return sql, params

        import_models()
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add_all([Usuario(id=i, nome=f"Conta {i}", email=f"{i}@example.com", senha_hash="teste") for i in (1, 2)])
            db.commit()

        def sessao():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = sessao
        self.addCleanup(app.dependency_overrides.pop, get_db)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def entrar(self, usuario_id):
        self.client.cookies.set(settings.auth_cookie_name, criar_token_acesso(usuario_id))

    def abrir(self):
        resposta = self.client.post(self.rota)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        return resposta.json()["id"]

    def test_cadastros_e_vinte_pares_calculaveis(self):
        self.entrar(1)
        base = f"/api/obras/{self.abrir()}"
        sondagens = self.client.get(base + "/sondagens").json()
        estacas = self.client.get(base + "/estacas").json()
        self.assertEqual([len(s["leituras"]) for s in sondagens], [19, 18, 14, 14, 14])
        self.assertEqual(sondagens[0]["leituras"][0]["cota"], 253.485)
        self.assertEqual([e["capacidadeEstruturalTf"] for e in estacas], [80, 80, 86.49539, 79.287441])
        for e in estacas:
            for s in sondagens:
                resposta = self.client.post(base + f"/estacas/{e['id']}/carga-admissivel", json={"sondagemId": s["id"]})
                self.assertEqual(resposta.status_code, 200, resposta.text)
                self.assertTrue(resposta.json()["curva"])

    def test_copia_privada_persiste_edicoes_e_pode_ser_recriada(self):
        self.assertEqual(self.client.post(self.rota).status_code, 401)
        self.entrar(1)
        id1 = self.abrir()
        self.assertEqual(self.client.patch(f"/api/obras/{id1}", json={"nome": "Minha cópia"}).status_code, 200)
        reaberta = self.client.post(self.rota).json()
        self.assertEqual((reaberta["id"], reaberta["nome"]), (id1, "Minha cópia"))
        self.entrar(2)
        self.assertNotEqual(self.abrir(), id1)
        self.assertEqual(self.client.get(f"/api/obras/{id1}").status_code, 404)
        self.entrar(1)
        self.assertEqual(self.client.delete(f"/api/obras/{id1}").status_code, 200)
        self.assertEqual(self.client.post(self.rota).json()["nome"], "Obra de Referência — Balsas")

    def test_falha_reverte_obra_e_permite_nova_tentativa(self):
        self.entrar(1)
        with patch("app.services.obra_exemplo_service.aplicar_payload_sondagem", side_effect=SQLAlchemyError("teste")):
            self.assertEqual(self.client.post(self.rota).status_code, 500)
        self.assertEqual(self.client.get("/api/obras").json(), [])
        self.abrir()
