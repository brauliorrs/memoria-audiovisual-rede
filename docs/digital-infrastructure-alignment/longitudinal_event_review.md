# Revisão append-only de eventos longitudinais

## Objetivo

Submeter mudanças materiais, alertas de desaparecimento e sinais sensíveis a decisão humana auditável antes de qualquer projeção pública ou interpretação científica.

## Decisões

```text
confirmed       → evento sustentado pelas evidências disponíveis
rejected        → alerta ou mudança não sustentado
reclassified    → classe de triagem corrigida
needs_evidence  → decisão suspensa por falta de evidência
deferred        → análise adiada explicitamente
contested       → evento submetido a contestação documentada
```

`confirmed` significa que o evento superou o critério de revisão definido. Não significa, isoladamente, que o texto público, o indicador ou a interpretação estejam automaticamente aprovados.

Decisões `confirmed`, `rejected` e `reclassified` exigem evidência ou justificativa metodológica identificável. Toda decisão registra revisor, papel, data, nota, evidências consideradas e possíveis conflitos.

## Quórum

Como regra inicial:

```text
material_change       → 1 confirmação
disappearance_alert   → 2 revisores distintos
sensitive             → 2 revisores distintos
```

O quórum pode ser ampliado por política ética, jurídica ou editorial. Revisores impedidos ou com conflito não contam. O cumprimento numérico do quórum não substitui a qualidade da evidência.

## Histórico

Cada decisão é acrescentada ao ledger como `longitudinal_event_review`. Uma nova decisão do mesmo revisor declara `supersedes_review_id`; a decisão anterior permanece preservada.

A revisão deve distinguir:

- mudança no objeto observado;
- correção de erro;
- nova evidência sobre evento antigo;
- reclassificação metodológica;
- alteração de cobertura;
- contestação institucional ou de terceiro.

## Interface operacional

Exportar fila:

```bash
python scripts/review_digital_infrastructure_longitudinal_events.py export \
  --events data/digital_infrastructure/triage/<snapshot_id>.json \
  --output data/digital_infrastructure/event_review/queue_<snapshot_id>.csv
```

Importar decisões:

```bash
python scripts/review_digital_infrastructure_longitudinal_events.py import \
  --input data/digital_infrastructure/event_review/decisions_<snapshot_id>.csv
```

Os nomes são exemplos operacionais. O contrato real é definido pelo código e pelos schemas ativos.

## Elegibilidade posterior

Um evento confirmado pode receber estado `publishable_after_review`, indicando que superou a revisão do evento. Ainda são necessários, quando aplicáveis:

- revisão editorial do enunciado;
- cobertura e denominador adequados;
- licenciamento e proteção de evidências;
- análise de contestação;
- vínculo com produto e manifesto versionados;
- decisão de publicação.

Eventos rejeitados, adiados, contestados ou sem evidência permanecem bloqueados. Reclassificação isolada não equivale a confirmação.

## Estado atual

O fluxo append-only, a fila e as regras de quórum estão implementados estruturalmente. Permanecem pendentes a validação operacional com casos reais e a definição institucional dos papéis de revisão para o primeiro ciclo oficial.