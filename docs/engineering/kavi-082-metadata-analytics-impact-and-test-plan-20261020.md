# MAR — KAVI/Kuvi nº 82: auditoria preventiva de impacto e plano de testes

**Pré-registro ANTES DE QUALQUER ALTERAÇÃO DE CÓDIGO.** Data: 20/10/2026. Estado da `main` auditado: `c8e7ab809e2051b6b2012f484f78cadf1bbd55e6` (PR #86 integrado). Escopo científico **somente relatórios e indicadores de fichas documentais** provenientes do lote Finna publicado. Não altera os critérios de acesso, o coletor, a análise científica #82 nem autoriza extração de novos registros.

## 1. Inventário factual

- Fonte já publicada: `data/output/kavi_mar_metadata_links.csv` (200 registros/200 links individuais `recordPage`), validada pelo `load_published_kavi_rows()` contra `data/output/kavi_mar_metadata_links_manifest.json` e SHA-256 `2458484980094c10db9e9f990b6ca2236e8abcfdb09d3cafc886d0e0e9b22a31`. Referência histórica da faceta KAVI × vídeo: 138.399 em 19/10/2026; **não** é quantidade de filmes reproduzíveis, filmes com custódia ou universo completo do sítio.
- `kavi_finna_registry.load_kavi_metadata_index_summary()` já computa total de fichas, links, percentual sobre snapshot e situação de playback não comprovada; `app/streamlit_app.py::render_kavi_kuvi_metadata_tab` oferece a aba específica; pesquisa global inclui links verificados por item.
- `output_files.build_output_files()` reserva artefatos tradicionais `summary`, `video_links`, `analytic_video_catalog`, visibilidade, disponibilidade etc.; **não** há tais saídas analíticas KAVI materializadas nem contrato que as torne equivalentes a vídeos.
- `dashboard_data.build_dashboard_base_data()`, `analysis_exports.build_analysis_frames()` e `app/streamlit_app.py::build_category_combined_frames()` são construídos para catálogos audiovisuais e estatísticas de obras com links classificados. São **consumidores com semântica incompatível** com registros `recordPage` sem validação de playback.
- O cadastro `CORPORA['kavi_kuvi']` possui `published_index_active=true`, `organism_active=false`, `monthly_refresh_enabled=false`, `counts_as_analyzed_corpus=false`. **Esses estados não podem mudar** nesta fase. A FINA/Ninateka polonesa é outra unidade.
- A interface Streamlit hospedada não foi validada funcionalmente; testes de unidade/CI não equivalem a teste do deploy.

## 2. Matriz prévia de impacto (alteração → consumidores → risco → teste → reversão)

| Mudança planejada | Dependências/consumidores | Efeito indireto a evitar | Verificação pré-definida | Reversão |
| --- | --- | --- | --- | --- |
| Função pura de relatórios de fichas sobre `load_published_kavi_rows` | `kavi_finna_public_catalog.py`, `kavi_finna_registry.py`, CSV/manifesto | Injetar metadado não auditado, recontar IDs, sobrepor snapshot | A1, A2, A3, A4 | Remover o módulo sem mudar o catálogo fonte |
| Indicadores de cobertura e completude de descritores | IDs, campos opcionais, `film_semantics`, `media_access_status` | Confundir presença de campo com qualidade curatorial; inferir disponibilidade e direitos | A2, A5, A6, A7 | Desativar somente indicadores documentais |
| Exportação de relatórios padronizados em namespace `metadata_*` | `output_files`, relatórios existentes, `reporting`, scripts de check, CI | Escrever nomes de arquivos reservados para vídeos; modificar fonte ou publicar mídia | A3, A8, A9 | Remover arquivos derivados; fonte imutável |
| Apresentação na aba institucional KAVI | `render_kavi_kuvi_metadata_tab`, filtros e links; pesquisa global | Quebrar campos opcionais, renomear links, inflar totais de vídeo nas categorias | A5, A10, A11 | Reverter só bloco de indicadores da aba |
| Regressão das interfaces/filas globais | `CORPORA`, `europe_research`, `dashboard_data`, organismos e workflows | Fechar nº 82, avançar fila para nº 83 ou iniciar cron | A11, A12, A13 | Nenhuma alteração permitida nesses contratos |

## 3. Contrato técnico antes do código

**Pré-condição:** CSV de metadados e manifesto já publicados devem passar integralmente na validação existente (SHA, contagem, IDs únicos, links de ficha por item, escopo e direitos). Se faltar fonte ou ocorrer corrupção: **HOLD/REJECT, nunca produzir relatórios novos ou declarar números**.

**Entradas:** sequência de dicionários de metadados **já verificados**, manifesto correspondente e caminho de destino externo aos arquivos da fonte. Não usar serviço remoto ou inferir campos não recebidos.

**Saídas propostas e independentes:** relatório-resumo documental, tabela de completude de campos e distribuição por tipo de metadado (p.ex. `film_candidate` versus `unverified_audiovisual_record`). Formato CSV/JSON, rótulos explícitos; arquivos em namespace `kavi_kuvi_metadata_*`, sem utilizar `analytic_video_catalog`, `video_links`, `availability_summary` ou estatísticas curatorias existentes. Relatórios e interface devem derivar da **mesma função pura**.

**Métricas com suporte na fonte:** fichas indexadas, links para fichas, % dessa **faceta e snapshot** da API, datas e metadados opcionais presentes/não preenchidos (título, ano, créditos, assunto, idioma, sinopse, gênero), classes de registros e estados comprovados de anotação. Uma string não vazia informa preenchimento do campo, **não valida sua correção factual**.

**Proibido apresentar como resultados:** total de filmes assistíveis, métricas de streaming, direitos de mídia concedidos, domínio público, custódia demonstrada, coleção exaustiva, curadoria concluída, vídeos reproduzidos; `online_url_metadata_present` não é confirmação de reprodução. Valores referentes a verificações inexistentes devem ser rotulados `não verificado`, não `0 vídeos disponíveis`.

**Invariantes:** CSV e manifesto fontes byte-a-byte inalterados; 200 IDs atuais com 200 links; numeração científica nº82 intacta; `organism_active=false` e `monthly_refresh_enabled=false`; sem chamadas HTTP nem download; nenhuma substituição de relatórios de outros corpora; FINA/Ninateka sem alterações; não introduzir contagem global de vídeos a partir das fichas.

**Compatibilidade/reversão:** adicionar arquivos e relatórios documentais complementares, sem modificar interfaces genéricas nem executar coletores. A função de resumo do registro atual pode ser reutilizada para a apresentação de metadados. O processamento deve ser reproduzível com os bytes do snapshot e lançar erro explícito ao receber fonte inválida.

## 4. Plano de testes pré-implementação — IDs e condições de aceite

| Caso | Condição | Resultado esperado |
| --- | --- | --- |
| A1 | Lote real publicado 200/200 validado com SHA | Totais de fichas e links exatamente 200, total de referência 138.399, status parcial e data de 19/10/2026 |
| A2 | Fonte em memória com 2 ou mais fichas e descritores presentes/ausentes | Completude por campo com denominador igual ao número de registros, sem imputar valores |
| A3 | CSV/manifesto adulterado ou ausente | Rejeição fail-closed, nenhum novo arquivo materializado/alterado |
| A4 | ID repetido ou link de mídia, mesmo com campo preenchido | Validador já existente rejeita antes de computar o relatório |
| A5 | Campos opcionais omitidos (`authors`, `languages`, `genres`, `summary`) | Relatório preserva contagens; aba KAVI não lança exceções |
| A6 | `online_url_metadata_present=true` com `media_access_status=unverified` | Nenhum vídeo dado como reproduzível/confirmado ou custodiado |
| A7 | `film_semantics=film_candidate` e `record_review_status=unreviewed` | Estado apresentado como candidato documental, nunca filme validado |
| A8 | Mesma fonte processada duas vezes | Mesmos valores e saídas determinísticas, sem carimbo variável embutido |
| A9 | Exportação documental | Não cria/sobrescreve `kavi_mar_metadata_links.csv` nem `kavi_kuvi_catalogo_videos_analitico.csv`, e não inclui URLs de mídia |
| A10 | Interface KAVI | Indicadores documentais exibidos de forma independente do filtro de vídeos públicos, com links de ficha preservados |
| A11 | Painel geral/categoria | Total de vídeos confirmados e seleção de catálogos curatorias não sofrem aumento artificial |
| A12 | Cadastro científico | `kavi_kuvi` permanece distinto de `fina`, 81 análises concluídas, candidato nº82 |
| A13 | Organismo e permissões | `organism_active=false`, `monthly_refresh_enabled=false`, nenhum job de Finna executado por geração de relatório |

**Definition of Ready:** impacto, fontes, invariantes, critérios A1–A13 e rollback acima aprovados como especificação. **Definition of Done:** regressões específicas e suíte existente verdes no HEAD do PR; revisão P1/P2 resolvida; merge somente com CI integral aprovado; releitura da `main`; atualização da issue nº59 e da memória do Drive.

## 5. Riscos conhecidos — sem redescoberta como risco novo

- **R1 — resolvido:** contagem CORPORA versus análises científicas; protegido por `counts_as_analyzed_corpus=false`; A12.
- **R2 — controle existente:** ficha Finna != player/permite mídia; protegido por `load_published_kavi_rows`; A4, A6, A7, A11.
- **R3 — limitação a resolver NESTE incremento:** faltam relatórios de metadados documentalmente comparáveis; não copiar nomes de saídas de `video_links`; A1–A10.
- **R4 — HOLD conhecido fora do escopo:** paginação com `resumptionToken` e atualizações persistentes; não realizar scraping nem tocar no ciclo agendado; A13.
- **R5 — verificação externa pendente:** deploy Streamlit não comprovado por CI; registro distinto, sem alegar que está publicado online.

## 6. Adendo pós-implementação — regressão de i18n capturada pelo CI

**Registro honesto de uma lacuna do plano inicial (não é risco novo de Finna):** a primeira execução do CI integral detectou que dois textos acrescentados à aba KAVI não estavam traduzidos em inglês/espanhol em `src/memoria_audiovisual/i18n.py`. A auditoria preliminar mencionava interface, mas não incluiu nominalmente `tests/test_i18n.py` como teste de regressão de interface; esse acoplamento é verificável no código e deveria ter sido mapeado.

**A14 — contrato permanente para alterações na UI:** qualquer texto visível novo no Streamlit exige mapeamento para `PHRASE_TRANSLATIONS['es']` e `['en']`, com teste de tradução e verificador `test_streamlit_visible_portuguese_fragments_are_covered` executados em etapa específica antes da suíte geral. Foi adicionado um teste exato para rótulos da aba KAVI e à etapa KAVI no Quality Checks, sem enfraquecer as regras de tradução. Classificação: **REGRESSÃO INTRODUZIDA NO PR, CORRIGIDA ANTES DO MERGE**, nunca limitação histórica do Finna.

**Adendo de qualidade A3:** revisão P2 encontrou que a geração de relatórios exigia `observed_on` sem checar a presença desse campo. Incluiu-se validação ISO YYYY-MM-DD e teste negativo para ausência/formato inválido. Mantém rejeição fail-closed e evita traceback ao usuário. O contrato do relatório fica mais estrito; o CSV de 200 fichas e o manifesto não foram modificados.

**Sequência de execução autorizada por esta auditoria:** commit deste documento **primeiro** → função pura e testes A1–A9 → interface documental e A10–A13 → CI integral → revisão → eventual merge. Nenhuma nova API Finna será consultada nesta tarefa.
