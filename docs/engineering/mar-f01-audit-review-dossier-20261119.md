# MAR — F01: dossiê de auditoria e decisão de saída

**Escopo:** somente F01 da [fila de implantação #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128). **Referência científica e de interface:** `main` no SHA `66e79afa8755ca2ff12f1a8088c9ffc808a8a8a3`. **Trabalho em revisão:** [PR #127](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/127). **Estado deste dossiê: EM REVISÃO; não aprovado.**

## Propósito e fronteira de aceite

F01 é uma **auditoria e um diagnóstico de equivalência**, não a implementação de todos os recursos e não a desativação do Streamlit. Sua aprovação significa que **cada fluxo foi corretamente inventariado, classificado, vinculado ao código, às fontes e ao item posterior de remediação**, com regressões estruturais e de dados verificáveis. As lacunas identificadas serão corrigidas somente nas etapas próprias (F03–F10, conforme a fila). Não declarar “site equivalente” ou “migração concluída” ao encerrar F01.

## Base inspecionada e cobertura rastreável

- Código original: `app/streamlit_app.py`, 5.425 linhas; todos os **20 renderizadores top-level `render_*`** e **18 helpers `build_*/load_*`** ligados a IDs da auditoria.
- [Inventário auditável](mar-f01-functional-equivalence-inventory.json): 24 fluxos, dos quais **6 têm snapshot disponível no site** (sem aceite de UI), **12 possuem equivalência parcial**, e **6 não têm integração operacional equivalente**.
- [Matriz histórica reconciliada](mar-streamlit-vercel-functional-migration-matrix.md) distingue página pronta, dados agregados presentes, comportamento legado, direitos, atualização científica e lacunas.
- Site: arquivos Next.js e JSON históricos versionados. A estrutura estática atual não oferece diretamente operações seguras de Neon nem um `/admin` dinâmico.
- Segurança científica: comparação de dados agregados e metadados autorizados **não** confere direitos de mídia, admissão científica nem revisão de registros HOLD.

## Evidência de testes de correspondência — não é aceite funcional

| ID | Contrato verificado | Evidência automática | Limitação |
|---|---|---|---|
| M02 | 200 fichas KAVI: SHA da origem, identidade, título, ano, gêneros, assuntos, idioma, link à fonte e flags de mídia | `scripts/check_mar_f01_source_snapshot_parity.py` + `tests/test_mar_f01_source_snapshot_parity.py` + `scripts/check_mar_site_index.py` | Interface, revisão item a item e reprodução não aprovadas |
| M03 | Índice global e por corpus: 60 fontes históricas, três unidades restritas adicionais, totalizadores, versão da regra e bloqueio de fichas | Mesmo checker + testes adversariais | O índice é fotografia histórica; não é monitoramento em tempo real |
| M19 | 17 casos excluídos: decisão/razão, categoria, próximo passo e fonte original | Mesmo checker + testes adversariais | A visualização não inclui a unidade automaticamente |
| M12 | 62 relatórios agregados: reconstrução semântica da fonte | `tests/test_mar_site_analytics_projector.py` + `tests/test_mar_real_site_projections_b2.py` | Não cobre todos os controles visuais ou exportações do Streamlit |
| B04 | Pacote de 34 projeções e replay ARCHIPOP em staging isolado | `tests/test_mar_archipop_real_b2_replay.py` + `tests/test_mar_real_site_projections_b2.py` | Não é admissão de corpus novo nem atualização pública automática |

O novo teste F01 usa falhas induzidas **apenas sobre cópias em memória**, sem alterar as fontes ou o site. Casos negativos verificam mudança de título KAVI, promoção indevida de mídia/direitos, SHA inconsistente, soma errada de corpus, fonte ausente, identificador duplicado, liberação de fichas e alteração de decisões curatoriais.

O **workflow Quality Checks** integra os verificadores de ordem, inventário e origem-versus-site; o resultado para o commit exato de fechamento deverá ser incluído no checkpoint da issue #128 antes de qualquer proposta de conclusão. Não transferir um sucesso observado em SHA anterior para outro commit.

## Desvios funcionais confirmados e destino previsto

| Desvio | Evidência/efeito | Etapa de remediação |
|---|---|---|
| Pesquisa global multidimensional vs catálogo KAVI | Streamlit tem dez filtros dimensionais, seleção de reprodução pública verificada, agrupamento e CSV de resultados; catálogo Next usa apenas KAVI autorizado e filtros de texto/década/tema/ordem | F09, com gates de direitos; **não** transportar metadados sob HOLD |
| Pesquisa por instituições | Filtros institucionais originais incluem integridade, visibilidade, segmento e regime; Next institucional usa texto, fonte e país | F09, apenas em dados autorizados |
| Vídeos e fichas detalhadas | O legado exibe links/tabelas individuais que não podem ser republicados automaticamente; o site atual entrega indicadores e perfis editados | F09/F10, revisão de origem e de direitos |
| Descoberta, fila científica, fechamento europeu | Camadas internas originais não são equivalentes ao site público; o destino correto envolve Python, Neon e administração protegida | F03, F04, F07, F10 |
| Histórico de execução e alertas | Séries do site são de coletas históricas, não estado de Jobs, checkpoints ou defasagem `scientific_epoch` versus `site_epoch` | F05, F06, F08, F11 |
| SEO e detalhes PT/EN/ES | Algumas rotas indexáveis possuem versões internacionais, mas isso não garante cobertura de todas as fichas, metadados e páginas detalhadas | F09 |
| Exports do legado | CSV agregado permitido não equivale à exportação de registros individuais com direitos não validados | Proibição intencional; não considerar erro de migração |
| Programa de liberação pública | Vercel privada e Streamlit preservado durante auditoria; nenhum deploy READY é autorização | F11–F13 |

## Checklist de revisão independente de F01

1. Verificar se a matriz e o JSON enumeram todos os fluxos operacionais reais e não descrevem páginas como prova de comportamento.
2. Conferir por amostragem cada grupo com o código de origem, a rota Next.js e os arquivos científicos, inclusive caminhos com HOLD.
3. Confirmar que testes positivos, negativos e checks do PR passaram no SHA exato.
4. Registrar aceite **do inventário e de seu plano de remediação**, não aceite da equivalência total nem da publicação dos corpora.
5. Garantir que cada lacuna crítica tenha etapa F03–F10 associada, sem criar trabalho paralelo e sem antecipar F02.
6. Revisar a ausência de alterações em Neon principal, SSO Vercel, Streamlit, fontes científicas congeladas e direitos.
7. Só depois de revisão e merge permitido adicionar evidências `impact`, `contracts`, `tests`, `negative_tests`, `functional_acceptance`, `rollback`, `review` e `migration_matrix` à F01 do manifesto, com URL, SHA de 40 caracteres e revisor humano; a issue #128 deve refletir o mesmo estado.

**Decisão atual:** F01 **PENDENTE de aceite independente**. F02–F13 bloqueadas; sem alteração de banco, corpus, Vercel ou publicação.
