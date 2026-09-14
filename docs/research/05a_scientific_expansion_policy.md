# Scientific Expansion Policy

## Purpose

The expansion policy defines how the observatory moves from a validated baseline to new regional and continental coverage without turning discovery into automatic incorporation, changing analytical denominators opportunistically, or reproducing geographic bias through technical convenience.

Expansion is treated as part of the scientific method. It affects:

- which entities are observed;
- which units enter the scientific corpus;
- when denominators change;
- which comparisons remain valid across snapshots;
- how regional underrepresentation is identified and corrected;
- how negative, inaccessible and unresolved cases remain visible.

This chapter complements the [Corpus Policy](05_corpus_policy.md). The corpus policy defines eligibility at entity level; the expansion policy defines when and how eligible entities may enter new observation waves.

## Status of the policy

The principles and gates described here are the current governance policy of the platform.

Two elements remain provisional and require operational simulation before they can be treated as stable rules:

1. the threshold of 20 newly approved corpora for opening a continental round;
2. the current sequence of continental activation.

They are operational hypotheses designed to make expansion auditable. They are not universal scientific constants and may be revised only through a documented methodological decision.

## Why expansion requires a scientific policy

Uncontrolled expansion can produce at least five methodological distortions:

1. **opportunistic sampling**, in which technically easy sources are incorporated first regardless of scientific relevance;
2. **denominator drift**, in which published proportions change because the corpus changed without a versioned decision;
3. **regional concentration**, in which Europe and North America dominate because their digital infrastructures are easier to identify and collect;
4. **level mixing**, in which aggregators, custodial archives, directories and commercial services are treated as equivalent units;
5. **silent exclusion**, in which inaccessible or negative cases disappear from the research record.

The expansion policy therefore separates discovery, technical feasibility, scientific eligibility, curatorial approval and corpus incorporation.

## Expansion layers

```text
Global discovery
      ↓
Regional or continental radar
      ↓
Ranked candidate queue
      ↓
Technical probing
      ↓
Scientific eligibility gate
      ↓
Human curatorial review
      ↓
Approved incorporation batch
      ↓
Versioned active corpus
      ↓
Published snapshot and denominators
```

Each layer has a different analytical meaning.

### Global discovery

Sources may be identified in any region at any time. Discovery can occur in parallel and does not depend on the current activation wave.

### Regional or continental radar

The radar preserves relevant entities, directories, networks, aggregators and institutions even when they are not yet candidates for incorporation.

### Ranked candidate queue

The queue contains units that require individual assessment. A directory or membership list may generate candidates, but the directory itself is not automatically counted as one or more scientific corpora.

### Technical probing

Technical probing records whether a public, reproducible and ethically acceptable route exists. Technical success does not establish scientific eligibility.

### Scientific eligibility gate

The gate evaluates identity, institutional role, audiovisual relevance, assessability, evidence, duplication and methodological compatibility.

### Human curatorial review

Ambiguous, sensitive or consequential cases require human review. Automated processes may prepare evidence and recommendations but cannot promote a candidate directly into the canonical corpus.

### Approved incorporation batch

Approved candidates enter through a versioned batch with an explicit decision record. Corpus code, active status and denominators are not changed silently.

## Core principles

### Discovery may be parallel; activation is controlled

Research and source identification may proceed across all continents simultaneously. Activation of new incorporation waves is sequential so that the platform can preserve a stable baseline, complete validation and document denominator changes.

### Aggregators before individual institutions

Within a regional wave, the platform prioritises continental, supranational, national or large-scale aggregators when they:

- provide comparable access to multiple institutions;
- have a declared analytical role;
- preserve institution-level distinctions;
- offer a reproducible route compatible with the methodology.

Individual archives are then used to fill coverage gaps, represent institutions not covered by aggregators, or provide justified methodological contrast.

This priority is not an assumption that aggregators are superior archives. It is a coverage strategy that must preserve the distinction between aggregator-level and institution-level analysis.

### Technical convenience is not sufficient

Ease of collection, availability of an API, use of a familiar language or compatibility with existing software cannot be the sole basis for regional priority.

Scientific relevance, regional balance, institutional diversity, language, access conditions, infrastructure inequality and coverage gaps must also be considered.

### No automatic promotion

No crawler, queue, workflow, score or model may automatically:

- add a candidate to the canonical corpus;
- set an entity as active;
- alter a published denominator;
- treat a discovery source as a scientific unit;
- convert technical accessibility into institutional eligibility.

### Negative and unresolved cases remain documented

Rejected, inaccessible, duplicated, non-assessable and pending candidates remain in the discovery and decision records with evidence and rationale. Expansion must not erase unsuccessful attempts.

## Current baseline

At the policy review of 5 August 2026, the platform distinguishes:

- **58 entities** in the frozen scientific reference corpus;
- **55 operationally active entities**;
- **3 inactive entities**;
- discovery sources, radar records and candidates outside the active denominator.

These values describe a versioned state, not permanent totals. Future publications must identify the corpus version and snapshot to which their denominators refer.

## Readiness threshold of 20 approved corpora

The current operational proposal is to open a new continental observation round when there are at least **20 newly eligible, approved and validated corpora from the same continent** since the previous completed round.

Only units that have completed the full incorporation path count toward the threshold.

The following do not count:

- discovery sources and membership directories;
- radar records;
- duplicates;
- candidates with insufficient evidence;
- non-assessable candidates;
- methodological negatives;
- candidates awaiting curatorial review;
- technically reachable sources that failed scientific eligibility;
- transcontinental sources not assigned through an explicit decision.

### Interpretation of the threshold

The threshold is intended to:

