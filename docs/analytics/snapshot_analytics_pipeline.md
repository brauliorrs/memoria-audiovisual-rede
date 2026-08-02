# Pipeline analítico por snapshot

## Objetivo

Conectar a matriz consolidada `parameter_coverage.json` ao motor analítico sem reabrir a coleta, alterar observações ou modificar produtos históricos.

## Fluxo

```text
parameter_coverage.json
→ validação de snapshot e unicidade
→ IndicatorContext
→ IndicatorRegistry
→ AnalyticsEngine
→ AnalyticsRun
→ AnalyticsStore
```

## Indicadores nativos iniciais

- `api_coverage@1.0.0`;
- `interoperability_coverage@1.0.0`.

O conjunto nativo é declarado explicitamente em `default_indicator_registry()`. A inclusão de um novo indicador exige registro consciente e metodologia documentada; não há descoberta automática por importação lateral.

## Comando

```bash
python scripts/run_snapshot_analytics.py \
  --snapshot-id snapshot_2026_09 \
  --coverage data/digital_infrastructure/coverage/snapshot_2026_09/parameter_coverage.json \
  --output-root data/digital_infrastructure/analytics \
  --run-output data/digital_infrastructure/analytics/snapshot_2026_09/analytics_run.json
```

## Produtos

```text
data/digital_infrastructure/analytics/
├── indicator_history.jsonl
└── <snapshot_id>/
    ├── analytics_run.json
    ├── snapshot_indicators.json
    └── manifest.json
```

## Barreiras

A execução é interrompida quando:

- a cobertura não é uma lista;
- a matriz está vazia;
- uma linha pertence a outro snapshot;
- faltam `corpus_code` ou `detector_group`;
- existe mais de uma linha para a mesma combinação corpus–parâmetro;
- a mesma execução analítica já foi persistida.

## Integração periódica

No workflow mensal, a análise ocorre somente depois do pós-flight, da triagem e da construção da visão pública derivada. Os produtos analíticos são validados antes de a memória ser consolidada na branch `digital-infrastructure-history`.

A camada analítica é derivada. Falhas nela bloqueiam a consolidação da rodada, mas não modificam a coleta já realizada no runner temporário.
