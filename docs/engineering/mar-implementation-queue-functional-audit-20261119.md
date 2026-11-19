# MAR — fila única de implantação e auditoria F01

**Congelamento do escopo:** 19/11/2026. **Fonte canônica de status:** [GitHub issue #128](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/128). Este arquivo fixa o protocolo e as primeiras evidências; **não** manter uma segunda fila independente ou concorrente. A arquitetura-alvo está documentada em `mar-definitive-architecture-control-plane-20261119.md` (PR #127); a matriz funcional de base permanece `mar-streamlit-vercel-functional-migration-matrix.md`.

## Padrão obrigatório de engenharia

A [norma de engenharia F01–F13](mar-enterprise-engineering-standard-20261119.md) define DoR/DoD, revisão humana e distinção entre software aprovado, equivalência funcional, validação científica e publicação. O [manifesto executável](mar-implementation-stage-gates.json) e o verificador [scripts/check_mar_implementation_queue.py](../../scripts/check_mar_implementation_queue.py) implementam bloqueios estruturais no workflow Quality Checks. Resultado verde do CI **não encerra F01** nem aprova um corpus.

## Regra de serialização

**F00 concluído (fila registrada). F01 ATIVA. F02–F13 BLOQUEADAS.** Apenas uma etapa pode estar ativa. A criação de código ou de PR sem revisão não fecha uma etapa. O próximo item só é iniciado quando o anterior cumpre todos os testes, revisão e aceites, com registro na issue #128. Alterações de escopo funcional não entram antes de F13, mesmo que atraentes. Bloqueios de segurança/científicos implicam HOLD da etapa corrente, não atalho.

## Ordem bloqueante

| Etapa | Entrega | Critério mínimo de saída |
|---|---|---|
| F00 | Fila persistida e escopo congelado | Issue #128 criada; uma etapa ativa |
| **F01** | Matriz auditada Streamlit → Next.js/admin/Python/Neon | Todos os fluxos, origens, destinos, evidências de paridade e pendências classificados; revisão da matriz |
| F02 | Segurança P0 e recuperação | Prova isolada de restauração, segregação de credenciais, falha segura |
| F03 | Governança Neon do PR #99 | Revisão SQL/guards/roles, merge seguro e prova de autorização sem alterar direitos |
| F04 | Fila científica operacional | Sincronização idempotente a partir da fila Python; proveniência/HOLD/atores |
| F05 | Gerador integral de projeções | Mesma epoch em todas as projeções autorizadas, manifesto e rollback íntegro |
| F06 | Orquestração de atualização | Python → estado governado → staging → GitHub Actions, sem publicação automática |
| F07 | Área administrativa protegida | Acesso autorizado no servidor e leituras reais SELECT-only; acesso negado comprovado |
| F08 | Monitoramento operacional | Ciclos, falhas, diferença de epochs, últimas execuções, auditoria |
| F09 | Paridade final do site | Filtros, instituições, exportações permitidas, documentação, PT/EN/ES, mobile/a11y |
| F10 | Retomada europeia controlada | Cada instituição validada ou HOLD com evidência; APE continua bloqueado sem acesso |
| F11 | Teste E2E no projeto Vercel existente, protegido | Fluxo aprovado/HOLD, regressões, rollback, segurança e versão exata |
| F12 | Aceite integral e transição do Streamlit | Nenhum fluxo essencial perdido e retorno de versão documentado |
| F13 | Liberação pública sob consentimento explícito | Só após F12 e decisão humana; /admin continua privado |

## F01 — levantamento técnico inicial; ainda não homologado

A verificação de código identificou **5.425 linhas** em `app/streamlit_app.py`. O [inventário F01 completo desta rodada](mar-f01-functional-equivalence-inventory.json) liga **24 fluxos (20 do Streamlit, quatro de Python)** a arquivos existentes e às lacunas observadas. Todos os **20 renderizadores** e **18 helpers** top-level de interface têm vínculo auditável. Do total, seis fluxos possuem snapshots no site, 12 estão parciais e seis não têm integração operacional equivalente. **Nenhum tem aceite funcional independente registrado.** A tabela abaixo conserva 15 agrupamentos da triagem inicial como referência histórica; o JSON e a matriz funcional atualizada são as referências para a auditoria de 24 fluxos. “Destino” identifica rota ou camada esperada, **não** prova que o comportamento foi migrado.

| Fluxo Streamlit | Origem com linha de referência | Destino/camada previsto | Hipótese inicial | Prova necessária |
|---|---|---|---|---|
| Idiomas e formatação | `render_language_selector` L359 | Next.js PT/EN/ES | Parcial | Teste de navegação, rótulos, URLs e SEO por categoria |
| Pesquisa multidimensional | `render_research_tab` L1644; filtros L1690–1738 | `/acervo/`, `/comparar/` | Parcial | Paridade de filtros/campos/denominadores sem publicar HOLD |
| Visão geral e fontes | `render_observatory_overview_tab` L1887 | `/observatorio/` | Parcial | Paridade de cartões, séries e avisos científicos |
| Índice de acesso | Tabs do índice L2080–2151 | `/indice-acesso/` | Parcial | Contagens de 63 unidades e restrições preservadas |
| Histórico, sinais e métricas globais | L2182–2341 | `/series/`, `/comparar/`, área administrativa | Parcial | Séries reais, eventos e classificação de sinais |
| Descoberta e fila de novas fontes | L2399–2424 | Python + Neon + `/admin` | Pendente | Mesma fila determinística, estados e evidências |
| Fechamento europeu e restrições | L2814–3091 | Python + Neon + `/admin` | Pendente | Toda decisão de corpus, HOLD e justificativa rastreável |
| Histórico de ciclos e artefatos | L3162–3222 | Python + Neon + `/admin` | Pendente | Último ciclo, falha, checkpoint e epoch |
| Categorias, temas e instituição | `render_category_tab` L3252 | `/observatorio/`, `/temas/` | Parcial | Mesmos recortes/contagens e campo de origem |
| Painel por corpus | `render_panel_tab` L3603 | `/observatorio/[code]/` | Parcial | Relatórios, integridade e cruzamentos por corpus |
| Dados científicos detalhados | `render_data_tab` L4241 | `/temas/`, `/comparar/`, `/series/` | Parcial | Tabelas, filtros e exportação apenas agregada |
| Base de instituições | `render_base_tab` L4439 | `/instituicoes/`, `/observatorio/[code]/` | Parcial | Filtros institucionais e evidências em nível permitido |
| Detalhe de instituição | `render_institution_tab` L4612 | `/instituicoes/pesquisa/` | Parcial | Links à origem, status, observações e URLs autorizadas |
| Evidência KAVI / KUVI | `render_kavi_kuvi_metadata_tab` L4911; `render_kavi_direct_view` L5274 | `/acervo/`, `/acervo/kavi/[id]/` | Parcial | 200 metadados autorizados; direitos de reprodução não deduzidos |
| Navegação e oito abas por corpus | `render_corpus_tab` L5029–5273 | Várias rotas + admin | Parcial | Roteamento por fluxo e regressão de telas existentes |

### Evidências já vistas

- O código do site contém grupos `site/app/(pt)/` e `site/app/[lang]/`; isso prova organização de rotas, **não** cobertura de todos os filtros.
- A matriz histórica registra 200 fichas KAVI de metadados, 63 perfis históricos, 62 relatórios agregados e 17 casos; não equiparar essas contagens a fichas liberadas de outros corpora.
- A main já contém as travas B1/B2 de snapshots e a simulação com ARCHIPOP (PRs #121–#126), mas **não** comprova admissão de novo corpus real.
- O esquema `mar_corpora` e painel Streamlit administrativo foram testados em branch Neon isolada e continuam no PR #99; não tomar laboratório por banco de produção.
- Next.js ainda utiliza `output: "export"`; a rota administrativa dinâmica exigirá mudança específica em F07, depois dos gates de governança.

### F01 — próximos atos permitidos

1. Auditar chamadas de `app/streamlit_app.py` por fluxo, incluindo filtros, estados de acesso, downloads, links, operação, exclusões e telas internas.
2. Vincular cada fluxo a arquivo Next.js e origem científica (CSV/JSON/Neon quando existente), com testes por item.
3. Atualizar a matriz existente com ID, camada responsável, estado e evidência, sem alterar direitos ou expor dados.
4. Revisar discrepâncias entre o inventário histórico e a versão de código efetivamente em `main`.
5. Rodar testes de migração, segurança, filtros, permissões e regressões na mesma revisão; anexar SHA/CI à issue.
6. Somente após aceite, marcar F01 concluída e iniciar F02.

**Pontos de controle invariáveis:** não alterar Neon principal, credenciais, SSO Vercel, publicações individuais sob HOLD, 200 KAVI, fontes europeias ou execução de coleta nesta etapa. Esta documentação não é prova de teste concluído.
