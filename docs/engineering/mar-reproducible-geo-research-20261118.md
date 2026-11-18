# MAR — Recortes científicos reproduzíveis e cartografia territorial

**Marco:** 18/11/2026. **Aplicação:** exclusivamente o projeto Vercel existente `mar-public-site` e domínio `https://mar-public-site.vercel.app/`. **Origem funcional:** Streamlit e indicadores analíticos congelados já migrados para o Next.js. **Não altera** app/streamlit_app.py, Neon, corpora ou autorização de fichas.

## 1. URL reproduzível da bancada comparativa

A rota `/comparar/` codifica o estado em query string, sem serviço externo, identificador de usuário ou banco. Parâmetros:
- `a`, `b` e `c`: 2 a 3 códigos de corpora já integrantes de `site/data/research-slices-{0..15}.json`; duplicações e fontes inexistentes são descartadas.
- `view`: `distributions` ou `timeline`.
- `dimension`: `theme`, `country` ou `platform`.
- `metric`: somente uma das 5 métricas permitidas pela análise histórica.
- `q`: filtro de termo, com limite de 96 caracteres, sem caracteres de controle.
- `shared`: `1` para termos comuns a pelo menos duas fontes; outro valor significa não habilitado.
- `lang`: `pt`, `en`, `es`.

O botão **Copiar link desta pesquisa** compartilha o recorte; a URL é sincronizada quando o usuário altera filtros. A reabertura em outro navegador restaura a seleção. O link é uma **configuração de estudo**, não uma cópia dos dados. Dados públicos são estáticos e podem evoluir após um novo release, por isso a UI e os CSVs registram a revisão congelada de origem.

**Revisão científica dos snapshots (16 lotes):** `857cc40f119025ac4a9b2902ba4d1b1310d742bd`, confirmada no último commit da série `site/data/research-slices-15.json`. Os CSVs incluem `source_snapshot_commit`; links para arquivos de origem usam `blob/<sha>/data/output/...` em vez de `blob/main`.

**Testes executáveis:** `site/tests/research-permalink.test.cjs` via `npm run test:permalink`; tipagem estática via `npm run typecheck`; contratos documentais `tests/test_mar_geographic_permalinks.py`.

## 2. Mapa de países baseado em geometrias verificadas

A rota `/territorios/` usa:
- **Números:** somente as linhas `tema_pais` historicamente produzidas por fonte, no conjunto de 16 lotes estáticos.
- **Geometria:** Natural Earth, 1:110m, por meio de [datasets/geo-boundaries-world-110m](https://github.com/datasets/geo-boundaries-world-110m). Dados cartográficos sob ODC-PDDL e fonte Natural Earth de domínio público; arquivo `countries.geojson`, blob Git `2fcecba48f66fb5d24ed0e9644e877a870f9c560`. Derivação: projeção equiretangular da longitude/latitude em desenho SVG (900 × 450), arredondamento de coordenadas em pixels e preservação dos polígonos sem novos pontos inventados. Resultado versionado: `site/data/world-110m-geometry.json`.
- **Filtros:** um corpus e um tema por vez. Países sombreados mostram a quantidade observada na **fonte selecionada**; intensidades relativas ao maior valor do mesmo corpus, não à produção audiovisual mundial.
- **Pequenos territórios:** `Monaco` e `Isle of Man` não têm polígonos nesta edição de geometrias Natural Earth 110m. Suas contagens continuam visíveis na tabela, explicitamente sinalizadas como sem geometria. Nenhum centroide ou posição fictícia é usado.
- **Proveniência:** vínculo ao CSV original no commit científico congelado. O mapa não incorpora player, imagens, itens individuais ou descrições de fontes com restrição.
- **Idiomas:** rótulos e explicações em PT/EN/ES; nomes científicos dos países seguem os insumos originais sem tradução artificial.

**Limitações científicas:** o país de um registro é uma associação de metadados e não necessariamente o lugar de produção, filmagem ou circulação da obra. Não deduzir `país × plataforma` de duas tabelas independentes, nem somar fontes que podem conter a mesma obra. O desenho 1:110m é esquemático, e limites de países não estabelecem posições políticas ou jurídicas.

## 3. Regra de publicação e próximos passos

- Continuam **200 fichas KAVI publicadas** no catálogo sob gate específico, sem novas fichas liberadas por estes painéis.
- Os indicadores históricos de fontes sob HOLD podem ser estudados apenas de forma agregada; qualquer avanço para dados individualizados depende de validação editorial, jurídica e científica.
- A migração de PT/EN/ES **não está completa**: bancada de comparação, mapa, seletor e partes das páginas científicas têm suporte, mas textos legados no observatório, metodologia, outras fichas e institucional ainda exigem tradução.
- As fontes geográficas e estatísticas estão versionadas para auditoria. Expansão cartográfica deverá reconciliar nomes de países com fontes verificadas, nunca incluir coordenadas inferidas.

Após testes e merge, publicar no **mesmo** projeto Vercel `mar-public-site`; jamais criar projeto paralelo nem inferir acessibilidade anônima a partir do estado READY.
