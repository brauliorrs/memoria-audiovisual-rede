# Backlog técnico de implementação

## Fonte canônica

A prioridade executiva, a política dos 20 corpora e a sequência continental são mantidas em:

`docs/project/BACKLOG.md`

A auditoria que fundamenta o estado atual está em:

`docs/audit/platform_integration_expansion_audit_2026-08-05.md`

Este documento não cria uma segunda ordem de prioridades. Ele registra apenas o estado técnico das camadas de infraestrutura digital.

A organização específica das validações de automação e IA é mantida em:

`docs/digital-infrastructure-alignment/mar_intelligence_and_ai_validation_roadmap.md`

## Estado consolidado

| Camada | Estado | Implantado | Pendência operacional |
|---|---|---|---|
| Licença, citação e contribuição | implementada | `LICENSE`, `CITATION.cff`, `CONTRIBUTING.md` | release estável, DOI e revisão jurídica futura |
| Interface pública | implementada | quatro áreas principais, três idiomas, carregamento progressivo | auditoria manual, desempenho e responsividade |
| Corpus de referência | materializado | manifesto congelado com 58 entidades | nova versão apenas mediante mudança canônica |
| Corpus operacional | auditavelmente concluído | 55 entidades ativas globais; T1 com 49 sucessos e 6 falhas auditáveis | manutenção e próximos ciclos longitudinais |
| Baseline operacional T2 | materializado e congelado | 55 corpora, matriz de cobertura, nove indicadores, ledger, lotes, histórico e manifesto | validação longitudinal em ciclos futuros |
| Inteligência/automação do MAR | em andamento — prioridade atual | contratos, armazenamento separado, feature flags, baselines de triagem e integração fail-open | validar detecção de acervo, vídeo público, tipo de superfície, resolução de item, pertencimento e observabilidade |
| IA institucional | em andamento | baseline contextual `institutional_ai_use` e protocolo de evidências públicas | validação humana consolidada e cobertura das superfícies examinadas |
| IA no conteúdo audiovisual | em andamento | Porta 1 calibrada, classes operacionais e Porta 2 implementada | candidatos reais em nível de item, pertencimento, acesso, vínculo da evidência e validação ecológica |
| Produtos europeus | sincronizados | 54 ativos europeus, 118 registros na fila, validação obrigatória no CI | operação da sondagem e do gate |
| Núcleo de dados e proveniência | materializado no baseline operacional | modelos, IDs, evidências, integridade, persistência, ledger e lotes | manutenção longitudinal e validação em novas rodadas |
| Memória longitudinal | implementada estruturalmente | snapshots, comparação, baseline oficial e histórico append-only | segundo snapshot oficial comparável |
| Publicação derivada | implementada estruturalmente | revisão, ativação e entrega pública em código | produtos ativos, workflow editorial e conexão ao observatório |
| API e catálogo de downloads | planejados | contratos e produtos de base disponíveis | implementação pública somente leitura |

## T0 — consistência canônica

**Estado:** concluído.

O corpus ativo global possui 55 entidades. Os produtos europeus contêm corretamente 54 corpora ativos, pois o AAPB pertence ao recorte norte-americano.

Concluído:

1. regeneração de registro, fila e resumo europeus;
2. confirmação de que os CSVs já correspondiam ao gerador canônico;
3. criação de `scripts/sync_europe_research_outputs.py`;
4. modo `--check` para detectar produtos desatualizados;
5. validação separada dos denominadores global e europeu;
6. bloqueio de corpora extraeuropeus no recorte europeu;
7. validação de códigos, ranking, camadas, versões e totais;
8. testes contra alteração indevida do denominador;
9. integração do check ao workflow `Quality Checks`;
10. classificação de `observatorio_fila_fechamento_europa.csv` como histórico.

## T0A — preparação experimental de automação/IA antes do ciclo

**Estado:** concluído estruturalmente; validação empírica permanece em andamento em T2A.

### Implementado

1. contratos versionados para dimensões e tarefas operacionais de automação/IA;
2. separação entre uso institucional de IA, inteligência/triagem do observatório e conteúdo audiovisual gerado ou modificado por IA;
3. registros imutáveis com identificador estável e versão;
4. proveniência para evidência, modelo, configuração, prompt ou classificador, duração, custo e erro;
5. armazenamento JSONL append-only separado do baseline oficial;
6. feature flags independentes e desligadas por padrão;
7. bloqueio de execução fora do modo sombra;
8. executor fail-open que não propaga falhas ao ciclo oficial;
9. manifesto próprio para início e encerramento da execução experimental;
10. baseline determinístico para comparação futura com modelos de IA;
11. amostra inicial canônica com APE, Europeana, INA, BFI, ARCHIPOP e AAPB;
12. validação automática da amostra no CI;
13. integração opcional ao `scripts/run_observatory_cycle.py`;
14. separação entre contexto institucional e detecção sintética no nível de item, versão ou segmento;
15. documentação do runtime em `ai_experimental_runtime.md`;
16. testes de contratos, flags, armazenamento, falhas, baselines, amostra e integração.

