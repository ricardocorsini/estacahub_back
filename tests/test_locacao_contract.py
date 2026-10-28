"""Contrato dos GETs usados pela planta, em banco isolado. Não conecta ao PostgreSQL."""
import os
import unittest
from decimal import Decimal

# Configuração restrita ao processo de testes; nenhuma credencial de produção.
for key, value in {'POSTGRES_USER':'test','POSTGRES_PASSWORD':'test','POSTGRES_DB':'test','JWT_SECRET_KEY':'locacao-contract-test-only-secret-key-000000'}.items():
    os.environ[key] = value

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db, import_models
from app.core.security import criar_token_acesso, settings
from app.models.usuario import Usuario
from app.models.obra import Obra
from app.models.estaca import Estaca
from app.models.sondagem import Sondagem, LeituraSondagem
from app.routers.obras_routers import router as obras
from app.routers.estacas import router as estacas
from app.routers.sondagens import router as sondagens


class LocacaoContractTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool).execution_options(schema_translate_map={'app':None})
        @event.listens_for(self.engine, 'connect')
        def sqlite_functions(connection, _):
            connection.create_function('btrim', 1, lambda s: s.strip(), deterministic=True)
        import_models()
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Usuario(id=1,nome='Usuário teste',email='teste@example.test',senha_hash='test-only'),Usuario(id=2,nome='Outro',email='outro@example.test',senha_hash='test-only')])
        self.db.add_all([Obra(id=1,usuario_id=1,nome='Obra São João',sistema_coordenadas='local'),Obra(id=2,usuario_id=1,nome='Segunda obra',sistema_coordenadas='utm'),Obra(id=3,usuario_id=2,nome='Obra privada',sistema_coordenadas='local')])
        self.db.flush()
        for id_,obra,usuario,x,y in [(11,1,1,0,0),(12,2,1,3,4),(13,3,2,-3,-4)]:
            self.db.add(Estaca(id=id_,obra_id=obra,usuario_id=usuario,nome=f'E-{id_}',coord_x=Decimal(str(x)),coord_y=Decimal(str(y)),tipo='helice_continua',diametro_cm=Decimal('40'),capacidade_estrutural_tf=80,cota_arrasamento=Decimal('-2.123456'),carga_prevista_tf=0))
        self.db.add(Sondagem(id=21,obra_id=1,usuario_id=1,nome='SP-01',coord_x=0,coord_y=None,cota_boca=0,nivel_agua=0,leituras=[LeituraSondagem(id=31,ordem=0,profundidade=0,cota=0,nspt=0,solo='Argila',familia='argila')]))
        self.db.commit()
        self.app=FastAPI()
        for router in [obras,estacas,sondagens]: self.app.include_router(router,prefix='/api')
        def banco_teste(): yield self.db
        self.app.dependency_overrides[get_db]=banco_teste
        self.client=TestClient(self.app)
        self.client.cookies.set(settings.auth_cookie_name,criar_token_acesso(1))
        self.statements=[]
        @event.listens_for(self.engine,'before_cursor_execute')
        def capture(_conn,_cursor,statement,_params,_context,_many): self.statements.append(statement)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def test_gets_arrays_aliases_zero_precision_and_readings(self):
        obra=self.client.get('/api/obras/1')
        self.assertEqual(obra.status_code,200)
        self.assertEqual(obra.json()['sistemaCoordenadas'],'local')
        estacas=self.client.get('/api/obras/1/estacas')
        sondagens=self.client.get('/api/obras/1/sondagens')
        self.assertEqual(estacas.status_code,200);self.assertEqual(sondagens.status_code,200)
        self.assertIsInstance(estacas.json(),list);self.assertIsInstance(sondagens.json(),list)
        e=estacas.json()[0];s=sondagens.json()[0]
        self.assertEqual(e['coordX'],0);self.assertEqual(e['coordY'],0)
        self.assertEqual(e['diametroCm'],40);self.assertEqual(e['cotaArrasamento'],-2.123456);self.assertEqual(e['cargaPrevistaTf'],0)
        self.assertEqual(s['dadosCabecalho']['coordX'],0);self.assertIsNone(s['dadosCabecalho']['coordY'])
        self.assertEqual(s['dadosCabecalho']['nivelAgua'],0);self.assertEqual(s['leituras'][0]['nspt'],0)
        self.assertIn('criadoEm',e);self.assertIn('atualizadoEm',s)
        self.assertFalse(any(sql.lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for sql in self.statements))

    def test_work_and_user_isolation(self):
        self.assertEqual([e['id'] for e in self.client.get('/api/obras/2/estacas').json()],[12])
        for suffix in ['', '/estacas','/sondagens']:
            self.assertEqual(self.client.get('/api/obras/3'+suffix).status_code,404)
            self.assertEqual(self.client.get('/api/obras/999'+suffix).status_code,404)

    def test_session_required_for_all_three_gets(self):
        self.client.cookies.clear()
        for suffix in ['', '/estacas','/sondagens']:
            self.assertEqual(self.client.get('/api/obras/1'+suffix).status_code,401)

if __name__ == '__main__': unittest.main()
