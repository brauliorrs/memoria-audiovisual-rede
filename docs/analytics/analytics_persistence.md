# Persistência analítica versionada

A persistência analítica registra resultados produzidos pelo motor sem modificar os snapshots, o ledger ou as publicações que serviram de fonte.

## Produtos

```text
data/digital_infrastructure/analytics/
├── indicator_history.jsonl
└── <snapshot_id>/
    ├── snapshot_indicators.json
    └── manifest.json
```

`snapshot_indicators.json` contém a execução completa. `manifest.json` registra a versão metodológica, a quantidade de indicadores, as chaves versionadas e o hash SHA-256 do conteúdo. `indicator_history.jsonl` reúne uma linha por indicador e snapshot para formação de séries temporais.

## Chave analítica

Cada resultado é identificado por:

```text
snapshot_id
+ indicator_id
+ indicator_version
+ methodology_version
```

A repetição da mesma combinação é bloqueada. Um snapshot já persistido também não pode ser sobrescrito. Alterações metodológicas devem produzir outra versão do indicador ou da metodologia, nunca substituir resultados anteriores.

## Regras de aceite

Somente execuções com `status = completed` podem ser gravadas. A contagem declarada deve coincidir com os resultados, as chaves devem estar completas e não pode haver duplicidade interna ou no histórico.

O hash é calculado sobre uma serialização JSON canônica. A operação `verify` recalcula o hash e também confere a quantidade de resultados.

## Operação

```bash
python scripts/persist_analytics_run.py \
  --run data/tmp/analytics_run.json \
  --output-root data/digital_infrastructure/analytics
```

Verificação posterior:

```bash
python scripts/persist_analytics_run.py \
  --run data/tmp/analytics_run.json \
  --output-root data/digital_infrastructure/analytics \
  --verify-only \
  --snapshot-id snapshot_2026_09
```

A persistência é separada da execução do motor. Essa separação permite validar os resultados antes de incorporá-los à memória longitudinal da plataforma.
