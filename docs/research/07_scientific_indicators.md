# Scientific Indicators

## Role of indicators

Indicators translate documented observations into comparable research measures. They do not replace the underlying evidence and must always be interpreted together with their denominator, exclusions, limitations, assessability rules, and methodology version.

Every indicator admitted to the active analytical registry must have a scientific definition explaining:

- the research question it addresses;
- why it was selected;
- the observed dimension;
- the variables used;
- the calculation rule;
- the eligible and assessable population;
- suppression and exclusion rules;
- how the result should be interpreted;
- what the result does not measure;
- its relationship with other indicators;
- the indicator and methodology versions.

An indicator marked as `implemented` has executable code and controlled tests. This status does not by itself mean that detector accuracy or the empirical result has been validated on a representative sample of real institutions.

## Audiovisual Archive Access Index

### Research question

What proportion of eligible audiovisual archives can be accessed without registration, authentication, payment, or formal request?

### Formula

```text
eligible archives with immediate open access
──────────────────────────────────────────── × 100
eligible and assessable audiovisual archives
```

### Inclusion rule

An archive enters the numerator when the observed access route does not require registration, login, payment, subscription, institutional authorisation, email request, form submission, or another formal mediation procedure.

### Corpus rule

Commercial paid image or video banks may be identified and catalogued in the Discovery Registry, but they do not enter the Scientific Corpus and therefore do not enter either the numerator or denominator.

### Interpretation

The index measures an institutional access barrier at archive level. It does not measure collection size, metadata quality, technical performance, API availability, interoperability, or the proportion of individual records available online.

## API Coverage

### Research question

What proportion of assessable corpora shows evidence of a programmatic access service?

The indicator is relevant because APIs can support reuse, integration, computational research, and machine-readable access. Detection does not demonstrate that an API is open, complete, documented, stable, or unrestricted.

## Interoperability Coverage

### Research question

What proportion of assessable corpora shows evidence of at least one recognised interoperability mechanism?

This is a broad coverage measure. It must not be interpreted as proof of full technical conformity or interoperability across the entire archive.

## Specific pattern coverage

The platform currently records separate indicators for:

- IIIF;
- OAI-PMH;
- Dublin Core;
- Schema.org;
- JSON-LD.

A positive result requires an explicit recognised value in the relevant observation group. A generic detected status is not sufficient when the specific pattern cannot be identified.

### IIIF Coverage

IIIF is observed because it can support interoperable delivery, description, comparison, and reuse of digital objects. Detection does not prove complete implementation or unrestricted access to audiovisual content.

### OAI-PMH Coverage

OAI-PMH is observed because it enables structured metadata harvesting. Detection does not demonstrate complete, current, or high-quality metadata exposure.

### Dublin Core Coverage

Dublin Core is observed as a widely used descriptive metadata framework. Presence does not by itself demonstrate completeness, consistency, or semantic quality.

### Schema.org Coverage

Schema.org is observed because structured web markup can improve machine readability and discoverability. Detection does not guarantee search-engine visibility or comprehensive description.

### JSON-LD Coverage

JSON-LD is observed as a mechanism for publishing linked structured data on the web. Presence does not necessarily imply the use of shared vocabularies or effective semantic interoperability.

## Interoperability Index

### Research question

How mature is the observable adoption of selected interoperability and structured-metadata components across eligible corpora?

The current official version combines IIIF, OAI-PMH, Dublin Core, Schema.org, and JSON-LD with equal weights. The score ranges from 0 to 100.

A corpus is scored only when the minimum number of components is assessable. Available component weights may be renormalised, but missing or non-assessable evidence is not automatically converted into zero.

The aggregate value is the mean of eligible corpus scores that satisfy the minimum coverage rule.

### Limitations

The index is a synthetic measure. It does not prove implementation quality, protocol conformity, coverage of the complete collection, organisational capacity, public access, or preservation maturity.

## Denominators and evaluative states

Unless a specific methodology states otherwise, the analytical framework distinguishes:

- detected;
- not detected on the assessed surface;
- unknown;
- error;
- not assessable;
- missing observation;
- pending human review, when applicable.

`Not detected` describes the result of the declared observation procedure. It is not equivalent to verified institutional absence. Error, not-assessable, missing-observation, and pending-review states do not enter denominators as confirmed negatives unless a versioned methodology explicitly defines another treatment.

Excluded corpora and exclusion reasons remain visible in analytical outputs.

## Versioning and comparability

A longitudinal comparison is valid only when the indicator identifier, indicator version, methodology version, corpus rules, denominator rules, and assessability criteria are compatible. Methodological breaks must be reported rather than hidden inside a continuous series.

## Sources of truth

The active machine-readable scientific indicator registry is stored in:

```text
data/templates/analytics/indicator_registry.json
```

The machine-readable methodology registry is stored in:

```text
data/templates/analytics/methodology_registry.json
```

Executable indicator implementations are maintained under:

```text
src/memoria_audiovisual/analytics/
```

The Research Handbook controls scientific interpretation. The registries control identifiers, versions, dependencies, formulas, and executable methodological contracts. Historical or transitional catalogue files must not be treated as the active source of truth unless explicitly referenced by the current registry.

---

[← Previous: Analytics](06_analytics.md) · [Research Handbook](README.md) · [Next: Operational Validation →](08_operational_validation.md)
