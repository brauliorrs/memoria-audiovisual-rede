# Análise cumulativa nº 80 — Institut Jean Vigo (HOLD)

## Identificação e decisão

- Unidade da fila: `inedits-jean-vigo-institute`.
- Instituição: Institut Jean Vigo / Cinémathèque de Perpignan, França.
- Diretório de origem: INEDITS.
- Issue de auditoria: [#55](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/55).
- PR técnico: [#56](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/56).
- Decisão de admissão: **HOLD / protocolo de não incorporação**.
- A decisão não declara ausência de patrimônio audiovisual: declara **ausência de uma enumeração patrimonial admissível e comprovada pelas duas superfícies públicas avaliadas**.
- Contador histórico: nº **80** consumido, **sem compactação da fila**. Próximo candidato nº **81**, `fiaf-jugoslovenska-kinoteka` (Jugoslovenska Kinoteka, Sérvia).

## Fonte primária: inst-jeanvigo.eu

Sonda não invasiva, com `robots.txt` antes do catálogo, sitemap declarado, redirects restritos aos dois hosts canônicos HTTPS, traversal estrutural `sitemapindex/sitemap/loc` e `urlset/url/loc`, recuperação fail-closed de XML irregular e suporte a gzip limitado em tamanho. Páginas de agenda, taxonomia editorial, páginas institucionais e fichas individuais têm classificações distintas. Nenhuma mídia foi baixada.

Resultado vivo da execução Quality Checks [#38078688641](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/38078688641):

| Indicador | Valor |
| --- | ---: |
| URLs públicas enumeradas | 2.392 |
| Agenda/programação | 1.359 |
| Editoriais | 489 |
| Árvore institucional de coleções | 10 |
| Outras páginas públicas | 534 |
| Páginas de coleções inspecionadas | 10/10 |
| Índices/hubs de coleções | 2 |
| Páginas com apontamento externo | 1 |
| Outras páginas institucionais | 7 |
| Fichas patrimoniais individuais confirmadas | 0 |
| Truncamento de traversal/auditoria | não |

Gate primário: `hold_primary_site_no_enumerable_archival_records`. A existência de uma descrição de filmes ou de uma agenda não constitui enumeração de fichas patrimoniais.

Proveniência técnica: artefato `jean-vigo-probe`, id `11679419761`, digest ZIP `sha256:71b95fb974202a26081c4efb90a950c5c090822ff0a9c7afe057d8e2d0765cdd`.

## Superfície subordinada: Mémoire Filmique Pyrénées-Méditerranée

O site institucional aponta uma parte dos filmes amadores para `https://www.memoirefilmiquedusud.eu/`, **plataforma compartilhada** que não deve ser atribuída integralmente ao Institut Jean Vigo.

A sonda independente verificou a rota pública `https://www.memoirefilmiquedusud.eu/collection`; a resposta HTTP 200 apresentou um desafio de verificação humana/antibot, com zero registros enumerados e nenhuma proveniência de custódia confirmada. `robots.txt` respondeu 404; isso não autoriza contornar a barreira.

Gate subordinado: `hold_external_surface_antibot_challenge`. Nenhuma tentativa de contornar captcha, autenticação ou challenge foi realizada. Não se infere um subconjunto de registros do Jean Vigo a partir da plataforma compartilhada.

Proveniência técnica: artefato `memoire-filmique-probe`, id `11679915069`, digest ZIP `sha256:12a5fe3c0c4e082a1de711f1b1802b1d5cd5e368acc48f06727538caf5fa424d`.

## Critérios de retomada

Reabrir a incorporação apenas com evidência de **enumeração completa e reproduzível** de fichas públicas, sem barreira de acesso e com confirmação semântica audiovisual. Para a plataforma compartilhada, exigir adicionalmente campo de custódia/proveniência por registro e incluir exclusivamente os registros vinculados ao Institut Jean Vigo. Rotas de catálogo, exportações ou APIs devem ser comprovadamente públicas; nenhuma inferência de IDs, scraping atrás de challenge ou download de mídia é admissível.

## Reprodutibilidade e sequência

```bash
python -m unittest discover -s tests -p 'test_jean_vigo_probe.py' -v
python -m unittest discover -s tests -p 'test_memoire_filmique_probe.py' -v
python scripts/probe_jean_vigo.py
python scripts/probe_memoire_filmique.py
python scripts/build_europe_research_queue.py
python scripts/next_inclusion_candidate.py --limit 3
```

O CI da análise nº 80 foi aprovado no HEAD anterior ao commit automático de persistência de fila; a geração de outputs pelo próprio GitHub Actions preserva a cadeia de proveniência. Os quatro arquivos de `data/output/` foram persistidos na branch, sem alteração de código.

A análise nº 81 só deve iniciar após a integração do PR #56 e o encerramento formal da issue #55.
