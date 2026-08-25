# Experiment Registry and Validation Record

## Purpose

This chapter defines how **Memória Audiovisual em Rede (MAR)** records empirical experiments, calibration exercises, blind human reviews and diagnostic replays performed during operational validation.

The purpose of the registry is to prevent experimental activity from being reduced to transient workflow output or informal discussion. Every scientifically relevant experiment must leave a durable, versioned and auditable record that distinguishes:

- the research or validation question;
- the protocol that was intended;
- the protocol that was actually executed;
- the sample and its selection logic;
- software and data provenance;
- automated predictions, when applicable;
- human-review decisions, when applicable;
- deviations from protocol;
- results and limitations;
- whether the experiment supports calibration, validation, diagnosis or an official scientific claim;
- the decision taken after the experiment.

## Canonical locations

Experimental documentation is divided into complementary layers.

### Human-readable scientific record

Detailed experiment reports are stored under:

```text
docs/research/experiments/
```

These reports explain the scientific question, design, execution, results, deviations and interpretation.

### Machine-readable experiment registry

The canonical machine-readable registry is:

```text
data/digital_infrastructure/ai_experiments/experiment_registry_v1.json
```

It provides stable experiment identifiers, status, dates, scientific-claim level, scope, artifact references and interpretation restrictions.

Machine-readable experimental artifacts remain under:

```text
data/digital_infrastructure/ai_experiments/
```

The registry does not replace those artifacts. It indexes and interprets them.

### Executable contract

The registry is governed by JSON Schema Draft 2020-12:

```text
schemas/digital_infrastructure/experiment_registry.schema.json
```

Semantic and integrity rules are implemented by:

```text
scripts/validate_experiment_registry.py
```

The validator is executed by the repository **Quality Checks** workflow and by the automated test suite. A malformed or scientifically inconsistent registry therefore fails CI instead of remaining only a documentation problem.

## Experiment classes

MAR distinguishes at least the following experiment types:

- **controlled benchmark** — known positive and negative controls used to test expected detector behaviour;
- **blind human validation** — human reviewer classifies observations without access to model or rule predictions;
- **calibration experiment** — results are used to modify rules, thresholds, taxonomies or protocols;
- **ecological validation** — a frozen mechanism is evaluated on an independent real-world sample;
- **diagnostic replay** — a reconstruction or replay used to diagnose behaviour when the original execution is incomplete; it is not automatically a valid performance estimate;
- **operational pilot** — a limited real-world execution used to expose workflow or eligibility failures;
- **longitudinal validation** — repeated observation used to test temporal persistence and change detection.

An experiment may have more than one of these labels, but its scientific role must be explicit.

## Scientific claim levels

Every registered experiment declares one `claim_level`:

- `calibration_only` — may guide rule, taxonomy or workflow changes but is not an independent validation result;
- `protocol_scope` — supports only the explicitly bounded protocol or candidate-generation function documented by the experiment;
- `diagnostic_only` — supports diagnosis only and must not be reported as original-run model performance;
- `empirical_validation` — supports an empirical performance claim under the complete frozen and auditable validation protocol;
- `official_baseline` — reserved for a separately authorised baseline-transition process and incompatible with the current T2A registry, whose experiments do not modify T2.

The claim level is independent from the human-readable `status`. This prevents wording such as “completed” or “validated for current protocol” from silently implying a stronger inferential result than the evidence supports.

## Mandatory fields

Every registered experiment must record the structural fields required by the active schema, including:

1. stable experiment ID and version;
2. scientific layer and validation stage;
3. question or hypothesis;
4. experiment type or types;
5. status and scientific `claim_level`;
6. prevalence-sample status;
7. explicit baseline-modification status;
8. limitations;
9. prohibited interpretations;
10. durable artifact inventory;
11. a scientific decision or bounded scientific use.

When applicable, the record must additionally preserve dates, sample construction, workflow/commit provenance, automated predictions, human-review artifacts, blinding, evaluation output, protocol deviations and integrity identifiers.

## Pre-registration and prediction freezing for blind validation

For any new blind human evaluation that will claim **empirical validation** of an automated mechanism, the following order is mandatory:

```text
freeze protocol and software version
→ materialize sample
→ generate automatic predictions
→ persist predictions durably
→ compute and record integrity hash
→ generate blinded human-review queue
→ complete human review
→ close human-review artifact
→ unblind predictions
→ compute performance
→ record interpretation and limitations
```

The executable validator requires an empirical blind validation to reference a prediction artifact marked `frozen_before_human_review: true` and protected by an integrity identifier.

