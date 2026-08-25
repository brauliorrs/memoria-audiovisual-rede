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

Experimental documentation is divided into two complementary layers.

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

It provides stable experiment identifiers, status, dates, scope, artifact references and scientific-use restrictions.

Machine-readable experimental artifacts remain under:

```text
data/digital_infrastructure/ai_experiments/
```

The registry does not replace those artifacts. It indexes and interprets them.

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

## Mandatory fields

Every new registered experiment must record, when applicable:

1. stable experiment ID and version;
2. scientific layer and validation stage;
3. question or hypothesis;
4. start and completion dates;
5. sample source and selection procedure;
6. sample size and unit of analysis;
7. entities or corpora involved;
8. prevalence-sample status;
9. software branch and commit or workflow run;
10. protocol and classifier version;
11. input artifacts and their integrity identifiers when available;
12. automated prediction artifact and hash before human review, when applicable;
13. blinding procedure;
14. human-review artifact;
15. evaluation artifact;
16. protocol deviations;
17. limitations and non-assessable cases;
18. result scope;
19. whether the result may modify the official baseline;
20. final scientific decision and next gate.

## Pre-registration and prediction freezing for blind validation

For any blind human evaluation of an automated mechanism, the following order is mandatory:

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

If automatic predictions are not durably persisted before human review, the run may still be useful as a **calibration experiment**, but it must not be reported as a valid post-hoc performance evaluation of the original mechanism.

## Protocol deviations

A deviation is part of the scientific record. It must not be silently repaired by rewriting the history of the experiment.

Examples include:

- missing prediction artifact;
- expired workflow artifact without durable copy;
- different sample size from the intended protocol;
- collection blocked by `robots.txt`;
- redirect outside collection scope;
- access state observed by the human reviewer but not represented by the original schema;
- human taxonomy refinement during review;
- software modification after sample exposure;
- a human review completed in practice but not closed in its original machine-readable queue.

When a deviation affects inferential validity, the experiment status must be downgraded appropriately, for example from `validation` to `calibration_only` or `diagnostic_only`.

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

The machine-readable registry currently includes the following T2A experiments:

| Experiment | Stage | Scientific role | Status |
|---|---|---|---|
| [`MAR-T2A-C1-TERM-001`](experiments/2026-08_c1_gate1_terminology_validation_v1.md) | Content-AI Gate 1 | terminology/context calibration | validated for current protocol scope |
| [`MAR-T2A-C2-M4-PILOT-001`](experiments/2026-08_c2_m4_gate2_candidate_pilot_v1.md) | Gate 2 / M4 | item-level candidate eligibility pilot | completed; calibration finding |
| [`MAR-T2A-M3-BLIND-001`](experiments/2026-08_m3_surface_typing_blind_validation_v1.md) | M3 | blind human surface-typing calibration | completed; calibration only |
| `MAR-T2A-M3-REPLAY-001` | M3 | compact-field diagnostic replay | diagnostic only; documented within M3 report |

## Rule for future experiments

No future T2A experiment should be considered scientifically closed until:

- its machine-readable registry entry exists;
- its durable artifacts are identified;
- deviations are documented;
- the interpretation is bounded to what the design supports;
- the next methodological decision is recorded.

---

[← Previous: Reuse and Research Collaboration](12_reuse_and_collaboration.md) · [Research Handbook](README.md)
