# Roadmap

## Purpose

The roadmap separates completed infrastructure work from validation, scientific production, public presentation and controlled geographic expansion. It is not a promise of fixed dates. Progress depends on successful validation, data quality, institutional capacity, reproducible longitudinal observations and completion of the documented expansion gates.

The operational order is maintained in the [Project Backlog](../project/BACKLOG.md). The scientific interpretation of regional and continental growth is defined in the [Scientific Expansion Policy](05a_scientific_expansion_policy.md).

## Phase 1 — Core Research Infrastructure

**Status: substantially completed**

Main components:

- discovery and corpus definitions;
- normalisation and data contracts;
- provenance and evidence records;
- append-only persistence;
- snapshots and historical state;
- longitudinal comparison;
- event triage and human review;
- versioned public outputs;
- durable historical records;
- analytical registries and indicator execution;
- tests and technical documentation.

Completion of this phase means that the architecture exists and can be exercised. It does not mean that every detector, indicator or expansion rule has completed empirical validation.

## Phase 2 — Scientific Presentation and Governance

**Status: first implementation cycle completed; residual review in progress**

Implemented components:

- repository licensing boundaries;
- machine-readable citation metadata;
- contribution and review rules;
- documentation-governance hierarchy;
- international README and Research Handbook entry points;
- automated documentation-link validation;
- multilingual interface auditing;
- explicit separation between implementation and empirical validation;
- documented corpus and scientific expansion policies.

Residual work:

- complete editorial review of specialised documentation;
- remove obsolete analytical references;
- harmonise terminology across the public interface in Portuguese, English and Spanish;
- update citation metadata with a stable release and DOI after formal archival publication;
- review third-party-data and institutional-use constraints;
- preserve consistency among the Research Handbook, backlog, audit reports and public interface.

Exit criterion:

> External readers can understand, cite, reuse and critically evaluate the project without encountering conflicting definitions, hidden denominator changes or exaggerated validation claims.

## Phase 3 — Operational Validation

**Status: in progress**

Objectives:

- maintain green automated quality controls;
- run a controlled heterogeneous corpus sample;
- inspect detector evidence manually;
- identify false positives and false-negative patterns;
- validate multilingual restriction detection;
- verify corpus-eligibility decisions;
- confirm the Audiovisual Archive Access Index;
- reconstruct indicator results from registered methodologies;
- test two-snapshot longitudinal behaviour;
- validate review, publication, persistence and recovery workflows;
- produce a formal validation report and acceptance decision.

Exit criterion:

> The infrastructure completes a controlled end-to-end cycle with documented, reproducible and manually audited results.

## Phase 4 — Complete Operational Baseline

**Status: priority before new continental activation**

The scientific reference corpus and the operationally active corpus must remain distinguishable. At the policy review of 5 August 2026, the platform records 58 reference entities, 55 active entities and 3 inactive entities.

Objectives:

- synchronise the canonical corpus, active registry, European queue and summaries;
- correct inconsistent denominators or stale totals;
- execute a complete cycle for all active corpora;
- record success, failure and non-assessable states without silent exclusion;
- materialise operational snapshots, coverage, analytics and manifests;
- initialise indicator history, provenance ledger and ingestion-batch records;
- preserve and publish the first complete operational baseline.

Exit criterion:

> Every active corpus appears in a complete auditable cycle and the resulting baseline can be reconstructed from evidence, manifests, corpus versions and denominator declarations.

## Phase 5 — European Queue and Expansion-Rule Validation

**Status: queue structured; operational execution pending**

Objectives:

- regenerate the current European products from the canonical corpus state;
- execute technical probing through a manual, restartable workflow;
- materialise probing evidence and errors;
- execute the scientific eligibility gate;
- create a human curatorial-review queue;
- prevent automatic promotion to the canonical corpus;
- simulate the proposed threshold of 20 newly approved corpora;
- test maximum waiting periods and proportional alternatives for regions with fewer assessable institutions;
- document the effect of incorporation batches on continental and global denominators;
- complete the European wave only after all scientific and governance gates are satisfied.

Exit criterion:

> European candidates have traceable evidence, eligibility status and curatorial decisions, and the expansion-readiness rule has been tested rather than merely asserted.

## Phase 6 — Controlled Continental Expansion

**Status: planned**

Discovery may continue across all regions in parallel. Activation follows the provisional sequence:

```text
1. Europe
2. North America
3. Latin America and the Caribbean
4. Africa
5. Asia
6. Oceania
```

Objectives:

- consolidate North America after completion of the European wave;
- prepare a dedicated Latin America and Caribbean inventory and candidate queue;
- maintain preparatory discovery for Africa, Asia and Oceania;
- prioritise aggregators before individual institutions when analytically appropriate;
- assess geographic, linguistic and infrastructural bias before activation;
- preserve transcontinental and global sources in a transversal queue;
- version every incorporation batch and denominator change.

