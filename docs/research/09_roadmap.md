# Roadmap

## Purpose

The roadmap separates completed infrastructure work from validation, scientific production, public presentation and future expansion. It is not a promise of fixed dates. Progress depends on successful validation, data quality, institutional capacity and the availability of reproducible longitudinal observations.

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

Completion of this phase means that the architecture exists and can be exercised. It does not mean that every detector or indicator has completed empirical validation.

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
- explicit separation between implementation and empirical validation.

Residual work:

- complete editorial review of specialised documentation;
- remove obsolete analytical references;
- harmonise terminology across the public interface in Portuguese, English and Spanish;
- update citation metadata with a stable release and DOI after formal archival publication;
- review third-party-data and institutional-use constraints.

Exit criterion:

> External readers can understand, cite, reuse and critically evaluate the project without encountering conflicting definitions or exaggerated validation claims.

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

## Phase 4 — First Official Scientific Cycle

**Status: planned**

Objectives:

- freeze the validated methodological baseline;
- execute the first official observation cycle;
- publish the corpus, coverage and exclusion statement;
- preserve the official snapshot and manifests;
- publish indicator results with explicit denominators;
- release a versioned validation and methodology report;
- archive the release and datasets in an appropriate repository;
- update `CITATION.cff` with the stable version and DOI when available.

Exit criterion:

> The project has a citable and archived scientific baseline whose results can be traced to evidence, methodology and review decisions.

## Phase 5 — Longitudinal Scientific Observatory

**Status: planned**

Objectives:

- repeat validated observation cycles;
- preserve regular snapshots;
- build comparable longitudinal series;
- analyse access, interoperability, metadata, technology adoption and infrastructural change;
- publish versioned datasets and methodological reports;
- develop comparative studies across countries and institutional types;
- introduce new indicators only through documented validation gates.

Exit criterion:

> The project has accumulated sufficient compatible observations to support defensible longitudinal analyses rather than isolated technical demonstrations.

## Phase 6 — Public Showcase and Research Delivery

**Status: definition in progress**

The public showcase and the analytical observatory are separate products.

### Project showcase

The showcase should be a lightweight, fast and indexable public entry point containing:

- project identity and research question;
- concise explanation of the method and scientific contribution;
- current phase and limitations;
- selected outputs and publications;
- links to the observatory, repository, documentation and datasets;
- Portuguese, English and Spanish versions;
- stable domain and visual identity.

### Analytical observatory

The observatory should provide:

- research dashboards;
- corpus, coverage and exclusion information;
- indicator and methodology pages;
- archive-level technological profiles;
- timelines and period comparison;
- downloadable datasets and manifests;
- a documented query interface or public API when sustainability permits.

The current Streamlit deployment remains an analytical implementation under evaluation. Its performance, first-load latency, memory use, caching and mobile behaviour must be measured before it is adopted as the definitive public delivery environment.

Public delivery must consume validated or explicitly labelled provisional products. It must not read directly from unreviewed observations or bypass publication rules.

## Phase 7 — Comparative and Reusable Infrastructure

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

Cross-domain reuse requires new corpus rules and empirical validation. It must not be treated as automatic transfer of already validated conclusions.

## Current priority order

```text
1. Complete specialised editorial harmonisation
2. Audit and correct public terminology in three languages
3. Execute controlled real-world validation
4. Correct detectors and confirm denominator rules
5. Produce the formal operational-validation report
6. Establish a stable release baseline
7. Execute and archive the first official observation cycle
8. Define and implement the public showcase
9. Begin longitudinal scientific production
```

The project showcase may be prototyped before the first official cycle, but it must not present provisional results as established scientific findings.

## Decision gates

Each transition requires an explicit gate:

- **Technical gate:** software, schema, deployment and integrity checks pass.
- **Editorial gate:** public and specialised documentation are consistent.
- **Methodological gate:** populations, formulas, exclusions and interpretations match registered definitions.
- **Empirical gate:** evidence has been inspected on real corpora.
- **Publication gate:** sensitive claims satisfy evidence and review requirements.
- **Release gate:** outputs are versioned, archived and citable.
- **Scientific gate:** available data support the proposed interpretation.

This phased structure protects the project from presenting architectural readiness as empirical validation, a public interface as a scientific release, or technical expansion as methodological maturity.

---

[← Previous: Operational Validation](08_operational_validation.md) · [Research Handbook](README.md) · [Next: Future Research →](10_future_research.md)
