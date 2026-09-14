# T2 — baseline operacional oficial

## Objetivo

O T2 transforma as estruturas científicas já implementadas em produtos operacionais versionados, verificáveis e carregáveis pela plataforma. A execução ocorre somente depois do portão auditável do T1, que exige resultado explícito para todos os 55 corpora ativos.

## Dependência do T1

O arquivo `data/output/t1_auditable_completion.json` registra o primeiro ciclo integral:

- 55 corpora ativos;
- 55 resultados registrados;
- 49 sucessos;
- 6 falhas auditáveis preservadas;
- hash SHA-256 do manifesto original;
- sinais experimentais de IA separados do baseline oficial.

Falhas externas não são convertidas em sucesso. O portão verifica cobertura integral e ausência de exclusão silenciosa.

## Produtos do T2

A execução materializa:

1. `data/output/operational_baseline_execution.json` — resumo da auditoria operacional;
2. `data/digital_infrastructure/coverage/<snapshot>/parameter_coverage.json` — matriz de 385 estados para 55 corpora e sete grupos de detecção;
3. `data/output/analytics/<snapshot>/snapshot_indicators.json` — nove resultados oficiais;
4. `data/output/analytics/<snapshot>/manifest.json` — manifesto analítico com hash;
5. `data/output/analytics/<snapshot>/run.json` — registro da execução;
6. `data/output/analytics/<snapshot>/interoperability_sensitivity.json` — análise de sensibilidade;
7. `data/output/analytics/indicator_history.jsonl` — histórico append-only;
8. `data/digital_infrastructure/ledger.jsonl` — ledger de entidades, evidências e proveniência;
9. `data/digital_infrastructure/ingestion_batches.jsonl` — histórico retomável dos lotes;
10. `data/output/analytics/<snapshot>/operational_baseline_manifest.json` — manifesto imutável que referencia todos os produtos e seus hashes;
11. `data/output/operational_baseline_latest.json` — ponteiro verificável para o baseline operacional vigente.

## Independência da inteligência artificial

Todas as flags experimentais de IA devem permanecer desligadas durante a materialização oficial:

- `MAR_AI_EXPERIMENTS_ENABLED`;
- `MAR_AI_INSTITUTIONAL_USE_ENABLED`;
- `MAR_AI_COLLECTION_DETECTION_ENABLED`;
- `MAR_AI_VIDEO_PRESENCE_ENABLED`;
- `MAR_AI_SYNTHETIC_VIDEO_ENABLED`.

O materializador interrompe a execução se qualquer uma dessas flags estiver ativa. Os nove indicadores oficiais são calculados sem dependência dos registros experimentais de IA.

## Critérios de validação

O baseline somente recebe estado `completed` quando:

- o portão T1 é válido e registra 55 resultados;
- a auditoria executa em modo `ledger` sobre os 55 corpora ativos;
- a matriz contém 385 estados de cobertura;
- existe exatamente um lote identificado por corpus;
- todos os lotes terminam em estado `completed`;
- o ledger contém transações válidas e não duplicadas;
- os nove indicadores e o `run.json` estão concluídos;
- o hash do manifesto analítico corresponde ao arquivo de indicadores;
- o histórico append-only existe;
- todas as flags experimentais de IA estão desligadas;
- todos os artefatos recebem hash SHA-256 no manifesto operacional;
- o ponteiro `latest` identifica o snapshot e o hash do manifesto imutável vigente.

## Workflow

O workflow `T2 operational baseline` executa a auditoria dos 55 corpora, materializa os produtos, valida a integridade, envia um artefato completo e registra os resultados na branch `presentation/rpv-1`.
