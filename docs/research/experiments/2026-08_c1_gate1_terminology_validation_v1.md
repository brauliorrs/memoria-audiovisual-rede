# C1 Gate 1 Terminology/Context Validation v1

## Experiment identity

- **Experiment ID:** `MAR-T2A-C1-TERM-001`
- **Stage:** Content-AI Gate 1
- **Scientific layer:** AI in audiovisual production/modification
- **Decision date:** 2026-08-18
- **Status:** `validated_for_current_protocol_scope`
- **Prevalence sample:** no
- **Official baseline modification:** no

## Question

Can the current deterministic Gate 1 protocol identify explicit, verifiable terminology and context indicating possible AI participation in audiovisual production or modification while preserving the distinction between **candidate evidence** and **confirmed AI occurrence in an observed archive**?

## Scope

Gate 1 is a terminology/context identification mechanism. It does not establish that an AI-modified or AI-assisted item belongs to a MAR corpus, is publicly observable at item level or satisfies the later archive-level confirmation gate.

A positive Gate 1 signal may only become an archive-level positive after Gate 2 confirms all of the following:

1. audiovisual item/version/segment observation;
2. membership in the observed corpus;
3. accessible public item surface;
4. evidence linked to that specific item.

## Evidence basis

### Controlled reference benchmark

The controlled benchmark contained six known controls:

- 3 positive controls;
- 3 negative controls.

The current protocol produced:

- true positives: 3;
- true negatives: 3;
- false positives: 0;
- false negatives: 0;
- binary precision: 1.0;
- binary recall: 1.0;
- binary F1: 1.0;
- exact usage-class accuracy: 1.0.

These values describe the **controlled reference benchmark only**. They are calibration evidence, not corpus-wide performance or prevalence estimates.

Primary artifacts:

```text
data/digital_infrastructure/ai_experiments/ai_content_validation_sample_v1.json
data/digital_infrastructure/ai_experiments/ai_content_validation_report_v1.json
```

### Blind real-corpus negative challenge

A separate blind challenge used 12 real-corpus units. Human review classified all 12 as negative for verifiable AI-production evidence.

Comparison result:

- evaluated units: 12;
- human positive: 0;
- human negative: 12;
- true negative: 12;
- false positive: 0;
- not assessable: 0.

This supports specificity on the observed negative challenge cases. Because the sample contained no human positives, positive recall cannot be estimated from this challenge.

Primary artifacts:

```text
data/digital_infrastructure/ai_experiments/ai_content_blind_predictions_v1.json
data/digital_infrastructure/ai_experiments/ai_content_blind_review_queue_v1.json
data/digital_infrastructure/ai_experiments/ai_content_blind_review_amendments_v1.jsonl
data/digital_infrastructure/ai_experiments/ai_content_blind_comparison_report_v1.json
```

### Supplementary positive-enriched challenge

A supplementary challenge was constructed to test positive terminology/context recognition without reusing the original 3×3 controls.

It contained six candidates:

- four BFI candidates that were human-evaluable and human-positive;
- two NFSA candidates that were not assessable because the specific public evidence surface was unavailable to the reviewer.

The two non-assessable cases were not converted into negatives or false negatives.

Primary artifacts:

```text
data/digital_infrastructure/ai_experiments/ai_content_blind_positive_challenge_v1.json
data/digital_infrastructure/ai_experiments/ai_content_blind_positive_challenge_amendments_v1.jsonl
data/digital_infrastructure/ai_experiments/ai_content_positive_challenge_scope_correction_v1.json
```

## Scientific conclusion

The Gate 1 terminology/context protocol is considered calibrated for its current deterministic version and may generate candidates for Gate 2.

This validation supports the narrow claim that the mechanism can recognise the tested terminology/context patterns under the documented controls and challenges.

It does **not** support:

- a claim that any MAR archive contains AI-produced material;
- prevalence estimates;
- corpus-wide sensitivity estimates;
- bypassing item-level resolution;
- converting inaccessible evidence surfaces into negative AI classifications.

The canonical conclusion artifact is:

```text
data/digital_infrastructure/ai_experiments/ai_content_gate1_terminology_validation_conclusion_v1.json
```

## Access and assessability finding

The experiment established an important separation among:

- indexed/discoverable in archive;
- public item surface status;
- AI-evidence assessability.

An item may be discoverable while its specific public evidence surface is unavailable. Such a case is not eligible for archive-level confirmation while access is unavailable and must not be interpreted as absence of AI evidence.

## Decision

Gate 1 may continue to operate as a candidate-generation stage. Scientific activation at archive level remains blocked until Gate 2 confirms the item-level observation, corpus membership, public surface and item-linked evidence.

The next experiment in the chain was the Gate 2/M4 candidate eligibility pilot, registered as `MAR-T2A-C2-M4-PILOT-001`.
