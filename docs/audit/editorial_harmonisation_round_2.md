# Editorial Harmonisation — Round 2

## Scope

This round implements the editorial sequence defined after the first specialised-documentation review:

1. review `docs/research/08_operational_validation.md`;
2. review `docs/research/09_roadmap.md`;
3. continue the review of `docs/digital-infrastructure-alignment/`;
4. locate obsolete analytical references;
5. audit public terminology in Portuguese, English and Spanish.

## Completed in this round

### Operational validation

`docs/research/08_operational_validation.md` was rewritten to:

- distinguish operational validation from universal detector validity;
- include documentation, citation, link and internationalisation controls;
- define ambiguous and not-assessable outcomes;
- require reconstruction of indicators from the active registries;
- add public-interface and showcase validation;
- define explicit acceptance criteria for the first official cycle.

### Roadmap

`docs/research/09_roadmap.md` was reorganised to distinguish:

- core infrastructure;
- scientific presentation and governance;
- operational validation;
- the first official scientific cycle;
- the longitudinal observatory;
- the public showcase and research delivery;
- comparative and reusable infrastructure.

The roadmap now treats the showcase and the analytical observatory as separate public products and records Streamlit performance as an unresolved deployment decision.

### Analytical source-of-truth alignment

The current canonical analytical sources remain:

- `data/templates/analytics/indicator_registry.json`;
- `data/templates/analytics/methodology_registry.json`;
- `src/memoria_audiovisual/analytics/`;
- the scientific interpretation in `docs/research/`.

The earlier reference to `indicator_catalog.json` in the Research Handbook was removed in the previous editorial round. No indexed occurrences were returned by the repository search performed in this round. This does not replace a complete filesystem-level audit of every historical or generated file.

### Multilingual terminology audit

A new report-only control was added:

```text
scripts/audit_locale_catalogue_language.py
```

It examines the English and Spanish locale catalogues for residual Portuguese terminology that may not be reached by runtime-only tests.

The `I18N Audit` workflow was expanded to:

- run the catalogue-language audit;
- preserve the existing blocking runtime audit;
- generate a combined human-readable report;
- upload both runtime and catalogue findings;
- keep catalogue findings report-only during the correction cycle.

This staged approach prevents known catalogue debt from being hidden while avoiding an indiscriminate deployment block before each flagged value has been reviewed for false positives.

## Still pending

### Digital-infrastructure specialised documents

A complete file-by-file review of `docs/digital-infrastructure-alignment/` remains pending. The review must prioritise:

- duplicated scientific definitions;
- terminology inconsistent with `docs/DOCUMENTATION_GOVERNANCE.md`;
- claims that conflate implementation with empirical validation;
- references to superseded analytical files or architecture names;
- descriptions of AI evidence that imply institutional absence from non-detection;
- references to provisional branches, pull requests or workflow states that are no longer current.

### Catalogue corrections

The new workflow must be executed and its `locale-catalogue-audit.json` artifact reviewed. Confirmed residual Portuguese values should then be corrected in controlled batches, with semantic review rather than automatic word replacement.

### External links

Internal Markdown validation is automated. Essential external links, redirects and anti-bot failures still require a separate network-capable validation process.

## Editorial rule reinforced

Translations are presentation metadata. They must not be used as identifiers in data transformations, analytical contracts or persistence keys.

Scientific claims must remain traceable to the Research Handbook, machine-readable registries, evidence records and review decisions.
