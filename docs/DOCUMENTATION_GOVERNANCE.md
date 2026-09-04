# Documentation Governance

## Purpose

This document defines the editorial hierarchy of **Memória Audiovisual em Rede** and prevents contradictory definitions across the research, analytical, experimental and technical documentation.

## Canonical hierarchy

### 1. Scientific narrative — `docs/research/`

This is the canonical source for:

- research problem and questions;
- conceptual and methodological framework;
- terminology used in scientific communication;
- corpus policy and unit of analysis;
- interpretation of indicators;
- operational-validation status;
- experiment interpretation and scientific-use boundaries;
- limitations, future research and collaboration.

When a public, academic or methodological statement appears in more than one place, the Research Handbook controls its scientific interpretation.

### 2. Machine-readable analytical specifications

The current canonical analytical specifications are:

```text
data/templates/analytics/indicator_registry.json
data/templates/analytics/methodology_registry.json
src/memoria_audiovisual/analytics/
```

Together, these resources control:

- indicator identifiers and versions;
- formulas, numerators and denominators;
- coverage, assessability and suppression rules;
- dependencies and sensitivity analysis;
- analytical persistence and reproducibility;
- executable contracts used by the analytics engine.

A future `docs/analytics/` directory may provide explanatory technical documentation, but it must not become an independent source of scientific populations, eligibility rules or interpretations. Such definitions require alignment with `docs/research/` and the active machine-readable registries.

### 3. Experimental validation records

Empirical calibration, blind validation, operational pilots and diagnostic replays are indexed in:

```text
data/digital_infrastructure/ai_experiments/experiment_registry_v1.json
```

Detailed human-readable experiment reports are stored under:

```text
docs/research/experiments/
```

The scientific policy governing these records is:

```text
docs/research/13_experiment_registry.md
```

Experimental artifacts may include prediction files, blinded review queues, human-review decisions, amendments, conclusions, comparison reports and diagnostic replays.

These records control **what was executed and preserved**, but their scientific interpretation remains subordinate to the Research Handbook. A machine-readable metric must not be presented more broadly than the experiment design supports.

### 4. Technical implementation and governance — `docs/digital-infrastructure-alignment/`

This directory is the canonical source for:

- implementation architecture;
- schemas and data contracts;
- evidence and provenance mechanisms;
- review, audit and publication workflows;
- technical backlog;
- operational and governance requirements.

Technical documents may describe implementation detail, but must not present automated detections as verified institutional facts.

### 5. Repository entry points

- `README.md`: concise international presentation in English.
- `README.pt-BR.md`: Portuguese presentation.
- `docs/research/executive_summary.md`: short scientific briefing.
- `CITATION.cff`: machine-readable citation metadata.
- `CONTRIBUTING.md`: contribution and review rules.
- `LICENSE`: licensing boundaries.

## Controlled terminology

The following definitions apply throughout the repository:

- **Project:** the complete scientific initiative Memória Audiovisual em Rede.
- **Research infrastructure:** the reusable method, evidence governance, data contracts and analytical architecture.
- **Platform:** the implemented software system.
- **Public observatory:** the public analytical interface and derived outputs.
- **Public showcase:** the lightweight institutional entry point planned to present the project and direct users to the observatory, repository and publications.
- **Discovery Registry:** identified entities, including excluded and pending candidates.
- **Scientific Corpus:** eligible entities admitted to analytical populations.
- **Eligible unit:** an entity that satisfies the documented corpus-admission rules.
- **Assessable unit:** an eligible unit for which the declared observation procedure produced sufficient evidence for the relevant classification.
- **Detected evidence:** an observation produced automatically or manually; not automatically a verified institutional fact.
- **Verified evidence:** evidence reviewed under the documented validation process.
- **Not identified:** no evidence was found through the declared procedure on the assessed public surfaces; it does not prove institutional absence.
- **Not assessable:** the available route or evidence is insufficient for a valid classification.
- **Operational validation:** controlled testing of implemented components against real-world observations.
- **Implemented indicator:** an indicator with executable code and controlled tests; the label does not by itself assert empirical validation.
- **Registered experiment:** a versioned empirical execution with stable identity, provenance, artifacts, deviations, limitations and a bounded scientific interpretation.
- **Calibration experiment:** an experiment whose observations may be used to modify the mechanism; its sample must not then be presented as an independent post-calibration estimate of generalisation performance.
- **Diagnostic replay:** a reconstruction used to investigate behaviour when the original execution or inputs are incomplete; it is not automatically equivalent to the original run.

## Editorial rules

1. Separate implementation status from empirical validation status.
2. State denominators, exclusions and non-assessable cases for every reported indicator.
3. Do not describe a partial collection as a complete institutional archive.
4. Preserve the distinction between public accessibility and institutional existence.
5. Use versioned methodology for indicators and composite indexes.
6. Link claims to evidence, snapshots, publications and review decisions when available.
7. Record significant terminology or methodology changes in version history rather than silently replacing earlier definitions.
8. Avoid project-specific references to external collaborators or research programmes in generic architecture names unless a formal partnership exists.
9. Do not treat legacy or transitional catalogue files as active sources of truth when the current registries identify another canonical resource.
10. Distinguish the public showcase from the analytical observatory and from the scientific repository.
11. Register scientifically relevant experiments and preserve protocol deviations; do not replace missing original artifacts with retrospective reconstructions presented as if they were the original execution.
12. For blind automated validation, preserve frozen predictions and integrity identifiers before human review whenever performance is intended to be estimated.

## Review procedure

A documentation change affecting scientific interpretation should be checked in this order:

1. Research Handbook consistency.
2. Experiment registry and detailed experiment-report consistency when empirical validation is involved.
3. Active indicator and methodology registry consistency.
4. Executable analytics consistency.
5. Technical architecture consistency.
6. README and executive-summary consistency.
7. Internal-link validation.

## Link validation

Run:

```bash
python scripts/check_markdown_links.py
```

The checker validates relative Markdown links and reports missing repository targets. External links remain subject to manual or dedicated network validation because availability and anti-bot behaviour can vary.

## Current editorial status

The international documentation is in operational validation. Automated checks confirm syntax, internal links and repository-level consistency, but they do not replace empirical validation of detectors, classifications or institutional claims.

The experiment registry now provides a durable distinction among calibration, blind validation, operational pilots, diagnostic replays and valid scientific conclusions. A full cross-document audit remains required whenever a registered experiment changes the interpretation or activation status of a scientific component.
