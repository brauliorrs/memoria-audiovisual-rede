# MAR — auditoria de equivalência Streamlit → Next.js e retomada da etapa europeia

**Data da auditoria:** 18/11/2026 (America/Fortaleza)  
**Base verificada:** `main` `a120102798467f67d8c9b8d905e1378e7b5fbf35`; projeto Vercel preexistente `mar-public-site` (`prj_ynSzKPjTZ4dvgermfa86UcyZN1ou`).  
**Natureza:** auditoria estática de código, datasets versionados, workflows, GitHub Actions e registros de deployment. **Não é validação visual/browser end-to-end nem autorização científica.**

## 1. Veredicto

**Migração funcional: avançada, porém incompleta.** Já existe interface pública de pesquisa, mas não foi demonstrado o ciclo íntegro **novo corpus científico → snapshots versionados → projeções web → verificação de equivalência → publicação autorizada**. Não desativar o Streamlit nem chamar a migração de concluída.

A experiência pública e o motor interno precisam continuar separados:
- **Fonte analítica/científica**: `src/memoria_audiovisual/`, `data/output/`, workflows e Streamlit; há muitos corpora inventariados, mas isso **não constitui autorização para publicar fichas**.
- **Produto web**: `site/`, Next.js em `output: "export"`; serve arquivos e indicadores estáticos, sem coleta ou Neon em tempo de execução.
- **Metadados individuais aprovados no site**: somente 200 KAVI/Finna; direitos e reprodução da mídia não verificados. Não publicar documentos, mídia, IDs ou URLs de corpora sob HOLD com base no inventário histórico.

## 2. Matriz de paridade, fundamentada em código

| Experiência de referência no Streamlit | Equivalência no Next.js | Diagnóstico e aceite |
|---|---|---|
| Visão institucional e apresentação | `/`, `/instituicoes/`, `/metodologia/` | Implementado; revisar acessibilidade, dispositivos e conteúdo final |
| Pesquisa pública KAVI | `/acervo/`, `/acervo/kavi/[id]/`, `/instituicoes/kavi/` | Implementado: 200 fichas admitidas; **não** significa corpus KAVI integral incorporado |
| Observatório e categorias | `/observatorio/`, `/observatorio/[code]/` | Implementado: 63 perfis históricos, vários níveis de detalhamento |
| Relatórios por corpus | `/analises/` e painel por fonte | Implementado: síntese de 62 relatórios históricos; verificar paridade com tabelas especializadas |
| Temas, país, plataforma e tipo | `/temas/`, `/pesquisa/[code]/`, `/comparar/` | Agregados implementados; não inferir cruzamentos não observados |
| Geografia e séries | `/territorios/`, `/series/` | Agregados e snapshots implementados; não são tempo real, nem localização de obras |
| Comparação multícorpus | `/comparar/` | Até três fontes, permalink e CSV **agregado**; recortes avançados Streamlit ainda exigem inspeção de equivalência |
| Casos documentados | `/casos/` | 17 casos; evidências literais preservadas |
| Instituições e fichas institucionais | `/instituicoes/pesquisa/` e rotas de entrada | Navegação e perfis implementados; faltam listas institucionais completas, atualização e drill-down equivalente aos oito painéis Streamlit |
| Inventário de acesso | `/indice-acesso/` | 63 unidades, 194.057 registros **classificados historicamente**; não são fichas publicadas |
| Nuvem temática de títulos | `site/data/title-wordcloud.json` | Estatística versionada; workflow de atualização por PR **somente da nuvem** |
| Coleta, pesquisa europeia, fila de expansão, ciclos mensais, exceções e fechamento | Sem superfície Next.js equivalente demonstrada | **Pendente**: painel informativo de governança, somente dados agregados públicos; operações restritas devem permanecer privadas |
| Pesquisa global detalhada: 10 filtros, vídeos por instituição, tabelas longas e exportações | Cobertura distribuída entre catálogo e análises | **Parcial**: reproduzir filtros e tabelas permitidos; não transformar dados HOLD em catálogo público |
| Idiomas e SEO | 14 rotas estáticas PT/EN/ES; rotas individuais existentes | 42 páginas linguísticas com HTML independente e `hreflang` na `main`; fichas KAVI e páginas dinâmicas **não** possuem equivalentes individuais indexáveis por idioma |

