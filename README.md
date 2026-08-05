# Memória Audiovisual em Rede

## An Open Scientific Research Infrastructure for the Longitudinal Observation of Digital Infrastructures in Audiovisual Archives

[Português](README.pt-BR.md) · [Executive Summary](docs/research/executive_summary.md) · [Research Handbook](docs/research/README.md) · [Public Observatory](https://memoria-audiovisual-rede-hv3dgxwqgaka2i6ahhmb5v.streamlit.app/)

> **Memória Audiovisual em Rede** is an open scientific research infrastructure that introduces a reusable longitudinal methodology for observing institutional digital infrastructures, demonstrated through the domain of audiovisual archives.

The project combines computational observation, human validation and reproducible analytics to study how audiovisual archives evolve over time in relation to accessibility, interoperability, metadata standards, digital preservation practices, artificial intelligence adoption and technological dependencies.

Although the current empirical application focuses on audiovisual archives, the methodological framework was intentionally designed to be reusable across other institutional domains requiring longitudinal observation of digital infrastructures.

## The research problem

Audiovisual archives increasingly depend on complex digital infrastructures, including content management systems, metadata standards, APIs, interoperability frameworks, cloud services, external platforms and artificial intelligence.

These infrastructures shape whether audiovisual heritage can be found, described, accessed, reused and preserved. Yet most existing initiatives provide catalogues, inventories or isolated datasets. They rarely document technological change over time, preserve complete provenance or expose reproducible evidence of infrastructural transformation.

**Memória Audiovisual em Rede addresses this gap by shifting from static inventory towards continuous scientific observation.**

## Guiding research question

> Under which infrastructural, institutional, technical and cultural conditions do audiovisual collections become visible, invisible, restricted or unstable in digital environments?

## Research questions

The infrastructure supports questions such as:

- How do audiovisual archives evolve technologically over time?
- Which interoperability and metadata standards are being adopted?
- Are archives becoming more accessible or more restrictive?
- Which technologies, services and public routes appear, disappear or become unstable?
- How transparent is the adoption of artificial intelligence in archival infrastructures?
- How can institutional digital infrastructures be documented through reproducible computational methods?

## Scientific contributions

- Longitudinal observation instead of static inventories.
- Snapshot-based reconstruction of technological change.
- Provenance for sources, acquisition methods, transformations and reviews.
- Human-reviewed evidence for sensitive or ambiguous events.
- Versioned data, schemas, indicators and analytical methodologies.
- Explicit separation between discovery records and the scientific corpus.
- Reproducible scientific indicators and composite indexes.
- Historical preservation without silent overwrite.
- Public research outputs traceable to observations and evidence.

## Research workflow

```text
Discovery
    ↓
Classification
    ↓
Corpus eligibility
    ↓
Observation and normalisation
    ↓
Provenance and snapshots
    ↓
Longitudinal comparison
    ↓
Event detection
    ↓
Human review when required
    ↓
Versioned publication
    ↓
Analytics engine
    ↓
Scientific indicators
    ↓
Research datasets
```

## Corpus policy

The project distinguishes between the **Discovery Registry** and the **Scientific Corpus**.

Every relevant entity identified during research may remain documented in the discovery layer. Only eligible audiovisual archives and institutional collections enter the analytical corpus.

Commercial image banks, paid stock repositories, commercial video banks, generic search engines, social media services and other out-of-scope entities may be identified and catalogued, but they are excluded from scientific denominators. Their exclusion is recorded rather than hidden.

This policy prevents commercial access models from distorting indicators designed to describe public audiovisual archives.

## Digital infrastructure observation

The platform records publicly observable evidence related to:

- content management systems and repository software;
- public APIs and service interfaces;
- IIIF, OAI-PMH and other interoperability mechanisms;
- Dublin Core, Schema.org, JSON-LD and other metadata formats;
- search systems and discovery mechanisms;
- authentication, registration, payment and formal-request barriers;
- external hosting and platform dependencies;
- public signals of artificial intelligence or automated cataloguing;
- changes, disappearance and recurrent unavailability over time.

The detectors are heuristic. Absence of a detected signal does not prove absence of a technology, and sensitive conclusions require human validation.

## Scientific indicators

| Dimension | Current indicators |
|---|---|
| Access | Audiovisual Archive Access Index |
| Infrastructure | API Coverage |
| Metadata | Dublin Core Coverage, Schema.org Coverage, JSON-LD Coverage |
| Interoperability | Interoperability Coverage, IIIF Coverage, OAI-PMH Coverage, Interoperability Index |

The **Audiovisual Archive Access Index** preserves the simple logic of the earlier platform: the percentage of eligible archives accessible without registration, authentication, payment or formal request, divided by the total number of eligible and assessable archives.

Every registered indicator must include a scientific question, selection rationale, formula, interpretation, limitations and a versioned methodological definition.

## Why longitudinal observation?

Digital infrastructures are not stable objects. Public routes disappear, APIs are introduced or withdrawn, access conditions change, platforms migrate and metadata practices evolve.

Periodic snapshots make it possible to reconstruct these transformations rather than replacing yesterday's observation with today's result. The platform preserves source, method, date, transformation, review and publication history for each cycle.

## Current status

**Current phase: Operational validation**

The following components are implemented in the feature branch associated with Pull Request #5:

- discovery and corpus classification;
- corpus eligibility policy;
- provenance and append-only historical records;
- periodic snapshots and longitudinal comparison;
- event triage and human-review workflows;
- versioned public views with controlled revisions;
- historical publication registry;
- analytics engine and methodological registry;
- scientific indicator catalogue;
- access and interoperability indicators;
- sensitivity analysis for the interoperability index.

Automated quality checks, including Python compilation, unit tests and the deployment snapshot check, have passed. The project has **not yet completed empirical validation of detector accuracy on a controlled sample of real archive websites**.

Current work therefore focuses on validating detectors, eligibility decisions and analytical outputs against real-world observations before the first official longitudinal cycle.

## Reproducibility

Every analytical result can be traced to:

- source and acquisition method;
- observation timestamp;
- corpus and snapshot identifiers;
- transformation history;
- evidence and human-review decisions;
- indicator and methodology versions;
- publication and revision history.

The project prioritises scientific reproducibility and methodological transparency over convenience.

## Documentation

For a concise presentation, read the [Executive Summary](docs/research/executive_summary.md).

The complete [Research Handbook](docs/research/README.md) includes:

- [Introduction](docs/research/00_introduction.md)
- [Research problem](docs/research/01_research_problem.md)
- [Scientific framework](docs/research/02_scientific_framework.md)
- [Methodological framework](docs/research/03_methodological_framework.md)
- [System architecture](docs/research/04_system_architecture.md)
- [Corpus policy](docs/research/05_corpus_policy.md)
- [Analytics](docs/research/06_analytics.md)
- [Scientific indicators](docs/research/07_scientific_indicators.md)
- [Operational validation](docs/research/08_operational_validation.md)
- [Roadmap](docs/research/09_roadmap.md)
- [Future research](docs/research/10_future_research.md)
- [Publications and research outputs](docs/research/11_publications_and_outputs.md)
- [Reuse and research collaboration](docs/research/12_reuse_and_collaboration.md)

Technical and operational documentation remains available under `docs/analytics/` and `docs/digital-infrastructure-alignment/`.

## Running locally

```bash
python -m venv .venv
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Validation:

```bash
python -m compileall -q app src scripts tests
python -m unittest discover -s tests -v
python scripts/check_deployment_ready.py
```

## Future directions

- international comparative studies;
- digital-preservation maturity indicators;
- AI-governance and transparency indicators;
- technology-diffusion and dependency analysis;
- network analysis of platforms, providers and institutions;
- public analytical dashboards and open APIs;
- reusable adaptations to other public and cultural digital infrastructures.

## Citation

Formal citation instructions will be added with the first stable research release and archived dataset.

## Author

**Bráulio Roberto Rangel da Silva**  
PhD in Communication Sciences  
Federal Institute of Paraíba, Brazil
