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
| Corpus operacional | ativo parcialmente | 55 entidades ativas globais | primeiro ciclo completo dos 55 corpora |
| Produtos europeus | sincronizados | 54 ativos europeus, 118 registros na fila, validação obrigatória no CI | operação da sondagem e do gate |
| Indicadores de referência | materializados | nove indicadores, cobertura e proveniência | validação operacional viva e histórico longitudinal |
| Núcleo de dados e proveniência | implementado estruturalmente | modelos, IDs, evidências, integridade, persistência e revisão | materializar ledger e lotes reais |
| Memória longitudinal | implementada estruturalmente | snapshots, comparação e ciclos parciais | dois snapshots oficiais completos e comparáveis |
| Publicação derivada | implementada estruturalmente | revisão, ativação e entrega pública em código | produtos ativos, workflow editorial e conexão ao observatório |
| API e catálogo de downloads | planejados | contratos e produtos de base disponíveis | implementação pública somente leitura |

## T0 — consistência canônica

**Estado:** concluído nesta rodada.

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

## T1 — execução integral do organismo

**Estado:** próximo portão técnico.

1. executar todos os 55 corpora ativos em um ciclo completo;
2. registrar sucesso, falha e não avaliabilidade sem exclusão silenciosa;
3. atualizar manifesto, linha do tempo e resultados do ciclo;
4. verificar snapshots e observation keys por corpus;
5. congelar o primeiro baseline operacional completo.

## T2 — materialização científica operacional

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

1. executar o workflow controlado com `europeana`, `ina` e `bfi`;
2. persistir cobertura, nove indicadores, sensibilidade, run e manifesto;
3. iniciar histórico append-only de indicadores;
4. materializar ledger e lotes de ingestão;
5. diferenciar na interface baseline de referência e execução operacional.

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
1. Executar o ciclo completo dos 55 corpora ativos globais
2. Materializar analytics, histórico, ledger e lotes
3. Executar sondagem e elegibilidade europeias
4. Abrir revisão curatorial controlada
```
