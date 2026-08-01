# Visão pública derivada Estado–tecnologia

## Finalidade

A visão pública é um produto derivado, versionado e rastreável. Ela não publica automaticamente páginas, alertas ou afirmações externas. Seu objetivo é separar, dentro da memória histórica, os eventos que já satisfazem as condições metodológicas mínimas para uma futura exposição pública.

## Entradas

```text
relatório de triagem do snapshot
+ ledger append-only
+ revisões humanas dos eventos
→ visão pública derivada
```

## Elegibilidade

Entram automaticamente apenas eventos rotineiros classificados como `routine`, com `publication_status = publishable` e sem exigência de revisão.

Eventos não rotineiros entram somente quando o `LongitudinalEventReviewService` comprova o quórum exigido:

```text
material_change
→ 1 confirmação válida

disappearance_alert ou sensitive
→ 2 confirmações válidas de revisores distintos
```

Eventos rejeitados, adiados, sem evidência, em revisão ou com quórum incompleto ficam fora da visão.

## Redação cautelosa

A redação pública é gerada por modelos fixos e conservadores. Um desaparecimento confirmado é descrito como sinal não identificado na rodada atual e inclui a ressalva de que isso não comprova eliminação definitiva do recurso ou da informação.

A visão não transforma erro de acesso, `not_assessable`, `still_missing` ou outro problema de qualidade em desaparecimento.

## Rastreabilidade

Cada item preserva:

```text
event_id
snapshot_id
corpus_code
detector_group
change_type
effective_class
previous_values
current_values
publication_basis
review_ids
evidence_ids
```

Eventos rotineiros usam `publication_basis = automatic_routine`. Eventos liberados por decisão humana usam `publication_basis = human_review_quorum`.

## Versionamento

Os arquivos são gravados em:

```text
data/statetech/public/
├── public_view_index.jsonl
└── <snapshot_id>/
    ├── events.json
    └── manifest.json
```

Um snapshot existente não pode ser sobrescrito. O manifesto informa o total de eventos, quantos foram rotineiros e quantos dependeram de revisão humana.

## Execução

```bash
python scripts/build_statetech_public_view.py \
  --snapshot-id snapshot_2026_09 \
  --events data/statetech/triage/snapshot_2026_09.json \
  --ledger data/statetech/ledger.jsonl \
  --output-root data/statetech/public
```

O workflow periódico gera essa visão depois da triagem e antes da consolidação na branch `statetech-history`.

## Limite deliberado

A existência de um item em `data/statetech/public` significa apenas que ele é elegível para uma camada pública futura. Não há implantação automática em site, API, dashboard ou rede social.
