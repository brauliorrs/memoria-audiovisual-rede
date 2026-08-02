# 03 — Methodological Framework

## Research design

The platform uses a longitudinal observational design. It does not treat each collection as an isolated scrape. Every observation belongs to a documented cycle and can be compared with previous cycles without deleting earlier states.

The core sequence is:

```text
Discovery
→ Classification
→ Eligibility
→ Observation
→ Normalisation
→ Provenance
→ Snapshot
→ Comparison
→ Event detection
→ Human review
→ Publication
→ Analytics
```

## Unit of observation

The principal unit is the eligible audiovisual archive or institutional corpus. The system also preserves related units such as institutions, platforms, routes, records, providers, technologies and discovery candidates.

These levels are not merged analytically. A platform, an institution and a corpus may be related but remain distinct entities.

## Discovery and eligibility

Discovery is deliberately broader than the scientific corpus. All relevant candidates may be registered, classified and retained even when they are excluded from analysis.

Eligibility decisions preserve:

- corpus status;
- reason for inclusion or exclusion;
- date and method of classification;
- evidence used;
- revision history when applicable.

Commercial paid image or video banks remain catalogued in the discovery layer but do not enter the research corpus or analytical denominators.

## Observation and normalisation

Automated detectors inspect publicly accessible routes and convert technical signals into normalised observations. Each detector group has an explicit contract and may return states such as:

- `detected`;
- `not_detected`;
- `unknown`;
- `error`;
- `not_assessable`;
- `missing_observation`.

Absence of a detected signal is not automatically interpreted as institutional absence. The result remains bounded by the observed route and method.

## Provenance

Every observation preserves its evidential chain, including:

- source URL or source identifier;
- acquisition method;
- observation timestamp;
- raw artefact reference;
- transformation history;
- schema version;
- reviewer decisions;
- publication history.

Raw artefacts are content-addressed when applicable, allowing later verification of the material from which an observation was derived.

## Snapshots

A snapshot is a closed analytical representation of one observation cycle. It has a stable identifier and is never silently overwritten.

Snapshot policies define:

- opening and closing criteria;
- expected corpus coverage;
- naming conventions;
- schema version;
- integrity checks;
- retention and historical preservation.

## Longitudinal comparison

Two compatible snapshots can be compared to identify:

- appearance of a signal;
- disappearance of a signal;
- change in detected values;
- change in access regime;
- technology adoption or discontinuation;
- source unavailability;
- unchanged observations.

Potentially sensitive events, especially disappearance or extinction signals, are not published as definitive facts without human confirmation.

## Human review

Review decisions are append-only. A later decision supersedes an earlier one without deleting it.

Routine and low-risk changes may be eligible for automatic publication. Material or sensitive changes require one or more confirmations according to the event class. Disappearance signals require independent confirmation by distinct reviewers.

## Publication

Published views are derived products. They do not modify the original observation, snapshot or review ledger.

Late review decisions may generate a new publication revision linked to the same source snapshot. Generating a revision and activating it as the current public version are separate operations.

## Analytics

The analytical engine executes versioned indicators over validated snapshot products. Results preserve:

- indicator identifier and version;
- methodology version;
- snapshot identifier;
- numerator and denominator;
- exclusions;
- interpretation notes;
- dimensions used in the calculation.

The system blocks silent replacement of the same analytical key.

## Missing data

Errors, non-assessable cases and missing observations are not automatically converted into negative evidence. Each indicator declares which states enter its denominator and which are excluded.

Composite indexes require a minimum number of evaluable components and document any renormalisation of weights.

## Reproducibility and limitations

The methodology supports reproducibility through versioned code, schemas, data contracts, provenance and immutable historical products.

It does not claim that public technical inspection reveals every internal system used by an institution. Results must always be interpreted according to observable evidence, route coverage, temporal context and known technical limitations.
