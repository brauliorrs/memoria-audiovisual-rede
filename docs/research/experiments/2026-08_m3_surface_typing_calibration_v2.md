# M3 Surface-Typing Calibration v2

## Experiment identity

- **Experiment ID:** `MAR-T2A-M3-CAL-002`
- **Source experiment:** `MAR-T2A-M3-BLIND-001`
- **Stage:** `t2a_mar_surface_typing_calibration`
- **Scientific layer:** intelligence/automation of MAR
- **Protocol version:** `2.0.0`
- **Completion date:** 2026-08-24
- **Status:** `completed_calibration_only`
- **Claim level:** `calibration_only`
- **Independent validation sample:** no
- **Prevalence sample:** no
- **Official baseline modification:** no

## Calibration question

Can the deterministic M3 surface-typing rules be revised so that they encode the semantic distinctions established during the completed 17-unit blind human review while preserving conservative item-level behaviour and explicitly separating surface role from access/collection state?

## Scientific role

This is a **calibration and regression experiment**, not an independent validation experiment.

The 17 observations were already exposed during the human review completed in `MAR-T2A-M3-BLIND-001`. They are therefore legitimate for rule development and regression testing but cannot be reused to estimate post-calibration generalisation performance.

Accordingly, complete agreement on this set is reported only as successful encoding of the known human corrections. It is **not** reported as accuracy, precision, recall, F1, prevalence or ecological validation.

## Calibration source

The authoritative human source is:

```text
data/digital_infrastructure/ai_experiments/mar_surface_type_human_review_v1.json
```

The development fixture derived from those decisions is:

```text
tests/fixtures/m3_surface_typing_calibration_v1.json
```

The fixture explicitly declares:

```text
scientific_role = development_and_regression_calibration_only
is_independent_validation_sample = false
is_prevalence_sample = false
```

It contains the 17 reviewed units from ARCHIPOP, BFI, ECPAD, Europeana and INA.

## Main protocol changes

### 1. Surface role is independent from access and collection state

Protocol 1.x allowed collector states such as `blocked_by_robots` to dominate semantic typing. Protocol 2.0.0 introduces a separate `access_state` dimension.

Examples include:

- `collector_blocked`;
- `redirect_outside_scope`;
- `geo_restricted`;
- `request_error`;
- `http_error`;
- `accessible`.

A recoverable semantic role is now classified independently. Thus a Europeana homepage may remain `homepage` while the collector state is `collector_blocked`, and a specific video surface may remain `audiovisual_item` while playback is `geo_restricted`.

### 2. Search/index recognition was expanded

`search_or_index` now covers more than explicit search-query pages. The calibration includes:

- explicit search/research/browse routes;
- consultation routes such as `consulter`;
- thematic research/index routes;
- nested or repeated archive/collection taxonomy that represents a thematic list or index rather than a single record.

This change addresses the ECPAD thematic-result pages and the INA archive/collection list surfaces observed during human review.

### 3. Observation roots no longer default to institutional landing pages

A configured `root_url` may itself be the operational homepage of the observed platform even when its path is not `/`.

Protocol 2.0.0 therefore treats the observation root as `homepage` unless a stronger semantic role such as search/index, archive landing, editorial or item-level has already been identified.

This encodes the human classifications of the INA observation root while preserving the BFI search root and ECPAD consultation root as `search_or_index` because their stronger role is identifiable first.

### 4. Isolated lexical cues were weakened

Words such as `press` or `presse` no longer force an editorial classification by themselves. Strong editorial evidence now relies on structural context such as `about`, `news`, `article`, structured article metadata or comparable evidence.

This prevents a thematic institutional page such as INA `presse-filmee-et-cinema` from being misclassified solely because the word `presse` appears in the path/title.

### 5. Item specificity was strengthened

Item-level typing now requires evidence that the surface is specific rather than merely containing words such as `film` or `video`.

Specificity signals include, depending on context:

- UUID-like paths;
- long or repeated numeric identifiers;
- item identifiers in query parameters;
- structured identifiers;
- audiovisual structured metadata;
- embedded or linked media.

### 6. Specific audiovisual routes can remain item-level without playback

A route structurally identifying a specific audiovisual unit, for example `/video/<UUID>`, can be classified as `audiovisual_item` even when no playable media URL is available, provided item specificity is strong.

This is necessary for the BFI geographically restricted video observed by the human reviewer.

### 7. Generic record routes remain distinct from audiovisual-item routes

A route such as `/record/film-123456` does not become `audiovisual_item` merely because the word `film` is present. In the absence of audiovisual media or structured audiovisual evidence, it remains `item_record`.

This rule protects the distinction between a catalog record and a directly audiovisual item surface.

## Regression result

The calibrated protocol was tested against the complete 17-unit human calibration fixture.

Result:

- surface-type matches: **17/17**;
- item-level matches: **17/17**;
- access-state matches: **17/17**;
- mismatches: **0**.

This means the rule set now reproduces the known human corrections used to construct it.

It does **not** mean that the M3 classifier has 100% accuracy in an independent sample.

## Automated quality check

The implementation and regression tests passed in GitHub Actions:

- workflow: `Quality Checks`;
- run ID: `32801387050`;
- job ID: `97662753288`;
- conclusion: `success`.

The quality run included compilation, the experiment-registry validator, the full pytest suite and the existing scientific-integrity checks.

## Calibration artifacts

```text
src/memoria_audiovisual/digital_infrastructure/surface_typing.py
scripts/build_surface_type_review_queue.py
tests/test_surface_typing.py
tests/test_surface_type_review_queue.py
tests/fixtures/m3_surface_typing_calibration_v1.json
data/digital_infrastructure/ai_experiments/mar_surface_type_calibration_v2.json
```

## Prediction-freezing improvement

The M3 real-surface workflow was also revised for protocol 2.0.0.

Future calibration-smoke products now use v2 filenames and generate a separate SHA-256 freeze manifest before any human review can begin. The workflow output explicitly declares that this recurring sample is `calibration_smoke_only` and **not** an independent validation sample.

The independent post-calibration validation must therefore use a separately designed sample.

## Limitations

1. The 17 units were used to develop the rules and cannot estimate generalisation.
2. Some calibration decisions are supported only by compact fields preserved in the historical queue plus the completed human observation, not by a frozen copy of every original discovery field.
3. Surface classes with zero human support in this calibration set, especially `item_record`, `restricted_or_unavailable` and `unknown`, require independent challenge coverage.
4. Exact agreement after calibration does not establish prevalence or corpus-wide performance.
5. The rule set remains deterministic and may require further refinement after independent validation exposes new surface structures.

## Scientific decision

Protocol `2.0.0` is accepted as the **calibrated M3 candidate** for the next validation gate.

It is not yet empirically activated as a validated classifier.

The next gate is a **new independent blind sample** with the following mandatory order:

```text
freeze classifier version and protocol
→ construct independent real-surface sample
→ generate automatic predictions
→ persist prediction artifact
→ compute and preserve SHA-256
→ create separate blinded human-review queue
→ complete and freeze human review
→ unblind predictions
→ compute multiclass and binary item-level performance
→ document residual error and scientific decision
```

The 17 calibration units may continue to serve as regression tests but must not be counted in the independent post-calibration performance estimate.
