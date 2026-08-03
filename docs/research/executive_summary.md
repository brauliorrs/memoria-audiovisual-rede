# Executive Summary

## Memória Audiovisual em Rede

**Memória Audiovisual em Rede** is an open scientific research infrastructure for the longitudinal observation of the digital infrastructures that support audiovisual archives.

Its central contribution is not a static catalogue, but a reusable methodology for documenting how institutional digital infrastructures evolve over time. The current empirical domain is audiovisual heritage, where access, visibility and preservation increasingly depend on software platforms, metadata standards, interoperability protocols, external services, artificial intelligence and institutional access policies.

## The research problem

Audiovisual archives are commonly described through their collections, institutions or public catalogues. Much less attention is given to the technical and institutional conditions that make those collections digitally visible, accessible, interoperable or unstable.

Static inventories cannot adequately document:

- the adoption or abandonment of technologies;
- changes in access restrictions;
- the appearance or disappearance of APIs and public routes;
- shifts in metadata and interoperability practices;
- recurring unavailability;
- the gradual incorporation of AI-related systems;
- the loss of previously observable digital evidence.

The project addresses this limitation through periodic, reproducible observation.

## Methodological approach

The infrastructure combines:

- discovery and classification of digital entities;
- explicit corpus eligibility decisions;
- computational observation of public surfaces;
- provenance for sources, methods and transformations;
- periodic snapshots;
- longitudinal comparison;
- cautious event detection;
- human review for sensitive or material claims;
- append-only historical records;
- versioned public views with controlled revisions;
- reproducible scientific indicators.

The system separates discovery from corpus inclusion. Commercial image and video banks may be identified and catalogued, but they do not enter the scientific corpus or the denominators of archive indicators.

## Analytical dimensions

The current analytical layer includes indicators for:

- public access without registration, payment or formal request;
- API availability;
- interoperability signals;
- IIIF and OAI-PMH adoption;
- Dublin Core, Schema.org and JSON-LD;
- a composite interoperability index;
- sensitivity to alternative weighting schemes.

Each indicator must include a scientific question, selection rationale, formula, interpretation, limitations and methodology version.

## Longitudinal value

The platform preserves previous states rather than replacing them. This allows researchers to investigate not only what is currently visible, but how infrastructures change over time.

Potential longitudinal questions include:

- Are audiovisual archives becoming more publicly accessible?
- Which standards are diffusing across institutions and countries?
- Which technologies or access routes disappear?
- Do technical interoperability and effective public access evolve together?
- How transparent is institutional AI adoption?

## Current stage

The core architecture, governance mechanisms, analytical engine and research documentation are implemented in the feature branch associated with Pull Request #5.

Automated quality checks have passed, including dependency installation, Python compilation, unit tests and the deployment snapshot check. This confirms structural and test-suite readiness, but it does not yet establish empirical detector accuracy on real archive websites.

The project is therefore in **operational validation**. The immediate priorities are:

1. select a small and representative sample of real corpora;
2. establish manually reviewed expected observations for that sample;
3. run the controlled collection without initiating the complete corpus cycle;
4. compare detector outputs with the reviewed expectations;
5. record false positives, false negatives and inconclusive cases;
6. verify eligibility decisions and the Audiovisual Archive Access Index denominator;
7. test snapshot, review and publication flows end to end;
8. correct only the defects revealed by the controlled validation.

## Reuse and collaboration

Although demonstrated through audiovisual archives, the framework may be adapted to other domains that require longitudinal observation of institutional digital infrastructures, including cultural heritage institutions, public digital services, governmental repositories and research data infrastructures.

Adaptation requires a new unit of analysis, corpus policy, observation schema, validation sample and methodology version. The current implementation should therefore be understood as a transferable framework, not as a validated analysis of every possible institutional domain.

## Project position

Memória Audiovisual em Rede shifts the study of audiovisual archives from static description toward continuous observation of the socio-technical conditions under which digital memory becomes accessible, restricted, unstable or invisible.

---

[Main README](../../README.md) · [Research Handbook](README.md) · [Introduction](00_introduction.md)