- avoid changing denominators after every isolated incorporation;
- create meaningful regional batches;
- support efficient re-observation and validation;
- make readiness visible and measurable;
- reduce ad hoc expansion decisions.

It must not be used to indefinitely exclude regions with fewer available institutions or weaker digital infrastructure.

Before the threshold becomes stable, the platform must test:

- how it behaves with the European queue;
- whether 20 units produce a meaningful analytical batch;
- whether a maximum waiting period is needed;
- whether proportional thresholds are required for regions with fewer assessable sources;
- whether a round reobserves all active units in the continent or only new incorporations;
- how denominator changes affect global and continental indicators.

Any exception must be defined before use and recorded as a methodological version, not decided retroactively to admit a preferred candidate.

## Provisional continental sequence

The current activation sequence is:

```text
0. Consolidation of the current baseline
1. Europe
2. North America
3. Latin America and the Caribbean
4. Africa
5. Asia
6. Oceania
```

### Interpretation

- **Baseline consolidation** means synchronising the canonical corpus, queues, snapshots and denominators before new incorporation.
- **Europe** is the first active expansion wave because it already has the most developed queue and methodological preparation.
- **North America** follows because the AAPB has already established an initial extra-European reference point.
- **Latin America and the Caribbean** follow as a scientifically relevant multilingual and institutionally diverse region for which discovery work has begun, while sources such as Iberarchivos remain discovery and curatorial references rather than automatically incorporated audiovisual corpora.
- **Africa** precedes expansion driven only by technical ease in Asia or Oceania in order to counter the risk of reproducing concentration in digitally advantaged regions.
- **Asia** and **Oceania** require their own comparable inventories of aggregators, languages, access regimes and institutional sources.

The sequence is provisional. It may change only after:

1. a comparable inventory of sources and infrastructures;
2. a scientific justification;
3. assessment of coverage and representational consequences;
4. a documented governance decision;
5. preservation of the previous policy version.

## Transcontinental and global sources

Worldwide, supranational or transcontinental sources remain in a transversal queue.

They do not automatically count toward one continent. Their treatment requires an explicit decision defining:

- analytical level;
- geographic attribution, if any;
- overlap with regional aggregators;
- duplicate-control rule;
- contribution to regional and global denominators;
- publication interpretation.

## Gate for activating a new regional wave

A new wave may be activated only when the following conditions are satisfied:

1. the canonical corpus, active corpus, queues and summaries are synchronised;
2. the current active corpus has completed an auditable observation cycle;
3. operational snapshots, coverage, analytics and manifests are materialised;
4. provenance, ledger and ingestion-batch records are available;
5. the regional queue has ranking, source evidence and documented provenance;
6. technical probing has been completed for the proposed batch;
7. the scientific eligibility gate has been executed;
8. human curatorial review has been completed;
9. no unresolved integrity block prevents incorporation;
10. the previous baseline remains preserved and publishable;
11. the effect on continental and global denominators has been documented;
12. the incorporation batch has a versioned decision record.

Passing tests or reaching a numerical threshold alone is not sufficient.

## Denominator governance

Every incorporation wave must produce a new corpus version or equivalent versioned declaration.

Published analytical products must preserve:

- the previous corpus definition;
- the new corpus definition;
- added, removed, activated and deactivated units;
- eligibility and review decisions;
- continental and global denominator changes;
- affected indicators;
- snapshot and methodology versions;
- interpretation limits introduced by the change.

Historical results are not recalculated silently. Recalculation, when scientifically justified, must be published as a new analytical product linked to the revised denominator.

## Geographic and linguistic safeguards

The platform must actively inspect whether expansion decisions reproduce structural inequalities in digital visibility.

Relevant checks include:

- geographic concentration of active units;
- language concentration in interfaces and metadata;
- dependence on English-language discovery routes;
- underrepresentation caused by absent APIs or weak indexing;
- prevalence of registration, payment or formal-request barriers;
- differences between national infrastructures and small independent archives;
- visibility of Indigenous, regional, minority-language and postcolonial collections;
- concentration in large broadcasters, national institutions or well-funded aggregators.

A low level of detectable evidence in a region may reflect infrastructural inequality rather than absence of audiovisual memory. The policy must not convert unequal digital visibility into an assumption of institutional nonexistence.

## Decision record

A regional activation decision should record at least:

- policy version;
- region or continent;
- previous completed round;
- approved-corpus count;
- threshold rule applied;
- exceptions, if any;
- candidate and approved-unit lists;
- evidence and review references;
- corpus version before and after incorporation;
- affected denominators;
- responsible reviewer or governance process;
- decision date;
- next review trigger.

## Current operational order

The policy is implemented through the following priority order:

```text
1. Synchronise the canonical corpus and European products
2. Complete an operational cycle for all active corpora
3. Materialise operational analytics, history, ledger and ingestion batches
4. Operationalise European technical probing and eligibility
5. Simulate and validate the 20-corpus readiness rule
6. Complete the European wave
7. Consolidate North America
8. Prepare the Latin America and Caribbean queue
9. Continue preparatory discovery for Africa, Asia and Oceania
```

This order prevents new feature development or geographic expansion from preceding the execution of scientific and governance components that already exist.

## Canonical references

Operational priorities and implementation status are maintained in:

- [Project Backlog](../project/BACKLOG.md);
- [Integration and Expansion Audit, 5 August 2026](../audit/platform_integration_expansion_audit_2026-08-05.md).

The Research Handbook controls the scientific interpretation. The backlog controls current execution priority. If the policy changes, both layers must be updated and the previous version must remain traceable.

---

[← Previous: Corpus Policy](05_corpus_policy.md) · [Research Handbook](README.md) · [Next: Analytics →](06_analytics.md)
