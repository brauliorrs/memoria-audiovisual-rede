# Analytics

## Purpose

The analytics layer converts validated snapshot products into reproducible research results. It does not collect data, alter historical observations, or replace human review. Its role is to calculate, persist, compare, and document indicators derived from consolidated evidence.

## Analytical architecture

```text
Validated coverage matrix
        ↓
Active indicator registry
        ↓
Versioned methodology registry
        ↓
Analytics engine
        ↓
Versioned indicator results
        ↓
Manifest and integrity hash
        ↓
Append-only indicator history
        ↓
Derived sensitivity analyses
```

The analytical layer is separated from collection and publication so that changes in formulas do not silently modify underlying evidence.

## Canonical analytical resources

The active machine-readable registries are:

```text
data/templates/analytics/indicator_registry.json
data/templates/analytics/methodology_registry.json
```

Executable analytical code is maintained under:

```text
src/memoria_audiovisual/analytics/
```

The Research Handbook controls scientific interpretation. The registries and executable code control identifiers, versions, dependencies, formulas, assessability rules, and computational behaviour.

## Indicator registry

Every active indicator is registered with a stable identifier and an explicit version. The registry prevents duplicate combinations of indicator identifier and version and enables deterministic execution.

Each result preserves at least:

- indicator identifier;
- indicator version;
- methodology version;
- snapshot identifier;
- title and category;
- value and unit;
- numerator and denominator, when applicable;
- eligible, assessable and excluded counts;
- status and notes;
- analytical dimensions and exclusions.

An indicator status of `implemented` means that executable code and controlled tests exist. It does not by itself establish empirical validation of the detector, denominator or institutional classification.

## Methodological versioning

Indicator code and indicator methodology are treated as related but distinct objects. A code change does not automatically imply that a scientific definition has changed, and a methodological revision must be documented explicitly.

A change in formula, weights, inclusion rules, assessability criteria, suppression rules or interpretation requires a new methodology version. Historical results remain linked to the methodology used when they were produced.

## Persistence

Analytical runs are stored under:

```text
data/digital_infrastructure/analytics/
├── indicator_history.jsonl
└── <snapshot_id>/
    ├── analytics_run.json
    ├── snapshot_indicators.json
    ├── manifest.json
    └── interoperability_sensitivity.json
```

The analytical key combines:

```text
snapshot_id
+ indicator_id
+ indicator_version
+ methodology_version
```

The same analytical key cannot be silently overwritten.

## Integrity

The manifest records the indicator count, output paths, result keys, generation time, methodology version, and a SHA-256 hash of the canonical indicator payload. Verification can therefore detect later alteration of persisted results.

## Evaluative states and denominators

The analytical layer preserves the distinction among detected, not detected on assessed surfaces, unknown, error, not assessable, missing observation and pending review.

A unit enters a denominator only when the active methodology defines it as eligible and assessable for that indicator. Error, missing-observation and not-assessable states are not silently converted into negative observations.

## Composite indexes

Composite indexes combine multiple documented components. Their weights, minimum data requirements, treatment of unavailable observations, and interpretation must be versioned.

The current interoperability index combines five components:

- IIIF;
- OAI-PMH;
- Dublin Core;
- Schema.org;
- JSON-LD.

The official version currently uses equal weights. Missing or non-assessable components are not automatically treated as absence. A corpus requires a minimum number of assessable components before a score can be calculated.

## Sensitivity analysis

Sensitivity analysis compares the official result with alternative, methodologically plausible weight scenarios. It is a derived analytical product and does not replace the official index.

The analysis reports:

- aggregate scores by scenario;
- corpus-level scores;
- score ranges;
- maximum corpus variation;
- rank changes;
- an operational interpretation of robustness.

## Scientific safeguard

The analytics layer must not create certainty that is absent from the evidence. Unknown, error, not-assessable, pending-review and missing-observation states remain distinguishable from confirmed absence.

## Reuse

Although the present implementation is applied to audiovisual archives, the engine is designed so that additional indicators can be registered without modifying the historical observation layer. Reuse in another institutional domain requires new corpus rules, detector validation and methodological assessment rather than automatic transfer.

---

[← Previous: Corpus Policy](05_corpus_policy.md) · [Research Handbook](README.md) · [Next: Scientific Indicators →](07_scientific_indicators.md)
