# Carga admissível de estacas

`POST /api/obras/{obra_id}/estacas/{estaca_id}/carga-admissivel`

A rota exige a sessão da API e usa uma estaca e uma sondagem da mesma obra do
usuário. O cálculo usa as tabelas atuais de estacas, sondagens e leituras. A
consulta é executada sob demanda, sem necessidade de SQL no DBeaver.

Envie `{"sondagemId": 21}` para calcular a curva. Para obter o memorial, envie
também uma `cotaPontaM` inteira que conste na curva.

```json
{
  "sondagemId": 21,
  "cotaPontaM": -8,
  "opcoes": {
    "desprezaUltimoMetroAtrito": true,
    "aplicaRedutorPonta": false,
    "tratamentoPonta": "calculado",
    "limitaPontaPorAtrito": false
  }
}
```

As opções exibidas são os padrões. `tratamentoPonta` admite `calculado`,
`contato_com_ressalva` (limita a ponta ao atrito lateral) e `sem_contato`
(zera a resistência de ponta). Para hélice contínua e escavada com fluido,
`verificar_contato_ponta` sinaliza a necessidade de verificar a hipótese
executiva ao considerar a ponta. [ABNT NBR 6122:2022, item 8.2.1.2](https://pt.scribd.com/document/786130232/NBR-6122-2022-Projeto-e-eExecucao-de-fundacoes).

## Resposta para a tela

- `curva` ordena as cotas de ponta da mais alta à mais baixa. Cada ponto
  traz a parcela lateral, a ponta bruta e a considerada, a ruptura e as cargas
  admissíveis de `decourtQuaresma` e `aokiVelloso`. Use
  `cargaAdmissivelFinalTf` ou `cargaAdmissivelFinalKn` para plotar com
  `cotaPontaM`. O limite estrutural da estaca é aplicado separadamente a
  cada método. `cargaPrevistaTf` vem do cadastro para a comparação na tela.
- `memorial` detalha uma cota, com leituras de ponta, coeficientes, NSPT
  medido e adotado, atrito por metro, camada desprezada e trechos sem
  SPT. O valor é `null` quando o corpo omite `cotaPontaM`.
- `cotaArrasamentoM` representa a cota cadastrada e
  `cotaArrasamentoGradeM` representa a cota inteira usada no cálculo.
  `comprimentoNaGradeM` mede o trecho entre o arrasamento da grade e a ponta.
  `quantidadeLeiturasPonta` evidencia janelas incompletas, e
  `comprimentoFusteSemSptM` indica o comprimento sem contribuição por falta
  de leitura. A ponta é avaliada nas cotas da grade com leitura representativa.
  Uma leitura exatamente a 0,50 m de duas cotas pode representar ambas na grade.

A rota devolve `401` para sessão ausente e `404` quando a obra, estaca ou
sondagem não está acessível. Perfis ou cotas indisponíveis devolvem `422` com
`detail.codigo` e `detail.mensagem`. O OpenAPI em `/docs` detalha os campos.

## Critérios de cálculo

- Seção circular conforme o diâmetro cadastrado. O arrasamento é arredondado
  para baixo. A grade usa a leitura mais próxima em até 0,50 m e, em caso
  de empate, a ordem de cadastro. A cota de boca menos a profundidade
  define a cota da leitura. A cota explícita é aceita quando a profundidade
  está ausente e a cota de boca está preenchida. Se ambos os valores da leitura
  estiverem cadastrados, a tolerância de consistência é de 0,005 m para
  acomodar o arredondamento da tela de sondagens. Leituras com NSPT informado
  devem estar entre a boca e a profundidade final, quando cadastrada. Linhas
  com NSPT vazio ficam fora da grade.
- O atrito é integrado no fuste em trechos de 1 m a partir do NSPT do
  topo de cada trecho. Adota-se NSPT de 3 a 50 no Décourt–Quaresma e de 1 a
  50 no Aoki–Velloso. Por padrão, o último metro é desprezado se houver
  uma leitura para esse trecho e pelo menos outro metro com leitura.
- Os dois métodos adotam o critério de ponta do GEOSPT-STRUCT. O NSPT da
  ponta é a média, arredondada para baixo, das leituras disponíveis na
  cota avaliada e nas duas vizinhas imediatas. Cada leitura usada na média
  é limitada ao intervalo de 1 a 50. O Décourt–Quaresma usa o alfa
  modificado do GEOSPT-STRUCT para hélice contínua. O Aoki–Velloso aplica
  alfa como percentual na parcela lateral.
- A carga geotécnica do Décourt–Quaresma é o menor valor entre o cálculo
  global com FS 2 e o cálculo por parcelas com FS 1,30 para o atrito e 4
  para a ponta. Em `sem_contato`, vale o cálculo global com ponta zerada.
  O Aoki–Velloso usa FS global 2. Em ambos, a carga admissível final
  considera também o limite estrutural cadastrado, com 1 tf = 9,80665 kN.

As regras acima reproduzem a variante semiempírica do GEOSPT-STRUCT para um
furo, com os coeficientes da revisão vinculada. Os resultados estimam a
capacidade axial à compressão. A adoção em projeto requer verificar as
hipóteses executivas e os critérios de serviço.
[Motor de referência](https://github.com/itanervale/GEOSPT-STRUCT/blob/5f5cded75e94dbce2bea90eb685deef74d1dfd1f/src/engine/geospt-engine.js) ·
[Formulações publicadas, ABMS Norte](https://www.abms.com.br/livros/arquivos/ABMS%20Norte%20%202023%20Livro%20Eng%20Geotec%20286p.pdf) ·
[Histórico do método de Décourt, SEFE 2023](https://www.fecfau.unicamp.br/~pjra/wp-content/uploads/2024/01/Me%CC%81todo-de-De%CC%81court_SEFE-2023_Polido-et-al..pdf).
