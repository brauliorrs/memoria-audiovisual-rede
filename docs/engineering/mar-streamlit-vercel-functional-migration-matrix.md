# MAR — Migração funcional do Streamlit para o portal Vercel

**Objetivo:** transferir a experiência de estudo do audiovisual em rede para o Next.js. A regra de design é considerar o Streamlit como **referência funcional**, não como produto público definitivo. Migração e publicação são processos distintos: indicadores agregados e análises científicas podem ser expostos com contextualização, enquanto fichas/objetos de terceiros exigem portas específicas de admissão.

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

## Etapa posterior — redação institucional e SEO (18/11/2026)

**Implementado na branch desta etapa:** textos institucionais restantes e nuvem de termos em PT/EN/ES; metadados canônicos das páginas originais, SEO institucional e duas entradas estáticas de apresentação em EN/ES com hreflang fundamentado. Sitemap restringe registros individuais aos 200 KAVI já admitidos; os perfis históricos de outras fontes não são liberados como itens. **Ainda pendente:** revisão humana de evidências documentais, SEO com HTML de idioma dedicado em todos os painéis/fichas e auditoria visual/deploy de produção no único Vercel existente. O Streamlit e as políticas HOLD não mudam. Detalhes em docs/engineering/mar-editorial-seo-multilingual-20261118.md.
