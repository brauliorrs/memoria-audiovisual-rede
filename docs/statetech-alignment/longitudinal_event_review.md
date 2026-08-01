# Revisão append-only de eventos longitudinais

## Objetivo

Submeter mudanças materiais, alertas de desaparecimento e sinais sensíveis a decisão humana auditável antes de qualquer visão pública derivada.

## Decisões

```text
confirmed       → evento sustentado pelas evidências
rejected        → alerta ou mudança não sustentado
reclassified    → classe de triagem corrigida
needs_evidence  → decisão suspensa por falta de evidência
deferred        → análise adiada explicitamente
```

Decisões `confirmed`, `rejected` e `reclassified` exigem evidência. Toda decisão exige justificativa, revisor e papel do revisor.

## Quórum

```text
material_change       → 1 confirmação
disappearance_alert   → 2 revisores distintos
sensitive             → 2 revisores distintos
```

Revisores com conflito que exija recusa ou conflito ainda sob avaliação não contam para o quórum.

## Histórico

Cada decisão é acrescentada ao ledger como `longitudinal_event_review`. Uma nova decisão do mesmo revisor deve declarar `supersedes_review_id`; a decisão anterior permanece preservada.

## Interface

Exportar fila:

```bash
python scripts/review_statetech_longitudinal_events.py export \
  --events data/statetech/triage/snapshot_2026_09.json \
  --output data/statetech/event_review/queue_snapshot_2026_09.csv
```

Importar decisões:

```bash
python scripts/review_statetech_longitudinal_events.py import \
  --input data/statetech/event_review/decisions_snapshot_2026_09.csv
```

## Publicação

Um evento só pode alimentar uma visão pública quando o serviço devolver estado `confirmed`. A saída recebe `publication_status = publishable_after_review`; isso ainda não publica automaticamente qualquer página, alerta ou afirmação externa.

Eventos rejeitados, adiados ou sem evidência permanecem bloqueados. Reclassificação isolada não equivale a confirmação e ainda exige o quórum aplicável.
