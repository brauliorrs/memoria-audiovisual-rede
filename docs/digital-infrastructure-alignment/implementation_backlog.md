# Backlog técnico de implementação

## Fonte canônica

A prioridade executiva, a política dos 20 corpora e a sequência continental são mantidas em:

`docs/project/BACKLOG.md`

A auditoria que fundamenta o estado atual está em:

`docs/audit/platform_integration_expansion_audit_2026-08-05.md`

Este documento não cria uma segunda ordem de prioridades. Ele registra apenas o estado técnico das camadas de infraestrutura digital.

## Estado consolidado

| Camada | Estado | Implantado | Pendência operacional |
|---|---|---|---|
| Licença, citação e contribuição | implementada | `LICENSE`, `CITATION.cff`, `CONTRIBUTING.md` | release estável, DOI e revisão jurídica futura |
| Interface pública | implementada | quatro áreas principais, três idiomas, carregamento progressivo | auditoria manual, desempenho e responsividade |
| Corpus de referência | materializado | manifesto congelado com 58 entidades | nova versão apenas mediante mudança canônica |
| Corpus operacional | validado em escala controlada | 55 entidades ativas globais; Europeana, INA e BFI executados com sucesso | primeiro ciclo completo dos 55 corpora |
| IA experimental | implementada estruturalmente | contratos, armazenamento separado, feature flags, amostra, coleta sombra e integração fail-open | anotação humana, modelos avaliáveis e detecção sintética no nível de item |
| Produtos europeus | sincronizados | 54 ativos europeus, 118 registros na fila, validação obrigatória no CI | operação da sondagem e do gate |
| Indicadores de referência | materializados | nove indicadores, cobertura e proveniência | validação operacional viva e histórico longitudinal |
| Núcleo de dados e proveniência | implementado estruturalmente | modelos, IDs, evidências, integridade, persistência e revisão | materializar ledger e lotes reais |
| Memória longitudinal | implementada estruturalmente | snapshots, comparação e ciclos parciais | dois snapshots oficiais completos e comparáveis |
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

## T0A — preparação experimental de IA antes do ciclo

**Estado:** concluído estruturalmente e validado em execução controlada.

### Implementado

1. contratos versionados para as três dimensões e quatro tarefas operacionais de IA;
2. separação entre uso institucional de IA, triagem do observatório e vídeo gerado ou modificado por IA;
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

### Pendências que não bloqueiam T1

- anotação humana da amostra;
- integração de modelos probabilísticos ou LLMs;
- medição de desempenho;
- detecção de vídeo sintético no nível de item;
- ativação científica de qualquer componente.

## T1 — execução integral do organismo

**Estado:** validação controlada concluída; rodada integral dos 55 corpora é o próximo portão.

### Proteções implantadas

- seleção explícita de corpora por argumento;
- opção controlada para ignorar a sondagem global sem alterar o ciclo integral;
- timeout configurável por script de corpus;
- registro de timeout como falha auditável;
- continuidade para os corpora seguintes após falha ou timeout;
- coleta de IA somente após coleta e verificação oficiais bem-sucedidas;
- IA desligada por padrão e habilitada por tarefa;
- falhas da IA não alteram o código de saída do ciclo oficial;
- preservação de manifestos, resumos e artefatos mesmo em ciclos controlados com falha.

### Próxima execução

1. executar todos os 55 corpora ativos com o prelude global habilitado;
2. habilitar em modo sombra as tarefas institucionais e de triagem;
3. manter a detecção de vídeo sintético desligada até existir contexto por item;
4. registrar sucesso, falha, timeout e não avaliabilidade sem exclusão silenciosa;
5. registrar separadamente falhas e custos das tarefas experimentais;
6. atualizar manifesto, linha do tempo e resultados do ciclo;
7. verificar snapshots e observation keys por corpus;
8. preservar evidências para revisão e recálculo posterior.

### Critério de conclusão

Todos os 55 corpora aparecem no manifesto da mesma rodada com estado auditável. A conclusão do T1 não exige sucesso de 100% das fontes, mas exige que nenhuma seja omitida e que toda falha possua diagnóstico reproduzível.

## T2 — materialização científica operacional

**Estado:** posterior à rodada integral do T1.

### Já materializado

- manifesto do corpus de referência;
- inventário derivado;
- snapshot científico de referência;
- cobertura de referência;
- nove resultados de indicadores;
- registros canônicos de indicador e metodologia.

### Ainda não materializado nos caminhos operacionais

- `data/output/controlled_validation_summary.json`;
- `data/output/analytics/<snapshot>/snapshot_indicators.json`;
- `data/output/analytics/<snapshot>/manifest.json`;
- `data/output/analytics/<snapshot>/run.json`;
- `data/output/analytics/indicator_history.jsonl`;
- `data/digital_infrastructure/ledger.jsonl`;
- `data/digital_infrastructure/ingestion_batches.jsonl`.

### Ações

1. executar o workflow controlado com `europeana`, `ina` e `bfi` para os nove indicadores;
2. persistir cobertura, nove indicadores, sensibilidade, run e manifesto;
3. materializar o snapshot oficial derivado da rodada integral;
4. iniciar histórico append-only de indicadores;
5. materializar ledger e lotes de ingestão;
6. diferenciar na interface baseline de referência e execução operacional;
7. demonstrar que os produtos oficiais são idênticos com a IA desligada.

## T2A — validação pós-baseline dos componentes de IA

**Estado:** posterior ao ciclo e ao baseline oficial.

1. revisar humanamente a amostra inicial;
2. calcular precisão, revocação, F1 e matriz de confusão por tarefa;
3. medir falsos positivos e falsos negativos por idioma, continente e tipo de instituição;
4. avaliar estabilidade entre versões, custo, tempo e dependência de fornecedor;
5. decidir separadamente quais componentes podem ser ativados;
6. registrar metodologia e indicador somente após aprovação científica;
7. recalcular apenas os indicadores de IA usando as evidências armazenadas;
8. não repetir a coleta integral salvo insuficiência documentada das evidências.

## T3 — fila europeia

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

### Produtos ainda ausentes

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

A sequência canônica está no backlog principal:

0. consolidação do baseline;
1. Europa;
2. América do Norte;
3. América Latina e Caribe;
4. África;
5. Ásia;
6. Oceania.

A pesquisa de fontes pode ocorrer em paralelo. A ativação de novas ondas permanece bloqueada até a conclusão do ciclo integral, da materialização científica e da operacionalização segura da fila europeia.

## Fora do primeiro ciclo operacional

A coleta experimental de sinais de IA poderá acompanhar o ciclo. Permanecem fora do primeiro baseline oficial:

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
Concluído: regenerar e validar os produtos europeus
Concluído: T0A — contratos, armazenamento, flags, amostra e integração sombra
Concluído: validação controlada do T1 com Europeana, INA e BFI
1. Executar o ciclo integral dos 55 corpora ativos
2. Materializar o baseline oficial, analytics, histórico, ledger e lotes sem dependência da IA
3. Revisar a amostra e calcular métricas por idioma
4. Decidir ativações por componente
5. Recalcular somente os indicadores de IA com as evidências armazenadas
6. Executar sondagem e elegibilidade europeias
7. Abrir revisão curatorial controlada
```
