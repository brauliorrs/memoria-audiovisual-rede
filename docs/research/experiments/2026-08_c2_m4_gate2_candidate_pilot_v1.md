# C2 / M4 Gate 2 Candidate Eligibility Pilot v1

## Experiment identity

- **Experiment ID:** `MAR-T2A-C2-M4-PILOT-001`
- **Stage:** `t2a_ai_archive_gate2_validation`
- **Scientific layer:** AI in audiovisual production/modification, dependent on MAR item-resolution intelligence
- **Experiment type:** operational pilot / calibration experiment
- **Status:** `completed_calibration_finding`
- **Prevalence sample:** no
- **Official baseline modification:** no

## Question

Before later Gate 2 conditions are applied, do candidate URLs generated from materialized MAR records represent eligible audiovisual **items, versions or segments**, rather than general archive or institutional pages?

This is both the first condition of Content-AI Gate 2 and the problem later formalised as M4 item-level candidate resolution.

## Gate 2 sequential rule

An archive-level positive requires all of the following:

1. the observation is an audiovisual item, version or segment;
2. the item belongs to the observed corpus;
3. a public item-specific surface is accessible;
4. the AI evidence is linked to that specific item.

The conditions are sequential. If condition 1 fails, the later conditions are not interpreted from that candidate URL.

## Candidate source

The original blind queue is:

```text
data/digital_infrastructure/ai_experiments/ai_archive_two_gate_review_queue_v1.json
```

Source metadata preserved in that queue:

- source workflow run ID: `32169213217`;
- source artifact ID: `9336613400`;
- candidates: 2;
- entities: ECPAD and INA;
- Gate 1 terminology/context positive for both candidates;
- Gate 2 prediction blinded for human review.

The source rule required candidates to originate from materialized records under `data/output` associated with active MAR corpora.

## Human review

### ECPAD

Candidate URL:

```text
https://archives.ecpad.fr/archives/archives
```

Human finding: the URL represented a **general archive page**, not an audiovisual item, version or segment.

Result for condition 1 / M4:

```text
human_is_item_level_observation = false
```

Because condition 1 failed, corpus membership, public item-surface accessibility and item-linked AI evidence were not adjudicated for this candidate.

### INA

Candidate URL:

```text
https://www.ina.fr/institut-national-audiovisuel
```

Human finding: the URL represented an **institutional/main page with links to other archive areas**, not an audiovisual item, version or segment.

Result for condition 1 / M4:

```text
human_is_item_level_observation = false
```

Again, later Gate 2 conditions were not reached.

## Result

- candidates reviewed: **2**;
- item-level eligible: **0**;
- item-level ineligible: **2**;
- observed eligibility rate in this pilot: **0/2**.

This ratio describes only the two pilot candidates. It is not a prevalence or general performance estimate.

## Scientific interpretation

The result exposed an upstream candidate-resolution problem: a record may contain a URL relevant to an archive or institution without that URL being an item-specific audiovisual surface suitable for later Gate 2 evidence linkage.

The pilot therefore does **not** support any of the following interpretations:

- ECPAD or INA do not use AI;
- ECPAD or INA lack audiovisual archives;
- no eligible item exists in either corpus;
- item surfaces are necessarily inaccessible;
- Gate 2 produced a negative archive-AI classification.

The only defensible finding is that **the two candidate URLs supplied to the pilot were not item-level observations**.

## Documentation gap discovered retrospectively

The original blind queue still has `status = pending_human_review` and its unit decision fields were not updated with the completed human findings.

The result was nevertheless incorporated into the MAR validation roadmap before M3 was initiated. To preserve the scientific history without rewriting the original queue, a retrospective conclusion artifact was created on 2026-08-24:

```text
data/digital_infrastructure/ai_experiments/ai_archive_two_gate_pilot_conclusion_v1.json
```

That artifact explicitly states that:

- the exact original human-review date was not preserved in a dedicated completion artifact;
- the 0/2 item-level finding is a retrospective durable record of the already documented review;
- the original queue remains unchanged as a historical artifact.

This documentation gap contributed to the new experiment-registry policy requiring completed human-review artifacts and durable experiment closure.

## Methodological decision

The pilot motivated two upstream validation stages:

- **M3:** classify the role of the observed public surface;
- **M4:** improve candidate resolution so tasks requiring an audiovisual item actually receive an item, version or segment URL.

The immediate next experiment was `MAR-T2A-M3-BLIND-001`, the blind human surface-typing calibration.

## Artifact inventory

```text
data/digital_infrastructure/ai_experiments/ai_archive_two_gate_review_queue_v1.json
data/digital_infrastructure/ai_experiments/ai_archive_two_gate_pilot_conclusion_v1.json
docs/digital-infrastructure-alignment/mar_intelligence_and_ai_validation_roadmap.md
```
