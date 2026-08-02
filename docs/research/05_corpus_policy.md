# 05 — Corpus Policy

## Purpose

The corpus policy defines which discovered entities become part of the scientific corpus and which remain documented outside it. This distinction protects analytical validity, preserves transparency and prevents the platform from treating every audiovisual website as an archive.

## Two-layer model

```text
Discovery Registry
    ↓
Classification
    ↓
Eligibility decision
    ↓
Research Corpus
```

The Discovery Registry is intentionally broader than the Research Corpus.

## Discovery Registry

The registry may contain:

- audiovisual archives;
- film archives and cinematheques;
- broadcasting archives;
- university repositories;
- museums with audiovisual collections;
- national and transnational aggregators;
- commercial image or video banks;
- external platforms;
- candidates awaiting validation;
- inactive or inaccessible entities;
- duplicates and out-of-scope cases.

Discovery does not imply analytical inclusion.

## Eligibility principle

An entity is eligible when its institutional or custodial role is compatible with the research object and there is sufficient evidence to observe its public digital infrastructure within the declared methodology.

Typical eligible categories include:

- audiovisual archive;
- film archive or cinematheque;
- institutional audiovisual collection;
- public broadcaster archive;
- university audiovisual archive;
- museum or library collection with a defined audiovisual component;
- aggregator included under a separately declared analytical role.

## Excluded entities

Entities may be excluded for reasons including:

- commercial image bank;
- commercial video bank;
- paid stock repository;
- generic commercial streaming platform;
- social media platform;
- search engine;
- news portal without an archival corpus;
- duplicate entity;
- inactive entity;
- object outside the audiovisual scope;
- insufficient evidence for incorporation.

## Commercial paid banks

Commercial paid image and video banks are identified, classified and retained in the Discovery Registry when relevant.

They do not enter the scientific corpus and are excluded from analytical numerators and denominators. Their exclusion prevents paid stock services from distorting measures intended to describe institutional audiovisual archives.

The decision is represented explicitly, for example:

```text
corpus_status = excluded
exclusion_reason = commercial_image_bank
```

or:

```text
corpus_status = excluded
exclusion_reason = commercial_video_bank
```

## Aggregators

Aggregators are not automatically equivalent to custodial archives. They may be included when their role is analytically declared and results are not mixed with institution-level measurements.

The platform preserves the distinction among:

- aggregator;
- archive or custodial institution;
- corpus;
- individual record;
- external access platform.

## Access-index denominator

The Audiovisual Archive Access Index uses only eligible and assessable archives.

```text
eligible archives open without registration, payment or formal request
────────────────────────────────────────────────────────────────────── × 100
eligible assessable archives
```

Commercial paid banks, excluded entities, technical errors, non-assessable cases and missing observations do not enter the denominator.

## Negative and unresolved cases

Exclusion is not deletion. Negative decisions and unresolved candidates remain documented with their evidence and rationale.

This allows researchers to reconstruct:

- how many entities were discovered;
- how many were incorporated;
- how many were excluded;
- why each exclusion occurred;
- whether the decision changed over time.

## Longitudinal eligibility

Eligibility may change when an institution launches a public catalogue, changes its role, becomes inactive or reveals evidence previously unavailable.

Any change must preserve the previous decision and create a new version or review record. Historical indicators remain linked to the corpus definition valid for their snapshot.

## Review requirements

Automatic rules may support preliminary classification, but ambiguous cases require human review. Decisions should document:

- entity identity;
- category;
- corpus status;
- exclusion reason when applicable;
- source evidence;
- decision date;
- reviewer or responsible process;
- methodological version.

## Reproducibility principle

A published result must make it possible to determine not only which archives were counted, but also which discovered entities were not counted and why.

This policy therefore treats corpus construction as part of the scientific method rather than as an invisible preprocessing step.
