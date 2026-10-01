# Friedrich-Wilhelm-Murnau-Stiftung — sondagem e desenho de coleta

**Fila europeia:** cabeça operacional, antigo rank 7.  
**Estado:** engenharia de coletor; promoção a corpus ativo condicionada à execução real.

## Evidência pública

A Murnau-Stiftung mantém uma `Filmsuche` pública e um endpoint `/movie_search` com filtros por título, diretor, ator, ano e gênero. Resultados apontam para fichas persistentes `/movie/<id>`.

A instituição informa um acervo próprio superior a **6.000 filmes** silenciosos e sonoros — ficção, documentário, curta e publicidade — dos anos 1890 ao início dos anos 1960. Informa separadamente um estoque fiduciário de aproximadamente 20.000 títulos. O corpus MAR não deve confundir essas duas populações.

## Estratégia de enumeração

Para reduzir arbitrariedade de amostragem, o coletor consulta de forma determinística cada ano de **1890 a 1969**:

`/movie_search?year=AAAA`

Cada resultado `/movie/<id>` é deduplicado por ID. A soma das contagens declaradas por partição é registrada e comparada ao número de links efetivamente extraídos. Até 30 fichas, escolhidas deterministicamente pelos menores IDs, são abertas apenas para enriquecer metadados.

A estratégia:
- não baixa filmes;
- não presume que ficha pública significa filme disponível online;
- não representa o estoque fiduciário de 20.000 títulos como corpus;
- não afirma completude física da coleção;
- permite medir a cobertura da própria superfície pública por partições anuais.

## Gate de incorporação

A promoção a `CORPORA` ativo exige execução real no CI demonstrando:
1. política de robots verificável e permissiva para as rotas usadas;
2. resultados não vazios;
3. IDs/permalinks públicos reproduzíveis;
4. outputs/snapshot completos;
5. checks verdes;
6. nota de completude coerente com a execução.

Se qualquer condição falhar, o coletor permanece versionado e a unidade é protocolada para reavaliação, sem bloquear a fila.

M3/M4 não participam da decisão de inclusão.
