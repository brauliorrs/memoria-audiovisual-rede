# Forum des images — decisão de incorporação da rodada

**Fila europeia:** rank 6 (`inedits-forum-des-images`)  
**Decisão em 30/09/2026:** **não incorporar nesta rodada; manter protocolado para reavaliação**.

## Evidência pública

A superfície `https://collections.forumdesimages.fr/` oferece catálogo audiovisual público, busca/pesquisa avançada, facetas e fichas individuais. A instituição declara um fundo superior a 8.000 filmes e distingue, na interface, estados de visibilidade na internet. Essa evidência foi suficiente para construir um coletor limitado e reproduzível, sem uso de M3/M4.

## Prova operacional

O PR #33 executou o coletor real no GitHub Actions, após os testes sintéticos. Quality Checks #1760 materializou o artefato temporário `forum-des-images-baseline`:

- workflow run: `36766309512`;
- HEAD: `bf68572dcc77d42998a85a67c71715aebd0f610f`;
- artifact id: `11121660413`;
- artifact SHA-256: `e532f94617e6c5ff6cded70e122cc8d568c5cfc1df3e4426625cf946f2abcdcf`;
- snapshot `generated_at`: `2026-09-30T19:33:10Z`.

Resultado da rodada real:

- registros audiovisuais materializados: **0**;
- páginas tentadas: **5**;
- todas as páginas: `bloqueado_robots`;
- causa: `robots_unreachable`;
- `institutions_with_video_links`: **0**;
- `videos_in_curatorial_catalog`: **0**.

O coletor foi deliberadamente implementado em modo **fail-closed**: se não consegue verificar a política `robots.txt`, não presume autorização e não segue para a coleta.

## Interpretação

O resultado **não significa** que o catálogo inexista ou que a instituição não ofereça metadados públicos. A existência do catálogo foi confirmada independentemente pela superfície pública. O resultado significa que, nas condições do executor de incorporação desta rodada, o MAR **não consegue demonstrar autorização de crawl de modo compatível com sua política**.

Por isso:

- Forum des images **não entra em `CORPORA` ativo**;
- o coletor, parser, pipeline e checks permanecem versionados como engenharia pronta para reavaliação;
- a unidade recebe estado `protocolado`, `blocks_expansion=false`;
- a fila pode prosseguir sem reordenamento;
- o próximo candidato passa a ser **Friedrich-Wilhelm-Murnau-Stiftung, rank 7**.

## Gate para futura incorporação

Reavaliar em ciclo futuro. Somente ativar o corpus se:

1. a política de robots puder ser verificada sem contornar barreira;
2. a rota pública continuar disponível;
3. o coletor materializar registros não vazios de forma reprodutível;
4. os checks de corpus e snapshot passarem;
5. a promoção a `CORPORA` ativo ocorrer em PR próprio.

Não reutilizar o artefato temporário da rodada bloqueada como corpus científico.
