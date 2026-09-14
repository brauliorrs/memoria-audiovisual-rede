# M3 surface typing — post-validation calibration 2.1.0

## Status

Protocol **2.1.0** is a calibrated development candidate produced after the independent ecological validation of protocol 2.0.0 (`MAR-T2A-M3-VAL-003`). It is **not** an independently validated protocol.

The official T2 baseline is unchanged.

## Why a new version was required

Independent validation of protocol 2.0.0 produced only 3/33 exact fine-grained surface matches and item-level recall of 58.33%. The error analysis identified four main families: catalogue and item confusion in Cinearchives, thematic/index and fiche-film precedence problems in Cinémémoire, year/facet filter errors in EYE, and the `item_record` versus `audiovisual_item` boundary in Luce.

Those findings were used only after the 2.0.0 evaluation was frozen and completed. Consequently, the 33 labelled units are now development data for 2.1.0 and cannot be reused as independent evidence of 2.1.0 performance.

## Protocol changes

Protocol 2.1.0 changes evidence precedence rather than merely adding isolated URL exceptions:

- facet/filter query semantics are resolved before ID-like path heuristics;
- catalogue roots and AJAX keyword/filter endpoints are treated as index surfaces when appropriate;
- strong item routes such as catalogue details and `fiche-film` are not suppressed by repeated archive path context;
- generic JSON-LD `Article` metadata cannot override a strong item route;
- semantic restriction routes such as `/acces-pro` are separated from collector access state;
- audiovisual frame metadata can support `audiovisual_item` classification when a direct media URL is not extracted;
- semantic surface role and access state remain independent dimensions.

## Development/regression evidence

Two known labelled sets are used only for development regression:

1. the original 17-unit M3 calibration fixture;
2. the 33 units from the completed 2.0.0 independent validation, reused only after that experiment was evaluated and closed.

The resulting known set contains **50 units**. The 2.1.0 regression tests reproduce all 50 human decisions for surface type, item-level status and access state: **50/50 agreement with zero known mismatches**.

This is **not accuracy**. It is not precision, recall, F1, prevalence or a generalisation estimate because all 50 labels are now known to the development process.

## CI verification

Quality Checks run `32901520587`, job `97976231651`, completed successfully with **746 tests passed and 2 subtests passed**.

The dedicated workflow `T2A MAR surface typing calibration smoke 2.1`, run `32901520435`, job `97976231334`, also completed successfully. Its M3 regression step passed **26/26 tests**. The live calibration smoke produced 25 reviewable surfaces and was explicitly marked `calibration_smoke_only`, not independent validation. Its frozen prediction SHA-256 is `d50cc50c7239278a6fd6709d7c373fbe34053c0e9bbf2e83fc932eb9c73d5126`.

## Scientific decision

**Accept protocol 2.1.0 only as a calibrated candidate for a new independent validation.**

Do not report the 50/50 development agreement as performance. Do not scale M4 yet. The next scientific step is to preregister a new independent ecological validation, exclude all previously labelled URLs, freeze predictions before human review, preserve blinding, and evaluate 2.1.0 without further tuning after the freeze.

## Limitations

The known labels are concentrated in specific archives and route families. Several semantic classes remain absent or sparse. Platform-specific route structures may still create overfitting. The 25-unit smoke sample was not human-reviewed to generate a new performance estimate.

## Durable references

- Classifier: `src/memoria_audiovisual/digital_infrastructure/surface_typing.py`
- Regression tests: `tests/test_surface_typing.py`
- Calibration artifact: `data/digital_infrastructure/ai_experiments/m3_surface_type_post_validation_development_v2_1.json`
- Source independent evaluation: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_evaluation_v2.json`
