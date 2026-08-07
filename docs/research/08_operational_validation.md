# Operational Validation

## Purpose

Operational validation determines whether the implemented research infrastructure produces technically correct, reproducible and scientifically defensible results when applied to real audiovisual archives.

Passing automated checks is necessary but not sufficient. Validation also requires controlled execution, inspection of evidence, detector-level error analysis, denominator verification, review of exclusions and confirmation that public outputs do not exceed what the observed evidence supports.

## What operational validation is — and is not

Operational validation is the transition between architectural implementation and scientific use.

It confirms that:

- implemented components behave according to their documented contracts;
- evidence can be traced to sources, methods, dates and review decisions;
- analytical populations and denominators are constructed correctly;
- temporal comparisons preserve uncertainty and historical state;
- public outputs distinguish detected evidence from verified institutional facts.

It does not, by itself, establish that every detector is universally accurate, that every institutional website is fully observable, or that absence of public evidence proves absence of a practice or technology.

## Validation sequence

```text
1. Syntax, dependency and schema checks
2. Unit and integration tests
3. Documentation, citation, link and internationalisation checks
4. Controlled execution on a heterogeneous corpus sample
5. Manual evidence inspection
6. Detector-level error analysis
7. Indicator and denominator verification
8. Review, publication and historical-persistence checks
9. Two-snapshot longitudinal validation
10. Full-corpus readiness decision
```

## Automated quality controls

The current automated controls cover:

- dependency installation;
- Python compilation;
- unit and integration tests;
- scientific snapshot and reference-corpus integrity;
- indicator-result and methodology consistency;
- deployment snapshot checks;
- Markdown internal-link validation;
- `CITATION.cff` validation;
- multilingual interface auditing.

A green workflow confirms consistency with the implemented contracts. It does not prove external validity of heuristic detections or completeness of institutional observation.

## Controlled corpus sample

The first empirical validation run must use a deliberately heterogeneous sample, including:

- an archive with direct public access;
- an archive requiring registration, authentication or formal request;
- an aggregator;
- a corpus with a documented API;
- a corpus with IIIF or OAI-PMH evidence;
- a technically unstable or partially assessable route;
- an excluded commercial image or video bank;
- a case in which public evidence is ambiguous or distributed across internal pages.

The purpose is to test methodological boundaries and failure modes, not to maximise corpus size.

## Detector validation

Each detector group must be evaluated separately:

- technologies and repository systems;
- APIs and public services;
- metadata formats;
- interoperability mechanisms;
- search and discovery mechanisms;
- access restrictions;
- public evidence related to AI or automated processing.

For every detector group, validation must record:

- confirmed positives;
- false positives;
- confirmed negatives where a defensible negative can be established;
- suspected false negatives;
- ambiguous results;
- not-assessable cases;
- evidence quality;
- language and terminology issues;
- route instability;
- observation coverage.

A `not detected` result means that the declared procedure did not identify evidence on the assessed public surfaces. It must not be converted automatically into institutional absence.

## Access validation

The Audiovisual Archive Access Index requires specific review because a single unrecognised restriction can alter the numerator.

Validation must test multilingual expressions related to:

- registration;
- authentication;
- formal or administrative request;
- email or form submission;
- authorisation;
- payment or subscription;
- on-site-only consultation;
- partial access to records without access to the audiovisual object.

Commercial paid banks must remain visible in the Discovery Registry but excluded from the Scientific Corpus and from the indicator denominator.

## Indicator verification

For each controlled run, indicator results must be independently reconstructed from the coverage matrix and the active methodological contract.

Verification must confirm:

- indicator and methodology versions;
- analytical population;
- numerator and denominator;
- eligible and assessable units;
- excluded units and reasons;
- treatment of unknown, error, ambiguous and missing states;
- persistence key;
- integrity hash;
- compatibility with the machine-readable indicator and methodology registries.

Composite indexes require additional verification of component availability, weights, minimum evaluable coverage, renormalisation, unit-level scores, aggregate calculation and sensitivity analysis.

## Longitudinal validation

At least two controlled snapshots are required to validate temporal behaviour. The second snapshot should contain deliberate test changes such as:

- appearance of a technology;
- disappearance of a previously detected signal;
- change in an access restriction;
- new API or interoperability evidence;
- temporary route failure;
- unchanged observation;
- observation that becomes non-assessable.

The system must distinguish substantive change from collection error, missing observation, temporary unavailability and methodological change.

## Human-review validation

Sensitive or material events must be tested through the complete review lifecycle:

```text
detection
→ triage
→ review queue
→ reviewer decision
→ quorum where required
→ publication eligibility
→ versioned public output
```

Disappearance, restriction, institutional adoption of AI and other consequential claims must not be published as verified facts without the required evidence and review.

## Persistence and recovery

Validation must confirm that:

- previous snapshots are not overwritten;
- append-only histories remain valid;
- interrupted batches can be resumed safely;
- manifests match persisted products;
- corrupted or inconsistent state blocks consolidation;
- methodology changes do not silently rewrite historical results;
- temporary workflow-artifact expiry does not remove durable scientific history.

## Public-interface validation

The public observatory and the future project showcase require separate acceptance checks.

The observatory must:

- consume validated or explicitly provisional products;
- present denominators, coverage and limitations;
- preserve multilingual terminology without using translated labels as data identifiers;
- remain functional with partial or historical datasets;
- avoid presenting technical implementation as empirical validation.

The showcase must present the project accurately and direct users to the observatory, repository and documentation without duplicating provisional analytical claims.

## Acceptance criteria for the first official cycle

The infrastructure should be considered ready only when:

- the complete automated quality suite passes;
- the controlled sample has been manually reviewed;
- critical false positives and known false-negative patterns have been addressed;
- eligibility and denominator rules are confirmed;
- the access index matches independent manual classification;
- indicator results can be reconstructed from their registered methodology;
- two-snapshot comparison behaves as intended;
- review and publication gates function correctly;
- historical persistence and recovery are verified;
- unresolved limitations are documented;
- the acceptance decision is recorded explicitly.

## Validation outputs

Each validation cycle must produce a concise, versioned report containing:

- scope and selected corpora;
- software, schema, indicator and methodology versions;
- tests executed;
- detector-performance findings;
- indicator and denominator verification;
- known limitations;
- corrections applied;
- unresolved risks;
- final acceptance status and responsible reviewer.

Operational validation is therefore both a software-quality process and a methodological audit. It is the principal gate preventing architectural readiness from being presented as scientific validation.

---

[← Previous: Scientific Indicators](07_scientific_indicators.md) · [Research Handbook](README.md) · [Next: Roadmap →](09_roadmap.md)
