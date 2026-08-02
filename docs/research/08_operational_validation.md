# Operational Validation

## Purpose

Operational validation determines whether the implemented research infrastructure produces technically correct and scientifically defensible results when applied to real audiovisual archives.

Passing unit tests is necessary but not sufficient. Validation also requires controlled execution, evidence inspection, detector assessment, and review of false positives and false negatives.

## Validation sequence

```text
1. Syntax and dependency checks
2. Unit and integration tests
3. Controlled execution on a small corpus sample
4. Manual evidence inspection
5. Detector-level error analysis
6. Indicator verification
7. Workflow and historical persistence checks
8. Full-corpus execution
9. Acceptance decision
```

## Automated quality checks

The quality workflow must verify at least:

- successful dependency installation;
- Python module compilation;
- complete unit-test execution;
- deployment snapshot checks when applicable;
- absence of known schema or integrity failures.

A green workflow confirms consistency with the implemented test contracts. It does not prove external validity of heuristic detections.

## Controlled corpus sample

The first operational run should use a deliberately heterogeneous sample, including:

- an archive with direct public access;
- an archive requiring formal request or registration;
- an aggregator;
- a corpus with a documented API;
- a corpus with IIIF or OAI-PMH evidence;
- a technically unstable or partially assessable route;
- an excluded commercial image or video bank.

The purpose is to test methodological boundaries, not to maximise corpus size.

## Detector validation

Each detector group must be evaluated separately:

- technologies and repository systems;
- APIs and public services;
- metadata formats;
- interoperability mechanisms;
- search mechanisms;
- access restrictions;
- publicly observable AI-related signals.

For every group, validation should record:

- confirmed positives;
- false positives;
- confirmed negatives;
- suspected false negatives;
- not-assessable cases;
- evidence quality;
- language or terminology issues;
- route instability.

## Access validation

The Audiovisual Archive Access Index requires special review because a single unrecognised restriction term can alter the numerator.

Validation must test multilingual expressions related to:

- registration;
- authentication;
- formal request;
- email request;
- authorisation;
- payment;
- subscription;
- on-site-only consultation.

Commercial paid banks must remain catalogued but excluded from the scientific corpus.

## Indicator verification

For each controlled run, indicator results should be independently checked from the coverage matrix. Verification should confirm:

- numerator;
- denominator;
- excluded corpora;
- exclusion reasons;
- treatment of unknown and missing states;
- methodology version;
- persistence key;
- integrity hash.

Composite indexes require an additional check of component availability, weights, renormalisation, corpus scores, and aggregate calculation.

## Longitudinal validation

At least two controlled snapshots are needed to validate temporal behaviour. The second snapshot should include deliberate test changes such as:

- appearance of a technology;
- disappearance of a previously detected signal;
- access restriction change;
- new API evidence;
- temporary route failure;
- unchanged observation.

The system must distinguish real change from error, missing observation, and temporary unavailability.

## Human review validation

Sensitive or material events must be tested through the complete review lifecycle:

```text
detection
→ triage
→ review queue
→ reviewer decision
→ quorum where required
→ publication eligibility
→ versioned public view
```

Disappearance and other sensitive claims must not be published as definitive facts without the required confirmations.

## Persistence and recovery

Validation should confirm that:

- previous snapshots are not overwritten;
- append-only histories remain valid;
- interrupted batches can be resumed safely;
- manifests match persisted products;
- corrupted or inconsistent state blocks consolidation;
- temporary workflow artifact expiry does not remove durable history.

## Acceptance criteria

The infrastructure should be considered ready for the first official cycle only when:

- the full automated test suite passes;
- controlled corpus results have been manually reviewed;
- critical false positives are corrected;
- denominator rules are confirmed;
- the access index matches manual classification;
- snapshot comparison behaves as intended;
- historical persistence is verified;
- unresolved limitations are documented.

## Validation outputs

Each validation cycle should produce a concise report containing:

- scope and selected corpora;
- software and methodology versions;
- tests executed;
- detector performance findings;
- indicator verification;
- known limitations;
- corrections applied;
- final acceptance status.

Operational validation is therefore both a software-quality process and a methodological audit.
