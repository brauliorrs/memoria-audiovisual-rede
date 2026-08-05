# Documentation Governance

## Purpose

This document defines the editorial hierarchy of **Memória Audiovisual em Rede** and prevents contradictory definitions across the research, analytics and technical documentation.

## Canonical hierarchy

### 1. Scientific narrative — `docs/research/`

This is the canonical source for:

- research problem and questions;
- conceptual and methodological framework;
- terminology used in scientific communication;
- corpus policy and unit of analysis;
- interpretation of indicators;
- operational-validation status;
- limitations, future research and collaboration.

When a public, academic or methodological statement appears in more than one place, the Research Handbook controls its interpretation.

### 2. Analytical specifications — `docs/analytics/`

This directory is the canonical source for:

- indicator identifiers and versions;
- formulas, numerators and denominators;
- coverage and suppression rules;
- sensitivity analysis;
- analytical persistence and reproducibility;
- computational contracts used by the analytics engine.

Analytics documents must not introduce a new scientific population, eligibility rule or interpretation without corresponding alignment in `docs/research/`.

### 3. Technical implementation and governance — `docs/digital-infrastructure-alignment/`

This directory is the canonical source for:

- implementation architecture;
- schemas and data contracts;
- evidence and provenance mechanisms;
- review, audit and publication workflows;
- technical backlog;
- operational and governance requirements.

Technical documents may describe implementation detail, but must not present automated detections as verified institutional facts.

### 4. Repository entry points

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
- **Public observatory:** the public interface and derived outputs.
- **Discovery Registry:** identified entities, including excluded and pending candidates.
- **Scientific Corpus:** eligible entities admitted to analytical populations.
- **Detected evidence:** an observation produced automatically or manually; not automatically a verified institutional fact.
- **Verified evidence:** evidence reviewed under the documented validation process.
- **Not identified:** no evidence was found in the assessed public surface; it does not prove institutional absence.
- **Not assessable:** the available route or evidence is insufficient for a valid classification.
- **Operational validation:** controlled testing of implemented components against real-world observations.

## Editorial rules

1. Separate implementation status from empirical validation status.
2. State denominators, exclusions and non-assessable cases for every reported indicator.
3. Do not describe a partial collection as a complete institutional archive.
4. Preserve the distinction between public accessibility and institutional existence.
5. Use versioned methodology for indicators and composite indexes.
6. Link claims to evidence, snapshots, publications and review decisions when available.
7. Record significant terminology or methodology changes in version history rather than silently replacing earlier definitions.
8. Avoid project-specific references to external collaborators or research programmes in generic architecture names unless a formal partnership exists.

## Review procedure

A documentation change affecting scientific interpretation should be checked in this order:

1. Research Handbook consistency.
2. Indicator and analytics consistency.
3. Technical architecture consistency.
4. README and executive-summary consistency.
5. Internal-link validation.

## Link validation

Run:

```bash
python scripts/check_markdown_links.py
```

The checker validates relative Markdown links and reports missing repository targets. External links remain subject to manual or dedicated network validation because availability and anti-bot behaviour can vary.

## Current editorial status

The international documentation is in operational validation. Automated checks may confirm structure and internal consistency, but they do not replace empirical validation of detectors, classifications or institutional claims.