### Validação controlada concluída

O workflow `Controlled observatory cycle` executou Europeana, INA e BFI em 5 de agosto de 2026:

- corpora selecionados: 3;
- sucessos: 3;
- falhas: 0;
- registros de uso institucional de IA: 3;
- registros de triagem do observatório: 6;
- manifestos da execução experimental: 2;
- erros experimentais: 0;
- dependência do baseline oficial em relação à IA: não.

A execução identificou um sinal institucional de IA no INA pendente de revisão. A ausência de sinal em Europeana e BFI permanece classificada apenas como `not_identified_on_assessed_surfaces`.

## T1 — execução integral do organismo

**Estado:** auditavelmente concluído.

A rodada integral registrou os 55 corpora ativos:

- 55 corpora no manifesto;
- 49 sucessos;
- 6 falhas auditáveis;
- nenhuma exclusão silenciosa;
- conclusão definida por cobertura auditável, não por disponibilidade de 100% das fontes externas;
- portão canônico em `data/output/t1_auditable_completion.json`.

As proteções de timeout, continuidade após falha, preservação de artefatos e independência das tarefas experimentais permanecem válidas para os próximos ciclos.

## T2 — materialização científica operacional

**Estado:** oficialmente materializado e congelado.

O baseline operacional foi produzido com a IA experimental desligada e contém:

- 55 corpora ativos;
- matriz operacional de 385 estados de cobertura;
- nove indicadores oficiais;
- ledger e lotes de ingestão;
- artefatos brutos e proveniência;
- histórico append-only de indicadores;
- manifesto operacional com hashes SHA-256;
- ponteiro canônico para o baseline vigente;
- dependência da IA experimental: não.

T2 não deve ser reaberto para acomodar resultados experimentais de T2A. Mudanças futuras pertencem a novos ciclos/snapshots ou a artefatos experimentais separados.

## T2A — validação pós-baseline dos componentes de automação/IA

**Estado:** em andamento.

A ordem de prioridade interna de T2A passa a ser:

1. **inteligência/automação do MAR**;
2. **IA institucional**;
3. **IA na produção/modificação de conteúdo audiovisual**.

### Inteligência/automação do MAR — prioridade atual

No código, parte dessa camada aparece como `observatory_ai_triage`. A expressão metodológica preferida é **inteligência/automação do MAR**, pois os mecanismos podem ser regras determinísticas, heurísticas ou modelos de IA.

Validar em amostra humana:

1. detecção de acervo audiovisual;
2. detecção de vídeo público;
3. classificação do tipo de superfície observada;
4. distinção entre página geral, índice, notícia, ficha de item e item/versão/segmento audiovisual;
5. resolução de URL específica de item quando a tarefa exigir unidade em nível de item;
6. pertencimento do item ao corpus observado;
7. observabilidade pública da superfície do item;
8. preservação do vínculo entre item, corpus, snapshot, URL e evidência.

### Primeira revisão da Porta 2

A primeira fila real de candidatos da Porta 2 continha ECPAD e INA. Nos dois casos, a URL selecionada não correspondia a item, versão ou segmento audiovisual:

- ECPAD: página geral de arquivos;
- INA: página institucional/principal com links para outras áreas do acervo.

Resultado metodológico: **0/2 URLs candidatas eram unidades audiovisuais elegíveis em nível de item**.

Esse resultado:

- não prova ausência de IA;
- não prova ausência de acervo audiovisual;
- não avalia pertencimento, acesso público específico ou vínculo de evidência, porque o fluxo foi interrompido no primeiro teste;
- revela uma limitação da seleção/resolução de URLs pelo gerador de candidatos;
- justifica priorizar a inteligência/automação do MAR antes de repetir a Porta 2 em escala.

### IA institucional — em andamento

1. manter o baseline contextual e os registros já produzidos;
2. definir e registrar cobertura das superfícies públicas examinadas;
3. revisar positivos e amostra de negativos;
4. distinguir pesquisa, piloto, anúncio e operação;
5. não publicar ausência institucional a partir de não detecção;
6. só ativar indicador após metodologia, cobertura, denominador e revisão humana suficientes.

### IA no conteúdo audiovisual — em andamento

1. preservar a Porta 1 como validada apenas para identificação terminológica/contextual na versão atual;
2. melhorar a geração de candidatos em nível de item;
3. validar sequencialmente item, pertencimento, acesso público e vínculo da evidência;
4. validar classes de participação de IA em itens reais do corpus;
5. calcular métricas apenas quando houver unidades humanas concluídas e avaliáveis;
6. recalcular somente indicadores experimentais de IA, sem alterar o baseline oficial.

