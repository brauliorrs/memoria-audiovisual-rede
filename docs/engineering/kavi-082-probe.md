# Análise cumulativa nº 82 — KAVI / Elonet / Finna (sonda inicial)

## Escopo e estado

- Unidade: `fiaf-kavi` — Kansallinen audiovisuaalinen instituutti / National Audiovisual Institute, Finlândia.
- Issue: [#59](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59).
- **Estado: sonda técnica em avaliação; não incorporar nem avançar para nº 83.**
- Catálogo institucional publicamente indicado: [Elonet](https://elonet.finna.fi/Content/faq?lng=en-gb), serviço do KAVI integrado à Finna.
- Página oficial do KAVI: https://kavi.fi/en/film/
- Documentação oficial da [API Finna](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish).
- [Termos da API](https://www.kiwi.fi/spaces/Finna/pages/53839699/Finna%2BAPI%2BTerms%2Bof%2BUse): metadados CC0; mídias associadas e respectivos direitos não são automaticamente liberados.

### Continuidade institucional (2026)

Desde **1º de janeiro de 2026**, o National Audiovisual Institute (KAVI) e o Arts Promotion Centre Finland (Taike) foram unificados na **Finnish Arts and Culture Agency (Kuvi / Taide- ja kulttuurivirasto)**. A página oficial https://kavi.fi/en/about-kavi/ confirma a continuidade integral das atividades e a permanência dos sites e serviços. O identificador histórico `fiaf-kavi` continua válido para a análise da fila: não se criará uma entrada nova ou um segundo corpus apenas por mudança administrativa. A descoberta das facetas considera tanto KAVI como Kuvi, mas não mistura suas contagens sem prova de relação.

### Primeiro probe vivo (antes de filtro de provedor)

- CI `#38137767376`; artefato `kavi-elonet-probe`, id `11702041701`, ZIP sha256 `49f72736c796631675b37cddcaf188b0bf8678aaa4e1d9951c9cf1b5c331d66f`.
- `robots.txt` avaliados e válidos separadamente em `kavi.fi`, `elonet.finna.fi` e `api.finna.fi`.
- Páginas oficiais e duas consultas leves de API: **HTTP 200**, JSON válido.
- A primeira consulta respondeu com `resultCount=19.742.685`, que corresponde ao **índice Finna geral, não ao KAVI**. Reportou 236 entradas no facet `building`; o artefato inicial reteve apenas as primeiras 20 para inspeção.
- A consulta limitada pelo título `Salaviinanpolttajat` retornou identificadores `kavi.elonet_elokuva_117150` e `kavi.elonet_elokuva_1582895`, ambos classificados como vídeo/curta no retorno. O total de resultados da busca não é contagem de filmes do instituto nem de itens sob custódia.
- Gate inicial `investigate_kavi_provider_scope_and_batch_enumeration`; **0 registros incorporados**.

O segundo probe passa a procurar as facetas de construção institucional por seus rótulos e códigos **efetivamente retornados pela API** (KAVI / Kuvi), sem inventar filtros. Somente se houver **exatamente uma** faceta inequívoca, é feita uma amostra filtrada limitada a três registros. Se houver facetas múltiplas, os códigos são registrados e nenhuma hipótese de soma ou união é aplicada. O processo continua sem `resumptionToken` nesta etapa.

## Critérios de prova

Elonet publica filmografia e serviços VOD. O instituto informa que a base inclui títulos cujo uso audiovisual **não pertence** ao KAVI. Por isso, três conjuntos não podem ser tratados como equivalentes: filmes catalogados, filmes preservados sob custódia do instituto e filmes disponíveis para visualização online.

A Finna documenta `/v1/search`, `facet[]` e, para grandes conjuntos, a paginação por `resumptionToken`. Também alerta que a paginação normal não é adequada para volumes altos. A presente sonda **não inicia coleta em lotes**: faz apenas testes públicos mínimos de disponibilidade e formato (facet `building` e amostra de título documentada), condicionados a verificação de `robots.txt` individual por host.

A etapa seguinte só poderá realizar enumeração em lotes quando identificar e demonstrar um filtro **oficial/documentado e reprodutível** que limite o conjunto a fichas da instituição KAVI, separando formato audiovisual de registros de biblioteca, autoridade e material não fílmico. A origem KAVI no índice não estabelece por si posse de direitos de vídeo.

### Segundo probe vivo — faceta institucional comprovada

- CI `#38138032167`; artefato `kavi-elonet-probe`, id `11702067099`, digest ZIP `sha256:d775aae566ea0c7f89e9aca070493617fee1e115ca9170b9d3f1ab48c3c36bf1`.
- A API respondeu **HTTP 200** e identificou exatamente uma faceta `building` relacionada à continuidade KAVI/Kuvi: **`0/KAVI/`**, nome apresentado `Taide- ja kulttuurivirasto`, total anunciado **178.770 registros**.
- O filtro específico foi produzido **a partir desse código observado** e funcionou, retornando três registros de exemplo. O primeiro conjunto amostrado contém **livros** (`kavi_kirjasto.*`), demonstrando empiricamente que os 178.770 registros não são exclusivamente filmes.
- A busca por `Salaviinanpolttajat` retornou registros `kavi.elonet_elokuva_*` classificados como **Video** (código exibido `0/Video/`). Uma nova consulta exploratória de tamanho 3 combinará **os códigos institucionais e de formato que a API efetivamente retornou**, sem adivinhação.
- A verificação de `robots.txt` de `kavi.fi` respondeu **HTTP 202** nesta segunda execução, tornando a auditoria da página obrigatória inconclusiva; os outros dois robots foram avaliados e as consultas à API e Elonet permaneceram acessíveis. Isso não autoriza forçar o acesso ou declarar o gate institucional plenamente verificado.

## Protocolo da sonda

1. Avaliar `robots.txt` antes de qualquer consulta a `kavi.fi`, `elonet.finna.fi` e `api.finna.fi` (e novos hosts de redirecionamento separadamente).
2. Consultar as páginas oficiais de contexto e duas consultas pequenas e documentadas da API (facet com `limit=0`, busca de filme pelo título com `limit=2`).
3. Validar JSON, status, `resultCount`, identificadores não vazios e sem duplicação, faceta `building`, sem interpretar contagens de faceta como filme catalogado.
4. Proibir diretamente downloads de vídeos, filtros inferidos, IDs supostos, contorno de bloqueio, paginação massiva e incorporação automática.
5. Registrar por host/URL status, erro, evidência JSON, e gate fail-closed.

## Próximo gate

- Se API e Elonet forem acessíveis: investigar filtro exato do provedor, consulta somente de metadados com estrutura estável, `resumptionToken`, deduplicação, total reconciliado e amostras de fichas arquivísticas com proveniência.
- Se houver HTTP 403, challenge ou erro de `robots.txt`: registrar HOLD da superfície correspondente, sem contorno de proteção.
- Somente com enumeração **completa e verificável** e fichas semânticas comprovadas avançar a um staged collector de metadados.

## Reproduzir

```bash
python -m unittest discover -s tests -p 'test_kavi_elonet_probe.py' -v
python scripts/probe_kavi_elonet.py
```

Nenhum número de registros é afirmado antes da execução viva e exame de evidência.