If automatic predictions are not durably persisted before human review, the run may still be useful as a **calibration experiment** or narrower protocol-scope exercise, but it must not be registered as an empirical blind-performance validation.

## Historical experiments and the new rule

The executable governance rule was adopted after some T2A experiments had already occurred. Historical deviations remain visible rather than being retroactively rewritten.

For example, the C1 real-corpus negative challenge preserved a blind human review, but its prediction artifact explicitly states that it was materialized after the human blind review. The result remains usable within the bounded Gate 1 protocol-scope calibration documented for that experiment; it is not reclassified as a preregistered empirical blind-performance estimate.

The first M3 blind review has a different historical deviation: predictions were computed in runner memory but were not durably persisted. M3 therefore remains `calibration_only`, while the subsequent compact replay is `diagnostic_only`.

## Artifact integrity

The validator verifies that every registered artifact path exists. When the registry declares an integrity identifier for the current artifact, it also verifies the bytes:

- a 40-character `content_sha` or `current_blob_sha` is checked as a Git blob SHA-1;
- a 64-character `content_sha` is checked as SHA-256;
- an explicit `sha256` field is checked as SHA-256.

Historical identifiers such as `initial_blob_sha` may identify an earlier preserved Git object and are not compared with the current file bytes. This permits the registry to document artifact evolution without pretending that the current file is identical to its initial version.

## Protocol deviations

A deviation is part of the scientific record. It must not be silently repaired by rewriting the history of the experiment.

Examples include:

- missing prediction artifact;
- prediction materialized only after human review;
- expired workflow artifact without durable copy;
- different sample size from the intended protocol;
- collection blocked by `robots.txt`;
- redirect outside collection scope;
- access state observed by the human reviewer but not represented by the original schema;
- human taxonomy refinement during review;
- software modification after sample exposure;
- a human review completed in practice but not closed in its original machine-readable queue.

When a deviation affects inferential validity, the experiment claim level must remain appropriately bounded, for example `calibration_only` or `diagnostic_only` rather than `empirical_validation`.

A retrospective conclusion may be created to preserve a finding that was already documented elsewhere, but it must identify itself as retrospective, state what original information is missing and leave the historical source artifact unchanged.

## Separation from official scientific results

Experimental products do not modify the official T2 baseline unless a separate, documented scientific gate explicitly authorises that transition.

In particular:

- calibration metrics are not prevalence estimates;
- a validation sample selected to expose edge cases is not a corpus-representative sample;
- absence of detected evidence is not institutional absence;
- a diagnostic replay is not the original run;
- technical success is not empirical validation;
- human review of a page role does not by itself establish corpus membership, AI use or institutional practice.

## Current registered experiments

| Experiment | Stage | Claim level | Status |
|---|---|---|---|
| [`MAR-T2A-C1-TERM-001`](experiments/2026-08_c1_gate1_terminology_validation_v1.md) | Content-AI Gate 1 | `protocol_scope` | validated for current protocol scope |
| [`MAR-T2A-C2-M4-PILOT-001`](experiments/2026-08_c2_m4_gate2_candidate_pilot_v1.md) | Gate 2 / M4 | `calibration_only` | completed; calibration finding |
| [`MAR-T2A-M3-BLIND-001`](experiments/2026-08_m3_surface_typing_blind_validation_v1.md) | M3 | `calibration_only` | completed blind human calibration |
| `MAR-T2A-M3-REPLAY-001` | M3 | `diagnostic_only` | compact-field diagnostic replay |

## CI acceptance rule

No future experiment record is scientifically closed merely because a Markdown report exists. The registry must pass both structural and semantic validation.

At minimum, CI blocks:

- invalid JSON Schema structure;
- duplicate experiment IDs;
- missing governance or artifact files;
- declared current hashes that do not match artifact bytes;
- blind human validation without explicit blinding metadata or durable human-review artifact;
- empirical blind validation without a frozen, hashed prediction artifact;
- empirical validation without an evaluation/comparison artifact;
- diagnostic replay presented as original-run or scientific performance;
- an `official_baseline` claim inside this T2A registry.

## Rule for future experiments

No future T2A experiment should be considered scientifically closed until:

- its machine-readable registry entry exists;
- its durable artifacts are identified;
- its claim level matches what the design actually supports;
- deviations are documented;
- limitations and prohibited interpretations are explicit;
- the interpretation is bounded to what the design supports;
- the next methodological decision is recorded;
- the executable registry validation passes.

---

[← Previous: Reuse and Research Collaboration](12_reuse_and_collaboration.md) · [Research Handbook](README.md)
