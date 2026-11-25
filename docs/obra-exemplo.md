# Obra de referência de Balsas

O endpoint autenticado `POST /api/obras/exemplos/balsas` devolve uma obra no mesmo formato de `GET /api/obras/{id}`. A primeira abertura grava a obra, quatro estacas, cinco sondagens e suas 79 leituras em uma transação. Chamadas seguintes recuperam a mesma obra mesmo que tenha sido renomeada. Excluir a obra no cadastro permite carregar novamente o exemplo original.

## Dados de origem

O GEOSPT-STRUCT fornece os perfis SPT de Balsas/MA, com cotas de boca absolutas e coordenadas locais inferidas para a demonstração. As profundidades finais e o critério de paralisação são mantidos separadamente da última leitura medida. O nível d’água é nulo nos cinco furos. As cotas das leituras são a diferença entre a cota de boca e a profundidade, com a precisão de três casas do banco. [Sondagens na revisão de origem](https://github.com/itanervale/GEOSPT-STRUCT/blob/5f5cded75e94dbce2bea90eb685deef74d1dfd1f/src/engine/dataset-balsas.js)

As quatro estacas vêm do comando Balsas (demo). As cargas estruturais efetivas foram obtidas com a função do GEOSPT para a seção circular de cada estaca e arredondadas para a precisão do cadastro. A carga prevista é preservada inclusive quando excede a capacidade estrutural. Os resultados são calculados pelo motor do EstacaHub ao solicitar uma análise. A tabela de compatibilização do GEOSPT é um gabarito de validação de múltiplos furos e fica fora dos cadastros por sondagem. [Estacas de origem](https://github.com/itanervale/GEOSPT-STRUCT/blob/5f5cded75e94dbce2bea90eb685deef74d1dfd1f/src/layout/Header.jsx) · [Cargas efetivas](https://github.com/itanervale/GEOSPT-STRUCT/blob/5f5cded75e94dbce2bea90eb685deef74d1dfd1f/src/domain/estacas.js)

| Estaca | Tipo | Diâmetro (cm) | Arrasamento (m) | Carga prevista (tf) | Capacidade estrutural (tf) |
| --- | --- | ---: | ---: | ---: | ---: |
| E-01 | Hélice contínua | 40 | 253 | 50 | 80 |
| E-02 | Hélice contínua | 40 | 250 | 40 | 80 |
| E-03 | Raiz | 30 | 250 | 110 | 86,495390 |
| E-04 | Pré-moldada cravada | 30 | 257 | 45 | 79,287441 |

O startup habitual da API cria a tabela de vínculos com `init_db()`. Para ambientes com DDL aplicado manualmente, execute o [SQL de criação](sql/obras_exemplo.sql) antes de publicar a nova versão da API.
