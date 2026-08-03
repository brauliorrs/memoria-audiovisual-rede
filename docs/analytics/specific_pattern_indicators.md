# Indicadores de padrões específicos

## Objetivo

Medir a adoção observada de IIIF, OAI-PMH, Dublin Core, Schema.org e JSON-LD sem confundir a presença geral do grupo detector com a presença do padrão específico.

## Regra de cálculo

Cada indicador usa como denominador os corpora cujo grupo correspondente está em estado `detected`, `not_detected` ou `unknown`. Estados `error`, `not_assessable` e `missing_observation` são excluídos e registrados no resultado.

O numerador inclui somente corpora com estado `detected` e cujo `detected_values` contenha um alias normalizado do padrão.

```text
100 × corpora com padrão explicitamente identificado
      ─────────────────────────────────────────────
      corpora avaliáveis no grupo correspondente
```

## Grupos utilizados

- IIIF e OAI-PMH: `interoperability`;
- Dublin Core, Schema.org e JSON-LD: `metadata_format`.

## Garantias

- um grupo detectado sem o padrão pesquisado conta como avaliável, mas não como positivo;
- aliases ficam registrados nas dimensões do resultado e no registro metodológico;
- valores são normalizados apenas para comparação textual;
- a detecção não comprova conformidade, completude, qualidade ou funcionamento do padrão;
- cada indicador possui versão própria e metodologia explícita.

## Indicadores

```text
iiif_coverage@1.0.0
oai_pmh_coverage@1.0.0
dublin_core_coverage@1.0.0
schema_org_coverage@1.0.0
json_ld_coverage@1.0.0
```
