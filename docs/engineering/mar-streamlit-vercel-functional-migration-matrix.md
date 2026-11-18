# MAR — Migração funcional do Streamlit para o portal Vercel

**Objetivo:** transferir a experiência de estudo do audiovisual em rede para o Next.js. A regra de design é considerar o Streamlit como **referência funcional**, não como produto público definitivo. Migração e publicação são processos distintos: indicadores agregados e análises científicas podem ser expostos com contextualização, enquanto fichas/objetos de terceiros exigem portas específicas de admissão.

## Matriz de cobertura funcional (origem: app/streamlit_app.py, 5.425 linhas)

| Experiência Streamlit | Destino Next.js | Situação após esta etapa |
|---|---|---|
| Pesquisa global de fichas | `/acervo/` | Já disponível, 200 fichas KAVI |
| Visão geral do Observatório | `/observatorio/` | **Implementado nesta etapa**: cartões e painel comparativo |
| Categorias e agregadores | `/observatorio/` | **Implementado nesta etapa**: filtros e agrupamento por categoria |
| Territórios e distribuição | `/observatorio/`, `/territorios/` | **Implementado (agregado):** mapa mundial Natural Earth 1:110m de distribuições tema×país para fonte selecionada; regiões muito pequenas sem polígono aparecem apenas na tabela; não geolocaliza obras |
| Instituições e unidades | `/observatorio/[code]/` | **Implementado nesta etapa**: 63 perfis históricos com acesso, evidência e limites |
| Pesquisa comparativa multícorpus | `/comparar/` | **Implementado nesta etapa:** até três fontes, temas/países/plataformas, séries independentes, filtros e CSV agregado |
| Recortes científicos reproduzíveis | `/comparar/?a=...&b=...&view=...` | **Implementado nesta etapa:** filtros salvos em URL, cópia de link e proveniência fixada por commit no CSV e nos links dos insumos |
| Índice de Dados Públicos | `/indice-acesso/` | Integrado e implantado em fase anterior |
| Casos documentados | `/casos/` | **Implementado nesta etapa**: 17 casos explicativos |
| Síntese por corpus (integridade, disponibilidade, plataformas) | `/observatorio/[code]/` | **Implementado (agregado)**: 62 relatórios da fonte com indicadores de instituições, sites, integridade e plataformas |
| Instituições com vídeo e evidência | `/observatorio/[code]/` | **Parcial**: instituições com sinal de vídeo agregadas por fonte; tabelas individuais pendentes |
| Vídeos e temas | `/temas/` e `/observatorio/[code]/` | **Parcial**: temas agregados disponíveis por fonte; fichas audiovisuais sob HOLD continuam bloqueadas |
| Países, temas por plataforma, tipos de arquivo | `/temas/`, `/pesquisa/[code]/`, `/comparar/` | **Implementado em nível agregado:** cruzamentos tema×país e tema×plataforma, mais comparação entre até três corpora; **não** inferir país×plataforma |
| Tabelas, download de indicadores e dados | `/observatorio/`, `/comparar/` | **Parcial**: tabelas comparativas e exportação CSV **somente de indicadores agregados**, filtros, proveniência; exportação de metadados individuais sob HOLD vedada |
| Ficha institucional detalhada | `/instituicoes/pesquisa/`, `/instituicoes/pesquisa/[source]/[entry]/` | **Parcial**: perfis institucionais estáticos com proveniência e paginação; atualização dinâmica e integração completa pendentes |
| Fundamentação/metodologia | `/metodologia/` e perfis | **Parcial:** quatro critérios científicos traduzidos PT/EN/ES, relatórios de acesso e proveniência preservados; fundamentação metodológica aprofundada continua pendente |
| Alternância de idiomas | Seletor global PT/EN/ES e núcleo científico | **Ampliado nesta etapa:** Observatório, tabelas de 62 relatórios, 63 perfis de corpus (estrutura), metodologia, casos, introdução do catálogo e rótulos de fichas institucionais; fontes documentais originais continuam no idioma de origem; índice de acesso, pesquisa de fichas e descrições institucionais ainda não têm tradução completa |
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
5. **Parcial, ampliado**: núcleo científico de Observatório, comparações, análises por fonte, metodologia, casos, mapa e introdução do catálogo PT/EN/ES, com testes. Faltam tradução do índice de acesso, controles do catálogo e descrições de fontes, conteúdo integral das fichas e auditoria visual/acessibilidade.
6. Substituir o Streamlit somente depois da equivalência funcional e da revisão de operação.

**Não usar “migração completa” até cada linha desta matriz ter implementação e validação demonstradas.**
