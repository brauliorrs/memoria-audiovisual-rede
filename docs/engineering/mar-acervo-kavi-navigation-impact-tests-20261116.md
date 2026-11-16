# MAR — retomada do acervo documental: navegação facetada KAVI/Finna (16/11/2026)

## Auditoria de impacto antes do código

Base: `main` em `42a2cd70f401eb33d48a5340952f37979235b09c`. A implementação não depende do PR #93 de backup, que permanece draft/HOLD para produção.

**Fonte existente:** `load_published_kavi_rows(data/output)` valida SHA-256, manifesto, 200 registros aprovados de metadados e links individuais de ficha institucional. `render_kavi_kuvi_metadata_tab` já oferece busca textual e relatórios de completude. `build_research_video_catalog_frame` inclui fichas KAVI na pesquisa transversal com aviso de mídia não verificada.

**Alteração necessária:** tornar mais útil a navegação do lote já publicado por meio de filtros combinados por ano, idioma e classificação documental; oferecer paginação determinística e resultados ordenados com link original preservado. Função pura em módulo novo `kavi_finna_catalog_navigation.py`; integração exclusivamente na aba KAVI. Sem novos registros, dados externos, download de mídias, scraping, player, persistência de cursor ou alterações em `CORPORA`.

**Dependências e riscos:** leitor de publicação, Streamlit, traduções pt/es/en, testes unitários. Não alimentar estatísticas de filmes/vídeos reproduzíveis, nem declarar cobertura de acervo completo. O arquivo CSV publicado, manifesto e relatórios permanecem imutáveis. Nenhum acesso a Neon/Blob ou secrets.

## Testes e contratos antes de código

- N1: pesquisa ignora maiúsculas e acentos, abrange título/ano/créditos/gêneros/assuntos/idiomas e não usa regex.
- N2: filtro combinado por ano, idioma e classificação não promove metadado a filme validado.
- N3: paginação estável com ordenação por título normalizado + ID institucional; IDs distintos preservados mesmo com títulos iguais.
- N4: página fora da faixa, tamanho de página inválido, metadados sem link oficial ou IDs duplicados rejeitados; total nunca muda por paginação.
- N5: função não lê rede, não escreve arquivos, não altera entradas.
- N6: interface usa somente linhas retornadas pelo leitor validado, nunca visualiza prévias de staging nem recursos de mídia.
- N7: traduções novas pt/es/en e testes `test_i18n.py` devem passar; nenhuma regressão do catálogo global.
- N8: CI completo aprovado, PR draft para revisão; sem merge automático e sem ativar workflows.

## Reversão e critérios de aceite

Rollback: reverter import e bloco de navegação na aba KAVI, apagar módulo novo e testes; CSV/manifesto originais não se alteram. Gate de aceitação: suíte de navegação + regressões KAVI + CI `quality` verdes. Teste do deploy Streamlit permanece etapa distinta.
