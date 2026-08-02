# Análise de sensibilidade do índice de interoperabilidade

## Objetivo

Avaliar quanto o resultado do `interoperability_index@1.0.0` depende da escolha dos pesos atribuídos a IIIF, OAI-PMH, Dublin Core, Schema.org e JSON-LD.

A análise é um produto derivado. Ela não substitui, recalcula nem altera o índice oficial persistido, cuja metodologia continua usando pesos iguais de 0,20.

## Cenários

| Cenário | IIIF | OAI-PMH | Dublin Core | Schema.org | JSON-LD |
|---|---:|---:|---:|---:|---:|
| `official_equal_weights` | 0,20 | 0,20 | 0,20 | 0,20 | 0,20 |
| `protocol_priority` | 0,30 | 0,30 | 0,15 | 0,10 | 0,15 |
| `semantic_web_priority` | 0,10 | 0,10 | 0,20 | 0,30 | 0,30 |
| `audiovisual_delivery_priority` | 0,40 | 0,15 | 0,15 | 0,15 | 0,15 |

Os cenários não representam novas metodologias oficiais. Eles são hipóteses de ponderação usadas para verificar robustez.

## Produtos

O relatório registra:

- escore agregado de cada cenário;
- escore de cada corpus em cada cenário;
- amplitude entre o maior e o menor resultado agregado;
- variação máxima de cada corpus;
- mudanças de posição em relação ao cenário oficial;
- corpora excluídos por cobertura insuficiente;
- interpretação padronizada da sensibilidade.

## Interpretação

- amplitude de até 5 pontos: resultado agregado robusto;
- acima de 5 e até 15 pontos: sensibilidade moderada;
- acima de 15 pontos: alta sensibilidade, exigindo interpretação cautelosa.

Esses limiares são operacionais e devem ser revistos antes de uso como convenção científica definitiva.

## Dados ausentes

A mesma regra do índice oficial é preservada: um corpus precisa ter ao menos três dos cinco componentes avaliáveis. Pesos ausentes são renormalizados dentro de cada cenário; ausência não é convertida automaticamente em zero.

## Comando

```bash
python scripts/analyze_interoperability_index_sensitivity.py \
  --snapshot-id snapshot_2026_09 \
  --coverage data/digital_infrastructure/coverage/snapshot_2026_09/parameter_coverage.json \
  --output data/digital_infrastructure/analytics/snapshot_2026_09/interoperability_sensitivity.json
```

## Limites

A análise verifica dependência em relação aos pesos escolhidos. Ela não valida se os componentes são teoricamente suficientes, se os detectores são completos ou se o índice mede conformidade técnica real.
