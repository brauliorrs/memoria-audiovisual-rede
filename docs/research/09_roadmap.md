# Roadmap

## Purpose

The roadmap separates completed infrastructure work from validation, scientific production, and future public delivery. It is not a promise of fixed dates. Progress depends on successful validation, data quality, institutional capacity, and the availability of reproducible longitudinal observations.

## Phase 1 — Core Research Infrastructure

**Status: substantially completed**

Main components:

- discovery and corpus definitions;
- normalisation and data contracts;
- provenance and evidence records;
- append-only persistence;
- snapshots and historical state;
- longitudinal comparison;
- event triage;
- human review;
- versioned public views;
- durable historical branch;
- workflow artifacts and operational reports;
- tests and technical documentation.

Completion of this phase means that the architecture exists. It does not mean that every detector has already been externally validated.

## Phase 2 — Operational Validation

**Status: in progress**

Objectives:

- stabilise the complete automated test suite;
- run a controlled heterogeneous corpus sample;
- inspect detector evidence manually;
- identify false positives and false negatives;
- validate multilingual restriction detection;
- verify corpus eligibility decisions;
- confirm the Audiovisual Archive Access Index;
- test two-snapshot longitudinal behaviour;
- validate review, publication, and persistence workflows;
- produce a formal validation report.

Exit criterion:

> The infrastructure can complete a controlled end-to-end cycle with documented, reproducible, and manually audited results.

## Phase 3 — Scientific Observatory

**Status: planned**

Objectives:

- execute the first official observation cycle;
- expand validated coverage across the research corpus;
- preserve regular snapshots;
- publish indicator results with explicit denominators;
- build comparable longitudinal series;
- analyse access, interoperability, metadata, technology adoption, and infrastructural change;
- prepare datasets and methodological reports for citation;
- develop comparative studies across countries and institutional types.

Exit criterion:

> The project has accumulated sufficient validated observations to support defensible scientific analyses rather than isolated technical demonstrations.

## Phase 4 — Public Research Delivery

**Status: planned**

Potential components:

- stable public data projection;
- research dashboard;
- documented query interface;
- downloadable datasets;
- indicator and methodology pages;
- archive-level technological profiles;
- versioned reports;
- public API, subject to sustainability and governance requirements.

Public delivery must consume validated publication products. It must not read directly from provisional observations or bypass review rules.

## Phase 5 — Comparative and Reusable Infrastructure

**Status: exploratory**

Potential directions:

- international comparative projects;
- adaptation to museums, libraries, public repositories, and cultural heritage platforms;
- institutional technology-provider mapping;
- digital preservation maturity research;
- AI governance and transparency indicators;
- technology diffusion and dependency analysis;
- network analysis of platforms, standards, and providers;
- reusable methodological packages for other research teams.

## Immediate priorities

The current priority order is:

```text
1. Green quality checks
2. Controlled real-world validation
3. Detector correction and methodological audit
4. Full validation report
5. Merge and stable baseline
6. First official observation cycle
7. Longitudinal scientific production
```

New functionality should be added only when it addresses a demonstrated validation gap or a clearly documented research need.

## Decision gates

Each phase requires an explicit decision gate:

- **Technical gate:** software and integrity checks pass.
- **Methodological gate:** results match documented definitions and exclusions.
- **Empirical gate:** evidence has been inspected on real corpora.
- **Publication gate:** sensitive claims satisfy review requirements.
- **Scientific gate:** the available data support the proposed interpretation.

This phased structure protects the project from presenting architectural readiness as empirical validation or public deployment maturity.

---

[← Previous: Operational Validation](08_operational_validation.md) · [Research Handbook](README.md) · [Next: Future Research →](10_future_research.md)