The order may change only after a comparable inventory, scientific justification, coverage assessment and documented governance decision.

Exit criterion:

> A new region is activated through a versioned incorporation wave whose candidates, exclusions, evidence, reviews and denominator effects are publicly reconstructable.

## Phase 7 — First Official Scientific Release

**Status: planned**

Objectives:

- freeze the validated methodological baseline;
- execute an official observation cycle on a declared corpus version;
- publish the corpus, coverage, exclusions and expansion statement;
- preserve the official snapshot and manifests;
- publish indicator results with explicit denominators;
- release a versioned validation and methodology report;
- archive the release and datasets in an appropriate repository;
- update `CITATION.cff` with the stable version and DOI when available.

Exit criterion:

> The project has a citable and archived scientific baseline whose results can be traced to evidence, methodology, corpus version, expansion decisions and review records.

## Phase 8 — Longitudinal Scientific Observatory

**Status: planned**

Objectives:

- repeat validated observation cycles;
- preserve regular snapshots;
- build comparable longitudinal series;
- analyse access, interoperability, metadata, technology adoption and infrastructural change;
- publish versioned datasets and methodological reports;
- develop comparative studies across countries, continents and institutional types;
- introduce new indicators only through documented validation gates;
- distinguish changes caused by institutional evolution from changes caused by corpus expansion.

Exit criterion:

> The project has accumulated sufficient compatible observations to support defensible longitudinal analyses rather than isolated technical demonstrations.

## Phase 9 — Public Showcase and Research Delivery

**Status: definition in progress**

The public showcase and the analytical observatory are separate products.

### Project showcase

The showcase should be a lightweight, fast and indexable public entry point containing:

- project identity and research question;
- concise explanation of the method and scientific contribution;
- current phase and limitations;
- corpus and expansion-policy statement;
- selected outputs and publications;
- links to the observatory, repository, documentation and datasets;
- Portuguese, English and Spanish versions;
- stable domain and visual identity.

### Analytical observatory

The observatory should provide:

- research dashboards;
- corpus, coverage, exclusion and expansion information;
- indicator and methodology pages;
- archive-level technological profiles;
- timelines and period comparison;
- downloadable datasets and manifests;
- a documented query interface or public API when sustainability permits.

The current Streamlit deployment remains an analytical implementation under evaluation. Its performance, first-load latency, memory use, caching and mobile behaviour must be measured before it is adopted as the definitive public delivery environment.

Public delivery must consume validated or explicitly labelled provisional products. It must not read directly from unreviewed observations, bypass publication rules or present queued candidates as active scientific corpora.

## Phase 10 — Comparative and Reusable Infrastructure

**Status: exploratory**

Potential directions:

- international comparative projects;
- adaptation to museums, libraries, public repositories and cultural-heritage platforms;
- institutional technology-provider mapping;
- digital-preservation maturity research;
- AI-governance and transparency indicators;
- technology-diffusion and dependency analysis;
- network analysis of platforms, standards and providers;
- reusable methodological packages for other research teams.

Cross-domain reuse requires new corpus rules, expansion policy and empirical validation. It must not be treated as automatic transfer of already validated conclusions.

## Current priority order

```text
1. Synchronise the canonical corpus, active registry and European products
2. Correct the inconsistent active-corpus totals
3. Execute a complete cycle for all active corpora
4. Materialise operational analytics, history, ledger and ingestion batches
5. Operationalise European probing and scientific eligibility
6. Open controlled human curatorial review
7. Simulate and validate the 20-corpus readiness threshold
8. Complete the European wave
9. Consolidate North America
10. Prepare the Latin America and Caribbean queue
11. Continue preparatory discovery for Africa, Asia and Oceania
12. Activate versioned public delivery and the first official scientific release
```

The public showcase may be prototyped before the first official release, but it must not present provisional results, queued candidates or unvalidated expansion rules as established scientific findings.

## Decision gates

Each transition requires an explicit gate:

- **Technical gate:** software, schema, deployment and integrity checks pass.
- **Editorial gate:** public and specialised documentation are consistent.
- **Methodological gate:** populations, formulas, exclusions, expansion rules and interpretations match registered definitions.
- **Empirical gate:** evidence has been inspected on real corpora.
- **Corpus gate:** candidates satisfy eligibility and curatorial requirements.
- **Expansion gate:** the regional batch, threshold rule, denominator effects and previous baseline are documented.
- **Publication gate:** sensitive claims satisfy evidence and review requirements.
- **Release gate:** outputs are versioned, archived and citable.
- **Scientific gate:** available data support the proposed interpretation.

This phased structure protects the project from presenting architectural readiness as empirical validation, a public interface as a scientific release, technical accessibility as corpus eligibility, or geographic expansion as methodological maturity.

---

[← Previous: Operational Validation](08_operational_validation.md) · [Research Handbook](README.md) · [Next: Future Research →](10_future_research.md)
