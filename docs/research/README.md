# Research Handbook

This handbook presents the scientific rationale, methodological framework, analytical design and validation strategy of **Memória Audiovisual em Rede**.

The repository contains a public-facing observatory interface and a reusable longitudinal research methodology. The handbook focuses on research design, evidence governance and reproducibility rather than on user-interface instructions.

For a concise international presentation, see the [Executive Summary](executive_summary.md).

For the relationship among the scientific, analytical and technical documentation layers, see [Documentation Governance](../DOCUMENTATION_GOVERNANCE.md).

## Contents

1. [Introduction](00_introduction.md)
2. [Research problem](01_research_problem.md)
3. [Scientific framework](02_scientific_framework.md)
4. [Methodological framework](03_methodological_framework.md)
5. [System architecture](04_system_architecture.md)
6. [Corpus policy](05_corpus_policy.md)
7. [Analytics](06_analytics.md)
8. [Scientific indicators](07_scientific_indicators.md)
9. [Operational validation](08_operational_validation.md)
10. [Roadmap](09_roadmap.md)
11. [Future research](10_future_research.md)
12. [Publications and research outputs](11_publications_and_outputs.md)
13. [Reuse and research collaboration](12_reuse_and_collaboration.md)

## Canonical role of this handbook

`docs/research/` is the canonical source for the scientific narrative, terminology, corpus policy, interpretation of indicators and description of the current validation phase.

The specialised layers complement this handbook:

- `docs/analytics/` specifies computational indicators, formulas, coverage and persistence;
- `docs/digital-infrastructure-alignment/` specifies schemas, implementation, evidence governance, workflows and backlog;
- `README.md` provides a concise international entry point and must remain consistent with this handbook.

When a scientific definition or interpretation differs across documents, this handbook and the documented governance rules control the public interpretation until the inconsistency is formally resolved.

## Core proposition

Audiovisual archives are not observed only as collections of objects. They are treated as evolving socio-technical infrastructures whose visibility, accessibility and preservation depend on software, standards, platforms, policies and institutional decisions.

The project therefore preserves not only collected records, but also the conditions under which those records became observable.

## Terminology used across the repository

To avoid ambiguity among the research, analytics and operational documentation, the following terms are used consistently:

- **Project** refers to *Memória Audiovisual em Rede* as the complete scientific initiative.
- **Research infrastructure** refers to the reusable longitudinal method, data contracts, evidence governance and analytical architecture.
- **Platform** refers to the implemented software system that operationalises the research infrastructure.
- **Public observatory** refers to the public-facing interface and derived outputs; it does not imply that every Phase 2 analytical component has already completed empirical validation.
- **Discovery Registry** contains identified entities, including those later excluded.
- **Scientific Corpus** contains only entities that satisfy the documented eligibility rules.
- **Eligible unit** satisfies the corpus inclusion rules.
- **Assessable unit** has sufficient public evidence for the parameter or indicator being calculated.
- **Detected evidence** is an automated or manually recorded observation; it is not automatically equivalent to a verified institutional fact.
- **Verified evidence** has completed the documented review process.
- **Not identified** means no evidence was found in the assessed surface; it does not prove institutional absence.
- **Not assessable** means the available route or evidence is insufficient for a valid classification.
- **Operational validation** is the current phase in which implementation behaviour and detector outputs are tested against controlled real-world observations.

## Documentation principles

- Separate empirical claims from methodological assumptions.
- Preserve the distinction between detected evidence and verified institutional facts.
- Version data, schemas and analytical methods.
- Keep excluded entities visible in the discovery record.
- Document limitations and non-assessable cases.
- Avoid silently replacing historical observations.
- Distinguish technical readiness from empirical validation.
- Require explicit denominators and exclusions for analytical claims.
- Link publications and datasets to their snapshots, corpus versions and methodologies.
- Treat cross-domain reuse as adaptation requiring new validation, not automatic transfer.

## Current phase

The core infrastructure and the first complete version of the Research Handbook are implemented in the feature branch associated with Pull Request #5.

The latest verified automated quality workflow passed dependency installation, Python compilation, unit tests and the deployment snapshot check. The project is now in **operational validation**, with emphasis on controlled real-world execution, manual evidence review, detector correction and verification of the scientific indicators.

Automated test success should not be interpreted as completed empirical validation of detector accuracy.

## Citation, reuse and contribution

- Citation metadata: [`CITATION.cff`](../../CITATION.cff)
- Licensing terms: [`LICENSE`](../../LICENSE)
- Contribution rules: [`CONTRIBUTING.md`](../../CONTRIBUTING.md)

Software code is licensed under MIT. Original documentation and project-produced published datasets are licensed under CC BY 4.0. Rights and restrictions attached to third-party source material remain unchanged.
