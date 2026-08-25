# MAR Research Experiments

This directory stores the human-readable scientific record of empirical experiments performed during validation of **Memória Audiovisual em Rede (MAR)**.

Each file must describe what was intended, what was executed, what evidence was preserved, what failed or deviated from protocol, what conclusions are supported and what conclusions are explicitly not supported.

## Required structure for each experiment report

A report should contain, where applicable:

1. **Experiment identity** — stable ID, version, dates, stage and scientific role.
2. **Question** — the validation question or hypothesis.
3. **Context** — why the experiment was required.
4. **Protocol** — sample construction, collection policy, classifier version and review rules.
5. **Blinding** — what information the human reviewer could and could not see.
6. **Provenance** — branch, commit, workflow run, source artifacts and integrity identifiers.
7. **Sample** — unit of analysis, size, entities and selection rationale.
8. **Execution** — what actually happened.
9. **Protocol deviations** — any divergence from the planned procedure.
10. **Human-review result** — if applicable, recorded separately from automated outputs.
11. **Automated result** — if applicable, only after valid unblinding.
12. **Diagnostic analyses** — clearly separated from valid performance estimates.
13. **Limitations** — including access, observability, representativeness and missing artifacts.
14. **Scientific interpretation** — bounded to the design.
15. **Decision** — calibration, acceptance, rejection, redesign or next validation gate.
16. **Artifact inventory** — durable repository paths and relevant workflow identifiers.

## Integrity rule

Blind automated validation must persist the prediction artifact and an integrity hash **before** the human-review queue is opened. A run without that frozen prediction record may inform calibration but must not be retrospectively presented as a valid estimate of the original model or rule performance.

Historical gaps must remain visible. Retrospective conclusion artifacts may make an already documented result durable, but they must identify themselves as retrospective and must not silently rewrite the original queue or workflow state.

## Current reports

- [`MAR-T2A-C1-TERM-001`](2026-08_c1_gate1_terminology_validation_v1.md) — C1 Gate 1 terminology/context validation.
- [`MAR-T2A-C2-M4-PILOT-001`](2026-08_c2_m4_gate2_candidate_pilot_v1.md) — Gate 2 / M4 item-level candidate eligibility pilot.
- [`MAR-T2A-M3-BLIND-001`](2026-08_m3_surface_typing_blind_validation_v1.md) — M3 blind human surface-typing calibration.

The M3 compact replay (`MAR-T2A-M3-REPLAY-001`) is documented inside the M3 experiment report because it is a diagnostic derivative of that experiment rather than an independent validation sample.

The machine-readable index is maintained in:

```text
data/digital_infrastructure/ai_experiments/experiment_registry_v1.json
```