**Fontes principais:** [Streamlit 5.425 linhas](https://github.com/brauliorrs/memoria-audiovisual-rede/blob/main/app/streamlit_app.py), [matriz funcional](https://github.com/brauliorrs/memoria-audiovisual-rede/blob/main/docs/engineering/mar-streamlit-vercel-functional-migration-matrix.md), [Next.js](https://github.com/brauliorrs/memoria-audiovisual-rede/tree/main/site), [PR #119](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/119).

## 3. Lacunas de infraestrutura e dados — prioridade P0/P1

1. **Acesso público real não atestado.** Vercel: implantação de `main` marcada `READY`; SSO informado como ativo para domínios `vercel.app`. É necessário testar anonimamente a URL canônica **https://mar-public-site.vercel.app/**, rotas principais, `/en/`, `/es/`, `/sitemap.xml` e `/robots.txt`. `READY` não prova navegação pública.
2. **Ausência de ponte integral de atualização científico→web.** O arquivo `site/next.config.ts` define `output: "export"`. O ciclo mensal `.github/workflows/organism-monthly.yml` executa a coleta existente e envia `data/output/` como artifact, **não publica por si só um snapshot revisado no repositório**. Os arquivos `site/data/*` são projeções versionadas; não há gate integrado comprovado que atualize todos os 63 perfis, 62 relatórios, índices e projeções após admissão de um novo corpus. A nuvem é exceção parcial: `mar-wordcloud-refresh.yml` propõe PR agregado.
3. **Paridade entre fontes e projeções.** Antes de incorporar o próximo corpus, criar gerador determinístico e verificações de schema, quantidade, versão, datas, hashes, IDs e diferenças entre outputs de origem e `site/data`. Falha segura quando há falta de autorização ou corpus sem saída revisada; zero publicação individual implícita.
4. **Painéis não migrados.** Transportar para páginas ou relatórios de governança somente leituras públicas e agregadas do ciclo mensal, protocolos de restrição, fila científica europeia e fechamento. Controle e validação de inclusão permanecem fora da interface pública, sem botão de coleta/publicação.
5. **Testes E2E/visuais e acessibilidade.** GitHub Actions aprovam contratos, typecheck e build estático, mas isso não substitui testes HTTP anônimos, navegação móvel, teclado, idioma/canônicas e comparação humana do Streamlit com o Next.js.

## 4. Estado europeu e contradições a reconciliar

- O dossiê histórico `observatorio_dossie_fechamento_europa.md` usa regra **2026-05**, registra **54 corpora europeus ativos** e abertura de etapa continental seguinte `autorizada_com_cautela`. Isso registra uma **decisão metodológica histórica**, não a conclusão auditada em novembro.
- O observatório web indexa **63 corpora/unidades** (categorias globais/históricas); as 62 sínteses, os 63 perfis, os 194.057 registros históricos e as 200 fichas KAVI possuem **denominadores diferentes**. Não somar como fichas publicadas.
- **APE**: 412 entradas do inventário histórico não equivalem a 412 fichas APE publicáveis. Em novembro, a política geral de metadados **CC BY-SA 4.0, salvo exceções**, foi localizada; continuam pendentes atribuição por provedor, checagem de exceções e licenças individualizadas. **HOLD de publicação**.
- **Europeana**: 20 entradas auditadas, com política de **CC0 para metadados Europeana**, distinta dos direitos da mídia e sujeita à confirmação da proveniência. **Não promover automaticamente**.
- **Eye/Czech**: o [PR #105](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/105) contém staging e auditoria offline (**Eye 630**, **Czech 10**) e amostras limitadas; continua **aberto**, sem aprovação G2/G3/G4 nem liberação de fichas.
- **CICLIC, Bundesarchiv, ASIM, BNFA**: há documentos G0/G1 recentes, mas partes da consulta são limitadas por ambiente, redirecionamento, autenticação ou agregador; nenhuma ficha nova liberada. 403/timeout de ferramenta **não** é prova de inacessibilidade ao público.
- **KAVI nº 82**: 200 fichas documentais **parciais** aprovadas para o site coexistem com decisão anterior **HOLD de admissão do corpus integral** no [PR #71](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/71). O arquivo `observatorio_proximos_candidatos_inclusao.json` ainda lista KAVI como próximo candidato nº 82 e Macedônia do Norte nº 83. Reconciliar fila e decisão antes de afirmar que a próxima fonte está definida.
- O registro `corpus_admission_engine.py` possui cinco conectores sob contrato; `approved_corpus_admission.py` exige CSV, manifesto, SHA-256 e revisão. **Registro técnico ≠ corpus admitido ≠ ficha autorizada**.
- O último ciclo mensal versionado inspecionado (`observatorio_ciclo_mensal.json`) é de **21/07/2026**, parcial, com um corpus selecionado. Não usar como prova de atualização longitudinal global em novembro.

**Evidência novembro:** [rodada de acesso G0/G1](https://github.com/brauliorrs/memoria-audiovisual-rede/blob/main/docs/engineering/mar-public-access-g1-survey-wave-20261118.md), [dossiê europeu](https://github.com/brauliorrs/memoria-audiovisual-rede/blob/main/data/output/observatorio_dossie_fechamento_europa.md), [motor de admissão](https://github.com/brauliorrs/memoria-audiovisual-rede/blob/main/src/memoria_audiovisual/corpus_admission_engine.py).

## 5. Ordem de execução e aceite

### Marco A — estabilização da migração pública (P0)
- [ ] Validar HTTP sem autenticação e comportamento real do domínio canônico; não criar projetos ou domínios alternativos.
- [x] Confirmar no GitHub `main` os testes `MAR Next.js Site` e `Quality Checks` verdes para o commit-base acima.
- [x] Confirmar no Vercel deployment do mesmo SHA como `READY` (sem alegar acesso público).
- [ ] Fazer auditoria visual, responsiva e de acessibilidade PT/EN/ES; preservar rotas antigas e dados científicos.

### Marco B — equivalência científica e atualização contínua (P0)
- [ ] Criar projeção versionada, reproduzível e testada para atualizar o site após corpus científico efetivamente admitido.
- [ ] Testar deltas de corpus, contagens, dimensões, hash, datas, direitos e estados HOLD; nada de liberação implícita.
- [ ] Reconciliar as 63 fontes, 62 relatórios e títulos da nuvem com artefatos de proveniência; produzir relatório de divergências.
- [ ] Transportar tabelas e recortes do Streamlit cuja publicação de agregados seja legítima; manter fichas restritas fora.
- [ ] Criar documentação pública da operação (último ciclo e estado das fontes) sem expor segredos/credenciais.

### Marco C — fechamento científico europeu (P1)
- [ ] Atualizar relatório europeu e fila a partir dos dados científicos atuais; distinguir cortes 2026-05, 2026-06 e 2026-11.
- [ ] Rever individualmente APE, Europeana, Eye, Czech, CICLIC, Bundesarchiv, ASIM e BNFA; registrar G0–G4 e motivos HOLD.
- [ ] Reconciliar posição KAVI nº 82, decisão HOLD integral e próximo candidato nº 83.
- [ ] Criar decisão assinável por corpus: incorporado analiticamente, protocolado/HOLD ou admitido para publicação de metadados.
- [ ] Aprovar formalmente dossiê de fechamento europeu com limites, amostragem, fontes, revisão e critérios para novo continente.

### Marco D — retomada de novos corpora (P1, condicionada)
- [ ] Selecionar um candidato cujo G0/G1 tenha evidência suficiente, respeitar robots/termos, sondagem limitada e sem mídia.
- [ ] Validar pipeline, deduplicação, checkpoints, integridade, revisão independente e compatibilidade de schema.
- [ ] Incorporar **primeiro no fluxo científico**, após aceite específico; atualizar o site **somente** pelas projeções publicáveis aprovadas.
- [ ] Confirmar que Streamlit e site concordam nos indicadores revisados sem conflitar com congelamentos científicos ou P0/Neon.

## 6. Fora de escopo desta auditoria

Nenhuma coleta, alteração de corpus, merge de PR científico, publicação de novas fichas, migração Neon, liberação de HOLD, modificação do Streamlit, criação de domínio/projeto Vercel, mudança de proteção SSO ou gasto novo. Uma auditoria estática não comprova equivalência de comportamento em navegação real.

**Porta de saída:** a migração só poderá ser declarada concluída depois de evidenciar os marcos A e B. A etapa europeia exige adicionalmente C; a expansão de corpus exige D, com aprovação por fonte.
