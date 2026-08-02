# 04 — System Architecture

## Architectural goal

The architecture separates acquisition, evidence, governance, publication and analytics so that no derived result can silently rewrite its historical source.

```text
Public sources
    ↓
Collectors and detectors
    ↓
Normalised observations
    ↓
Evidence and provenance ledger
    ↓
Snapshot coverage matrix
    ↓
Longitudinal comparison
    ↓
Event triage and human review
    ↓
Versioned public views
    ↓
Analytics engine
    ↓
Indicators and research datasets
```

## Layer 1 — Discovery and corpus registry

The discovery layer records active corpora, candidates, protocolled cases and excluded entities. It supports expansion without conflating everything found with the research corpus.

Its outputs answer:

- what was identified;
- how it was classified;
- whether it is eligible;
- why it was excluded when applicable.

## Layer 2 — Collection and detection

Collectors obtain records and institutional information from documented public routes. Digital-infrastructure detectors inspect observable technical evidence such as APIs, metadata formats, interoperability signals, search mechanisms, restrictions and declared AI-related practices.

The collection layer does not decide publication or scientific interpretation.

## Layer 3 — Normalisation and evidence

Adapters translate heterogeneous detector output into common observation contracts. Every observation can reference raw artefacts and evidence objects.

Stable identifiers allow observations, entities and evidence to remain traceable across processing stages.

## Layer 4 — Ledger and integrity

The ledger is append-only. Integrity controls prevent orphan evidence, duplicated identifiers, invalid version chains and conflicting entity resolutions.

This layer preserves the auditable memory of the platform.

## Layer 5 — Snapshot and coverage

Each periodic cycle produces an explicit matrix of corpus-by-detector-group coverage. Missing groups remain visible instead of disappearing from the dataset.

Preflight checks validate the historical state before collection. Post-flight checks confirm expected coverage and counts before consolidation.

## Layer 6 — Longitudinal events

Compatible snapshots are compared to derive events. Event triage classifies them as routine, material, sensitive, blocked or requiring evidence.

The comparison engine records previous and current values rather than replacing historical observations.

## Layer 7 — Curatorial governance

Curatorial review is separated from automatic detection. Review files and append-only decisions support confirmation, rejection, reclassification and requests for further evidence.

Sensitive claims may require multiple independent reviewers.

## Layer 8 — Publication management

Public views are immutable derived products. Later curatorial decisions generate numbered publication revisions.

An active-publication registry indicates which version is currently authoritative for delivery without deleting any earlier version.

A stable delivery projection allows dashboards or future APIs to consume only the active versions.

## Layer 9 — Analytics

The analytics engine uses a registry of versioned indicators. It reads validated snapshot products and produces persisted analytical runs, manifests, hashes and longitudinal history.

Current products include coverage indicators, the Audiovisual Archive Access Index, a composite interoperability index and sensitivity analysis.

## Historical storage

Durable products are preserved in the dedicated historical branch and include:

- ledgers;
- snapshots and coverage products;
- review decisions;
- public views and revisions;
- active-publication registries;
- analytical results and histories.

Temporary workflow artefacts may expire, but they are not the sole repository of scientific memory.

## Operational boundaries

The architecture intentionally separates these actions:

```text
collecting data
≠ confirming a scientific claim
≠ publishing an event
≠ activating a publication revision
≠ calculating an indicator
```

This separation reduces accidental escalation from heuristic detection to public assertion.

## Extensibility

New collectors, detector groups and indicators can be added through explicit contracts and registries. Extensions must declare schemas, methodology, expected coverage and validation rules before entering official runs.

## Current implementation status

The core architecture is implemented and under operational validation. A full real-world cycle remains necessary to verify detector accuracy, false positives, false negatives, performance and end-to-end historical consolidation.

---

[← Previous: Methodological Framework](03_methodological_framework.md) · [Research Handbook](README.md) · [Next: Corpus Policy →](05_corpus_policy.md)
