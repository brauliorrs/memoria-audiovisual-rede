# MAR — Migração funcional do Streamlit para o portal Vercel

**Objetivo:** transferir a experiência de estudo do audiovisual em rede para o Next.js. A regra de design é considerar o Streamlit como **referência funcional**, não como produto público definitivo. Migração e publicação são processos distintos: indicadores agregados e análises científicas podem ser expostos com contextualização, enquanto fichas/objetos de terceiros exigem portas específicas de admissão.


> **F01 — auditoria de equivalência (19/11/2026):** esta matriz histórica descreve páginas e *snapshots* disponibilizados. Expressões como “implementado” abaixo **não comprovam paridade funcional, integração operacional, admissão científica ou autorização de divulgação**. A auditoria rastreável está em [mar-f01-functional-equivalence-inventory.json](mar-f01-functional-equivalence-inventory.json), submetida ao controle da [fila #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128). O aceite de F01 continua pendente de testes por fluxo, revisão independente e registro de conclusão.

## Matriz de cobertura funcional (origem: app/streamlit_app.py, 5.425 linhas)

| Experiência Streamlit | Destino Next.js | Situação após esta etapa |
|---|---|---|
| Pesquisa global de fichas | `/acervo/` e `/acervo/kavi/[id]/` | **Implementado PT/EN/ES:** filtros, resultados e agora 200 páginas detalhadas com rótulos, proveniência, estados de validação e alertas traduzidos. Títulos, campos e identificadores preservados na forma de origem. SEO da ficha continua inicialmente em português |
| Visão geral do Observatório | `/observatorio/` | **Implementado nesta etapa**: cartões e painel comparativo |
| Categorias e agregadores | `/observatorio/` | **Implementado nesta etapa**: filtros e agrupamento por categoria |
| Territórios e distribuição | `/observatorio/`, `/territorios/` | **Implementado (agregado):** mapa mundial Natural Earth 1:110m de distribuições tema×país para fonte selecionada; regiões muito pequenas sem polígono aparecem apenas na tabela; não geolocaliza obras |
| Instituições e unidades | `/observatorio/[code]/` | **Implementado nesta etapa**: 63 perfis históricos com acesso, evidência e limites |
| Pesquisa comparativa multícorpus | `/comparar/` | **Implementado nesta etapa:** até três fontes, temas/países/plataformas, séries independentes, filtros e CSV agregado |
| Recortes científicos reproduzíveis | `/comparar/?a=...&b=...&view=...` | **Implementado nesta etapa:** filtros salvos em URL, cópia de link e proveniência fixada por commit no CSV e nos links dos insumos |
| Índice de Dados Públicos | `/indice-acesso/` | **Implementado PT/EN/ES:** introdução, números históricos, filtros, estados, motivos, limites jurídicos e acesso por fonte; mantém 63 corpora no inventário e zero novas fichas liberadas |
| Casos documentados | `/casos/` | **Implementado nesta etapa**: 17 casos explicativos |
| Síntese por corpus (integridade, disponibilidade, plataformas) | `/observatorio/[code]/` | **Implementado (agregado)**: 62 relatórios da fonte com indicadores de instituições, sites, integridade e plataformas |
| Instituições com vídeo e evidência | `/observatorio/[code]/` | **Parcial**: instituições com sinal de vídeo agregadas por fonte; tabelas individuais pendentes |
| Vídeos e temas | `/temas/` e `/observatorio/[code]/` | **Parcial**: temas agregados disponíveis por fonte; fichas audiovisuais sob HOLD continuam bloqueadas |
| Países, temas por plataforma, tipos de arquivo | `/temas/`, `/pesquisa/[code]/`, `/comparar/` | **Implementado em nível agregado:** cruzamentos tema×país e tema×plataforma, mais comparação entre até três corpora; **não** inferir país×plataforma |
| Tabelas, download de indicadores e dados | `/observatorio/`, `/comparar/` | **Parcial**: tabelas comparativas e exportação CSV **somente de indicadores agregados**, filtros, proveniência; exportação de metadados individuais sob HOLD vedada |
| Ficha institucional detalhada | `/instituicoes/pesquisa/`, `/instituicoes/pesquisa/[source]/[entry]/` | **Parcial**: perfis institucionais estáticos com proveniência e paginação; atualização dinâmica e integração completa pendentes |
| Fundamentação/metodologia | `/metodologia/` e perfis | **Parcial:** quatro critérios científicos traduzidos PT/EN/ES, relatórios de acesso e proveniência preservados; fundamentação metodológica aprofundada continua pendente |
| Alternância de idiomas | Seletor global PT/EN/ES, fichas KAVI, catálogo, acesso e núcleo científico | **Ampliado nesta etapa:** as 200 fichas KAVI detalhadas traduzem a interface, metadados de campo, proveniência e avisos de não verificação, sem alterar valores de origem. Áreas institucionais legadas, SEO e traduções documentais revisadas continuam pendentes |
| Ciclo de coleta, descoberta, atualização e governança | Área analítica e documentação | **Pendente**: visualização de relatórios operacionais sem credenciais |
| Comparação longitudinal e linha do tempo | `/series/`, `/comparar/` | **Implementado em snapshots**: gráficos por fonte e comparação separada de até três corpora, sem alinhamento artificial das datas; atualização ao vivo pendente |
| Exportação de fichas individuais de fontes sob HOLD | Catálogo | **Bloqueado**, não é requisito para liberar painéis agregados |

## Princípios de publicação
- **Estudo ≠ redistribuição de mídia:** publicar painéis agregados, transparência, metodologia e perfis institucionais é distinto de incorporar descrições extensas ou objetos.
- Não alterar corpora científicos congelados, bancos, coletores nem Streamlit enquanto o novo site cresce.
- Toda rota estática tem testes e não aciona serviços externos.
- Histórico de migrações e URLs permanece no `docs/engineering/mar-publication-ledger.md`.
- Os 194.057 registros do snapshot são registros classificados historicamente, **não fichas novas disponíveis**.
- Acesso por navegador a um catálogo institucional não autoriza reprodução do filme.

## Próxima ordem de execução
1. **Concluído neste PR:** migrados 62 relatórios agregados, com indicadores de disponibilidade, instituições e plataformas por fonte.
2. Cruzamentos de temas, países, visibilidade e tipos por corpus.
3. **Parcial**: séries históricas e novo mapa mundial por país (1:110m); geometrias de pequenos territórios e georreferenciamento de obras não disponíveis.
4. **Parcial**: comparação de até três corpora com filtros reproduzíveis em URL e proveniência Git fixada; futuras hipóteses e recortes com autenticação/perfis permanecem pendentes.
5. **Parcial, ampliado**: núcleo científico, catálogo KAVI (busca e 200 fichas detalhadas) e Índice de Dados Públicos em PT/EN/ES com testes. Restam algumas páginas institucionais legadas, SEO indexável por idioma, revisão humana das evidências documentais e auditoria visual/acessibilidade.
6. Substituir o Streamlit somente depois da equivalência funcional e da revisão de operação.

**Não usar “migração completa” até cada linha desta matriz ter implementação e validação demonstradas.**

## F01 — índice auditável de fluxos (sem aceite funcional)

Inventário estrutural fechado nesta revisão: **24 fluxos** (20 de interface Streamlit e 4 operacionais Python), incluindo referência explícita a **64 funções top-level**: 20 `render_*`, 18 `build_*/load_*` e 26 helpers adicionais; também **13 grupos de abas `st.tabs`**. Identificação dos símbolos e caminhos validada contra o código do SHA `66e79afa8755ca2ff12f1a8088c9ffc808a8a8a3`. A cobertura é **de rastreabilidade**, não de testes de comportamento equivalentes.

| ID | Fluxo | Situação de equivalência | Origem |
|---|---|---|---|
| `M01` | Pesquisa global multidimensional | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M02` | Fichas KAVI autorizadas | Snapshot presente; equivalência não demonstrada | `app/streamlit_app.py` |
| `M03` | Indice historico de acesso | Snapshot presente; equivalência não demonstrada | `app/streamlit_app.py` |
| `M04` | Visao geral e categorias do observatorio | Snapshot presente; equivalência não demonstrada | `app/streamlit_app.py` |
| `M05` | Mapa territorial de indicadores | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M06` | Comparacao multicoRpus | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M07` | Series historicas | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M08` | Paineis por corpus | Snapshot presente; equivalência não demonstrada | `app/streamlit_app.py` |
| `M09` | Cruzamentos tematicos e plataformas | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M10` | Instituicoes e filtros da base | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M11` | Ficha institucional detalhada | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M12` | Relatorios agregados de analise | Snapshot presente; equivalência não demonstrada | `app/streamlit_app.py` |
| `M13` | Downloads e exportacoes | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M14` | Fundamentacao e protocolos | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M15` | Internacionalizacao PT EN ES | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `M16` | Fila de descoberta e propostas | Integração operacional pendente | `app/streamlit_app.py` |
| `M17` | Fechamento de corpora europeus | Integração operacional pendente | `app/streamlit_app.py` |
| `M18` | Historico de ciclos operacionais | Integração operacional pendente | `app/streamlit_app.py` |
| `M19` | Casos documentados | Snapshot presente; equivalência não demonstrada | `app/streamlit_app.py` |
| `M20` | Completude de metadados KAVI | Cobertura parcial; equivalência não demonstrada | `app/streamlit_app.py` |
| `B01` | Seletor de candidatos cientificos | Integração operacional pendente | `src/memoria_audiovisual/inclusion_queue.py` |
| `B02` | Motor universal de admissao | Integração operacional pendente | `src/memoria_audiovisual/corpus_admission_engine.py` |
| `B03` | Ciclo de atualizacao de corpora | Integração operacional pendente | `scripts/run_observatory_cycle.py` |
| `B04` | Projetor e bundle cientifico | Cobertura parcial; equivalência não demonstrada | `scripts/build_mar_site_projections_b2.py` |

### Lacunas que bloqueiam o aceite integral

- **Pesquisa global:** Streamlit permite dez filtros dimensionais e uma seleção de reprodução verificada; o catálogo Next.js é o subconjunto de 200 fichas KAVI com pesquisa, década, tema e ordenação. Ampliar somente após discriminar dados realmente autorizados; não reaproveitar a exportação integral do legado em site público.
- **Administração:** descoberta e fila de candidatos, fechamento europeu, ciclos e checkpoints **não têm equivalente operacional integrado** no site; precisam de Neon governado e autenticação efetiva nas etapas F03–F08, sem alterar a ordem da fila.
- **Detalhes e direitos:** fichas institucionais, vídeos na origem, dados detalhados e downloads exigem separação por nível de acesso e direitos; a presença de 63 perfis ou 62 relatórios não autoriza publicação de fichas dos corpora correspondentes.
- **Projeções e sincronização:** o replay real ARCHIPOP e 34 projeções do baseline comprovam a reconstrução do estado atual, mas não a admissão científica de um corpus novo nem o sincronismo operacional em produção.
- **Aceite:** executar e vincular testes positivos/negativos específicos de cada comportamento, auditoria visual e de dados, revisão humana e registro no gate F01; CI verde e existência de rota são insuficientes.

A verificação automática `scripts/check_mar_f01_equivalence_inventory.py` e seus testes de contrato impedem perda silenciosa de símbolos, referências ou marcas de HOLD. O validador só inspeciona rastreabilidade e **não pode declarar conclusão nem aprovação científica**.
