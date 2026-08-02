# Índice composto de interoperabilidade

## Objetivo

Produzir um escore sintético de 0 a 100 para resumir sinais observados de interoperabilidade sem ocultar os componentes, pesos ou lacunas de dados.

## Componentes e pesos

Cada componente possui peso inicial igual a `0,20`:

- IIIF;
- OAI-PMH;
- Dublin Core;
- Schema.org;
- JSON-LD.

A opção por pesos iguais evita atribuir importância diferenciada sem validação empírica ou consenso metodológico. Os pesos permanecem versionados e poderão ser alterados somente em nova versão do indicador.

## Cálculo por corpus

Para cada corpus, um componente avaliável recebe:

- `1` quando o padrão foi explicitamente identificado;
- `0` quando o grupo foi avaliado, mas o padrão não foi identificado.

Estados `error`, `not_assessable` e `missing_observation` são tratados como dados ausentes, e não como zero.

```text
escore_corpus = 100 × soma dos pesos presentes
                      ─────────────────────────
                      soma dos pesos avaliáveis
```

A renormalização dos pesos ocorre apenas quando ao menos três dos cinco componentes são avaliáveis. Corpora abaixo desse limiar são excluídos do agregado e registrados com a justificativa.

## Agregação

```text
interoperability_index = média aritmética dos escores dos corpora elegíveis
```

O resultado preserva nas dimensões:

- pesos;
- limiar mínimo;
- escores por corpus;
- estado de cada componente;
- corpora elegíveis;
- corpora excluídos e motivo.

## Limitações

O índice mede sinais técnicos observados nas superfícies auditadas. Ele não comprova conformidade integral, estabilidade, qualidade dos metadados, funcionamento dos endpoints ou maturidade institucional.

A versão inicial é:

```text
interoperability_index@1.0.0
methodology_version=1.0.0
```
