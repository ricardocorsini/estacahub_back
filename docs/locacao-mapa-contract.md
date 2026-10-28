# Contrato de leitura — Locação / mapa

A tela `/obras/:obraId/locacao-mapa` e o gerador DXF consomem exclusivamente os GETs existentes:

| Consulta | Resposta | Autorização |
| --- | --- | --- |
| `/api/obras/{obraId}` | `ObraResponse` | `_obter_obra_ou_404`, obra e usuário |
| `/api/obras/{obraId}/estacas` | Array direto de `EstacaResponse` | `_garantir_acesso`, consulta por obra e usuário |
| `/api/obras/{obraId}/sondagens` | Array direto de `SondagemResponse`, com todas as leituras | `_garantir_obra_pertence_ao_usuario`, consulta por obra e usuário, `selectinload` |

Os três usam `CurrentUser` e a sessão existente. IDs fora do escopo retornam 404. Sessão ausente/expirada retorna 401. Não foi criado endpoint de exportação, tabela, migração, persistência de desenho, upload ou escrita para a nova funcionalidade.

## Campos e unidades

- Estacas: aliases camelCase de coordenadas e atributos, incluindo `obraId`, `diametroCm`, `capacidadeEstruturalTf`, `cotaArrasamento`, `cargaPrevistaTf`, `criadoEm` e `atualizadoEm`.
- Sondagens: `dadosCabecalho` com `coordX`, `coordY`, `cotaBoca`, `profundidadeFinal`, `criterio`, `nivelAgua`; `leituras` com profundidade, cota, nspt, solo, familia e ID; datas de criação/atualização.
- Obra: nome, número, localização, dataCadastro, sistemaCoordenadas local/utm, responsável, observações, legenda e datas. `fotoUrl` atual é metadado/URL fictícia; o fluxo não fornece os bytes da foto e o DXF não a incorpora.
- A interface atual usa coordenadas/cotas em m, diâmetro em cm e cargas em tf. Estacas persistem números com seis casas; sondagens com três casas. O frontend preserva os números retornados, sem inventar precisão anterior ao banco.
- X/Y nulos ou incompletos de sondagem são válidos no cadastro, mas não formam posição. Zero, inclusive NA e NSPT zero, permanece zero.
- Capacidade estrutural é valor cadastrado. Não há cálculo de carga admissível neste fluxo.
- O cadastro informa somente local/utm, sem fuso, hemisfério, datum ou EPSG. Não suporta georreferenciamento ou norte geográfico deduzidos.

## Testes de regressão adicionados

`tests/test_locacao_contract.py` monta os routers reais em FastAPI, usa cookies JWT reais de teste e substitui somente `get_db` por uma sessão SQLite em memória. Não importa/inicia o lifespan de produção e não se conecta ao PostgreSQL. A função `btrim` é registrada apenas nesse banco isolado para as constraints/índices existentes.

Os testes verificam os arrays e aliases, leituras, ausências, valores zero, precisão de seis casas, isolamento entre obras do mesmo usuário e entre usuários, 404 de obra inexistente, 401 sem sessão e ausência de INSERT/UPDATE/DELETE durante as três consultas. O teste não substitui uma validação do PostgreSQL de produção.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

Resultado em 28/10/2026: **3 testes aprovados** e compilação Python aprovada, com os requisitos de produção instalados em ambiente isolado. A versão atual de Starlette emite aviso de depreciação para o TestClient com httpx; os testes passam. `requirements-dev.txt` adiciona apenas a dependência de cliente HTTP dos testes; `requirements.txt` e os módulos de produção não mudam.

A implementação, decisões de geometria, layers, DXF, testes de navegador e evidências visuais estão em [`estacahub_front/docs/locacao-mapa-dxf.md`](https://github.com/ricardocorsini/estacahub_front/blob/master/docs/locacao-mapa-dxf.md).
