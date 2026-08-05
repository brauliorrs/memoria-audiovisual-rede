# Eixo executivo — integração operacional e expansão

## Finalidade

Este plano registra a ordem obrigatória entre interface, artefatos científicos, ciclos operacionais, filas de expansão e publicação. O estado detalhado da auditoria está em:

`docs/audit/platform_integration_expansion_audit_2026-08-05.md`

O backlog executivo vigente está em:

`docs/project/BACKLOG.md`

## Regras permanentes de integração

1. A interface pública é integrada diretamente em `app/streamlit_app.py` e nos módulos importados por ele.
2. GitHub Actions pode validar, executar, materializar e publicar artefatos, mas não deve ser o mecanismo permanente de edição do código-fonte da interface.
3. Coleta, sondagem técnica, elegibilidade científica, decisão curatorial e incorporação em `CORPORA` são etapas separadas.
4. Nenhuma fila promove automaticamente candidatos para `CORPORA` ou altera `organism_active`.
5. Ausência de artefato operacional deve ser apresentada como ausência ou não execução, nunca como resultado empírico.
6. Corpus de referência, corpus operacional global, recortes continentais, fontes de descoberta, radar e fila incorporável possuem denominadores distintos.
7. Produtos públicos devem derivar de snapshots e publicações aprovadas, não de observações ainda não revisadas.

## Estado auditado em 5 de agosto de 2026

### Etapa 1 — Infraestrutura científica na interface

**Estado: concluída estruturalmente.**

A seção está integrada à aplicação e disponível em português, inglês e espanhol, com carregamento progressivo e navegação principal leve.

### Etapa 2 — Catálogo, metodologia e resultados de referência

**Estado: concluída para o corpus científico de referência.**

Existem:

- registro canônico de nove indicadores;
- registro metodológico;
- manifesto congelado com 58 entidades;
- snapshot de cobertura;
- nove resultados materializados com proveniência;
- auditorias de consistência e integridade.

Esses produtos formam um baseline de referência. Eles não substituem um ciclo operacional completo dos corpora ativos.

### Etapa 3 — Carregadores, snapshots e proveniência

**Estado: implementada estruturalmente.**

A interface possui carregadores para:

- resultados e manifestos analíticos;
- cobertura;
- sensibilidade;
- histórico de indicadores;
- ledger;
- lotes de ingestão.

Ainda não estão materializados nos caminhos operacionais canônicos:

- `data/output/analytics/indicator_history.jsonl`;
- `data/digital_infrastructure/ledger.jsonl`;
- `data/digital_infrastructure/ingestion_batches.jsonl`.

### Etapa 4 — Validação controlada

**Estado: workflow implementado; execução operacional não consolidada.**

O workflow de validação controlada prevê:

- `europeana`, `ina` e `bfi`;
- cobertura verificável;
- nove indicadores;
- análise de sensibilidade;
- manifesto e run.

O produto `data/output/controlled_validation_summary.json` ainda não está materializado na branch auditada.

### Etapa 5 — Atualização integral dos corpora atuais

**Estado: próxima prioridade executiva.**

O corpus científico possui 58 entidades, das quais 55 estão ativas globalmente. O último ciclo, concluído em 21 de julho de 2026, foi parcial e processou somente `home-movies-memoryscapes`.

Não existe ciclo completo materializado para os 55 corpora ativos.

### Etapa 6 — Produtos e fila europeus

**Estado dos produtos canônicos: sincronização concluída.**

Os três produtos europeus foram regenerados e permaneceram inalterados:

- `observatorio_pesquisa_europa.csv`;
- `observatorio_fila_pesquisa_europa.csv`;
- `observatorio_resumo_pesquisa_europa.csv`.

O denominador foi validado como:

```text
55 ativos globais = 54 ativos europeus + AAPB
```

O sincronizador `scripts/sync_europe_research_outputs.py` e o passo obrigatório do CI protegem os três arquivos contra desatualização, duplicidade, ranking descontínuo, mistura de versões e entrada indevida de corpora extraeuropeus.

**Estado da operação da fila: pendente.**

A fila vigente contém 118 registros, separa fontes de descoberta de candidatos individuais e possui ranking explícito.

Existem código e testes para:

- sondagem técnica;
- enriquecimento verificável;
- gate de elegibilidade;
- exportação de avaliações.

Ainda não existem produtos materializados de sondagem e elegibilidade, workflow operacional da fila ou lote de revisão curatorial.

A fila antiga `observatorio_fila_fechamento_europa.csv` deve ser tratada como histórico, não como fila vigente.

## Política multilíngue

O bloqueio anterior dos catálogos inglês e espanhol foi superado. A interface principal e a Infraestrutura Científica já operam nos três idiomas.

A obrigação atual é manter auditoria de consistência e impedir regressões, não retornar ao bloqueio de internacionalização.

## Sequência continental provisória

A descoberta pode ocorrer em paralelo, mas a ativação de novas ondas segue:

0. consolidação do baseline atual;
1. Europa;
2. América do Norte;
3. América Latina e Caribe;
4. África;
5. Ásia;
6. Oceania.

Fontes mundiais, supranacionais e transcontinentais permanecem em fila transversal e não contam automaticamente para o limiar de um continente.

A sequência só pode ser alterada mediante inventário comparável, justificativa científica e registro da decisão. Facilidade técnica isolada não constitui justificativa suficiente.

## Ordem executiva autorizada

1. executar o ciclo completo dos 55 corpora ativos globais;
2. materializar validação controlada, analytics operacional, histórico, ledger e lotes;
3. operacionalizar a sondagem e o gate da fila europeia;
4. criar revisão curatorial sem promoção automática;
5. simular e automatizar a política dos 20 corpora;
6. fechar a onda europeia;
7. consolidar a América do Norte;
8. preparar a fila da América Latina e Caribe.

## Bloqueios atuais

Até a conclusão das etapas anteriores, a plataforma não deve:

- ativar uma nova onda continental;
- promover candidatos automaticamente;
- recalcular índices publicados com denominadores não congelados;
- misturar fontes de descoberta com corpora elegíveis;
- apresentar snapshots de referência como ciclo operacional vivo;
- publicar observações sem revisão e ativação formal.

## Próxima ação autorizada

Preparar e executar o primeiro ciclo integral dos 55 corpora ativos globais. A operação da fila europeia permanece posterior à materialização desse baseline operacional completo.