### Regra de ativação

Nenhuma dimensão experimental de IA será promovida a indicador científico apenas por existir em código. Cada componente precisa de população elegível, metodologia versionada, cobertura, evidência, revisão humana e métricas apropriadas à sua tarefa.

## T3 — fila europeia

**Estado:** em andamento.

### Fila vigente

`data/output/observatorio_fila_pesquisa_europa.csv`

- 118 registros;
- 24 campos;
- regra `2026-05-pesquisa-europa-v3`;
- cinco fontes de descoberta no início;
- 73 candidatos individuais na fila definitiva;
- 30 agregadores nacionais ou regionais em radar;
- oito agregadores temáticos em radar contextual.

### Código já existente

- `src/memoria_audiovisual/digital_infrastructure/european_queue.py`;
- `src/memoria_audiovisual/digital_infrastructure/queue_probe.py`;
- `src/memoria_audiovisual/digital_infrastructure/eligibility.py`;
- `scripts/probe_european_queue.py`;
- `scripts/evaluate_european_queue.py`;
- testes de sondagem e elegibilidade.

### Produtos ainda ausentes ou a operacionalizar

- `observatorio_sondagem_tecnica_fila_europa.json`;
- `observatorio_elegibilidade_fila_europa.json`;
- `observatorio_elegibilidade_fila_europa.csv`;
- workflow manual e reiniciável;
- lote de revisão curatorial;
- exposição dos estados do gate na interface.

### Regra de segurança

A fila pode sondar, avaliar e priorizar. Ela não pode:

- promover automaticamente candidatos;
- alterar `CORPORA`;
- alterar `organism_active`;
- automatizar a decisão curatorial;
- publicar candidatos como corpus científico.

## T4 — política dos 20 corpora

**Estado:** em andamento.

A implementação deve contar somente unidades:

- elegíveis;
- aprovadas;
- validadas;
- não duplicadas;
- sem bloqueio de integridade;
- com decisão curatorial concluída.

Fontes de descoberta, radar, negativas, pendências e não avaliáveis não contam.

Componentes pendentes:

1. contador por continente;
2. simulação com a fila europeia;
3. relatório de prontidão;
4. prazo máximo sem atingir 20;
5. regra proporcional para regiões menores;
6. tratamento de fontes transcontinentais;
7. integração com snapshots, indicadores e publicação.

## T5 — publicação derivada

**Estado:** em andamento.

Código estrutural existente:

- `public_view.py`;
- `publication_revision.py`;
- `active_publication.py`;
- `public_delivery.py`.

Pendências:

1. definir raiz pública canônica;
2. materializar publicações ativas e histórico;
3. criar portão editorial e workflow de ativação;
4. gerar eventos e manifesto de entrega;
5. conectar apenas publicações aprovadas ao observatório;
6. implementar API somente leitura e catálogo de downloads em ciclo posterior.

## T6 — expansão continental

**Estado:** em andamento sob os portões de ativação já definidos.

A sequência canônica está no backlog principal:

0. consolidação do baseline;
1. Europa;
2. América do Norte;
3. América Latina e Caribe;
4. África;
5. Ásia;
6. Oceania.

A pesquisa de fontes pode ocorrer em paralelo. A ativação de novas ondas permanece bloqueada até a conclusão dos portões operacionais e curatoriais correspondentes.

## Fora do baseline oficial congelado

Permanecem fora do T2 oficial:

- ativação pública dos indicadores de IA;
- decisões automáticas baseadas em previsões de IA;
- inferência automática de contratos;
- classificação autônoma de riscos por IA;
- publicação de dados pessoais;
- coleta em áreas autenticadas;
- promoção automática de candidatos;
- integração com fontes juridicamente não avaliadas;
- indicadores novos sem metodologia, cobertura e validação.

## Próximo portão técnico

```text
Concluído: T0 — consistência canônica
Concluído: T0A — preparação estrutural experimental
Concluído: T1 — execução auditável dos 55 corpora
Concluído: T2 — baseline operacional materializado e congelado
Prioridade atual: T2A — validar a inteligência/automação do MAR
1. Validar detecção de acervo audiovisual e vídeo público em amostra humana
2. Validar tipo de superfície e resolução de URL em nível de item
3. Corrigir o gerador quando páginas gerais forem selecionadas para tarefas item-level
4. Validar pertencimento ao corpus e observabilidade pública
5. Preservar IA institucional como em andamento, sem ativação científica prematura
6. Preservar IA no conteúdo como em andamento e retomar Porta 2 após candidatos item-level confiáveis
7. Prosseguir T3–T6 sob seus portões próprios, sem reabrir T1/T2
```
