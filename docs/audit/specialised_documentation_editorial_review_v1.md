# Specialised Documentation Editorial Review v1

**Branch:** `presentation/rpv-1`  
**Review date:** 2026-08-04  
**Scope:** analytical documentation, indicator source-of-truth references, evaluative states and documentation governance.

## 1. Workflow status before review

The following workflows completed successfully for commit `14f40db64510ceec28da4d39d4789f04292cb11d`:

- Quality Checks;
- I18N Audit;
- Documentation Quality.

This confirms repository-level structural quality, translation-key consistency and internal Markdown-link validity. It does not establish empirical detector validity or external-link availability.

## 2. Findings

### 2.1 Obsolete indicator source-of-truth reference

`docs/research/07_scientific_indicators.md` referred to `data/templates/analytics/indicator_catalog.json` as the machine-readable source of truth. The active scientific infrastructure now uses:

- `data/templates/analytics/indicator_registry.json`;
- `data/templates/analytics/methodology_registry.json`;
- executable implementations under `src/memoria_audiovisual/analytics/`.

**Correction applied:** the Handbook now identifies the active registry and methodology registry and warns against treating transitional catalogue files as canonical.

### 2.2 Documentation hierarchy did not match the implemented repository

`docs/DOCUMENTATION_GOVERNANCE.md` declared `docs/analytics/` as the canonical analytical layer, but that directory is not the active documentation entry point in the reviewed branch.

**Correction applied:** machine-readable registries and executable analytics are now defined as the current canonical analytical specifications. A future `docs/analytics/` layer may explain them but cannot independently redefine scientific populations or interpretations.

### 2.3 Implemented status could be read as empirically validated

The specialised documentation did not always state explicitly that an indicator marked `implemented` may still require empirical validation on real institutions.

**Correction applied:** `docs/research/06_analytics.md` and `docs/research/07_scientific_indicators.md` now distinguish executable implementation and controlled tests from empirical validation.

### 2.4 Evaluative states required tighter denominator rules

The documentation listed unknown, error and not-assessable states but did not fully standardise how `not detected` should be interpreted.

**Correction applied:** `not detected` now means that no signal was found through the declared procedure on assessed public surfaces. It is not equivalent to verified institutional absence. Error, missing, not-assessable and pending-review states are excluded from denominators unless an explicit versioned methodology defines otherwise.

### 2.5 Public showcase needed canonical terminology

The backlog introduced a public showcase distinct from the analytical observatory, but the controlled terminology did not yet include it.

**Correction applied:** documentation governance now distinguishes project, research infrastructure, platform, public observatory, public showcase and scientific repository roles.

## 3. Files revised

- `docs/research/06_analytics.md`;
- `docs/research/07_scientific_indicators.md`;
- `docs/DOCUMENTATION_GOVERNANCE.md`.

## 4. Residual editorial review queue

### High priority

1. review `docs/research/08_operational_validation.md` against the current workflows and empirical-validation status;
2. review `docs/research/09_roadmap.md` against the implementation backlog and public-showcase decision;
3. inspect `docs/digital-infrastructure-alignment/` for duplicated definitions of evidence, coverage, eligibility and publication;
4. verify all references to `indicator_catalog.json` and other transitional artefacts;
5. align public Streamlit terminology in Portuguese, English and Spanish.

### Medium priority

1. review publication and collaboration documents after the first stable release;
2. add a dedicated explanatory analytics index only when it can be generated from or verified against the active registries;
3. validate essential external links and document anti-bot or redirection exceptions.

## 5. Review conclusion

The first specialised editorial pass corrected the most consequential source-of-truth and denominator inconsistencies. The documentation is more accurate about the distinction between implementation readiness and empirical validation. The remaining work is a file-by-file audit of operational validation, roadmap, technical governance and public-interface terminology.
