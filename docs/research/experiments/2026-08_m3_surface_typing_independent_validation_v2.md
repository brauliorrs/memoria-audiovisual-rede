# M3 surface typing independent validation — protocol 2.0.0

## Status

Independent ecological blind validation completed on 2026-08-25. Automatic predictions from workflow run `32857274723` were frozen before human review and remained blinded until all 33 human decisions were closed.

This experiment does not modify the official T2 baseline and is not a prevalence study.

## Sample

The preregistered design requested six entities, but `european_film_gateway` was not present in `CORPORA` and therefore produced no surfaces. No replacement was introduced after prediction freeze. The authoritative frozen sample contains 33 units from five effective entities: Cinearchives, Cinémémoire, EAFA, EYE and Archivio Storico Istituto Luce.

Human reference distribution:

- `homepage`: 1
- `search_or_index`: 19
- `audiovisual_item`: 12
- `restricted_or_unavailable`: 1
- all other surface classes: 0
- item-level true: 12
- item-level false: 21

## Results

### Fine-grained surface type

Exact surface-type agreement was **3/33 (9.09%)**. Weighted F1 was **0.1203**. Macro F1 across the nine protocol classes was **0.0934**; macro F1 restricted to human-supported classes was **0.2101**.

The result is insufficient to validate protocol 2.0.0 for fine-grained M3 surface-role classification on this independent sample.

Human-supported class results:

| Human class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| `homepage` | 0.5000 | 1.0000 | 0.6667 | 1 |
| `search_or_index` | 0.5000 | 0.1053 | 0.1739 | 19 |
| `audiovisual_item` | 0.0000 | 0.0000 | 0.0000 | 12 |
| `restricted_or_unavailable` | 0.0000 | 0.0000 | 0.0000 | 1 |

Classes absent from the human reference cannot have their performance estimated from this sample.

### Binary item-level discrimination

For the operational distinction between item-level (`item_record` or `audiovisual_item`) and non-item-level surfaces:

- TP: 7
- TN: 19
- FP: 2
- FN: 5
- precision: **77.78%**
- recall: **58.33%**
- F1: **66.67%**
- specificity: **90.48%**
- accuracy: **78.79%**

This shows partial operational utility, but recall remains too low to scale M4 safely without revising M3.

### Access state

Access-state agreement was **33/33 (100%)**. This supports the protocol decision to represent semantic surface role and access state as independent dimensions on this sample.

## Error patterns

Cinearchives exposed over-reliance on `catalogue` path and archive-title cues. Three human audiovisual-item pages were classified as archive landing pages, and blocked AJAX filtering endpoints were classified as `unknown` instead of `search_or_index`.

Cinémémoire exposed two related weaknesses: archive/fonds and structured-article cues confused thematic index surfaces, while repeated archive-path context suppressed two genuine audiovisual items and generated item-level false negatives.

EYE exposed a major weakness in year-filter recognition. Most year-filter pages were classified `unknown`; the search root was treated as `homepage`; and two combined-year filters were falsely classified as `audiovisual_item`.

Luce exposed a finer semantic boundary problem rather than an item-level failure. The seven detail pages were correctly recognized as item-level, but all were classified `item_record` rather than the human `audiovisual_item` class.

## Scientific decision

**Do not accept protocol 2.0.0 as validated for fine-grained M3 surface typing.** Retain the frozen result as an empirical independent validation finding. Revise the classifier under a new protocol version, explicitly addressing catalogue-item recognition, thematic/index surfaces, year filters, and the `item_record` versus `audiovisual_item` boundary.

Do not tune protocol 2.0.0 retroactively. Any correction belongs to a later version and must be evaluated on a new prediction-frozen independent sample before M4 is scaled.

## Limitations

The sample contains only 33 units and five effective entities; the sixth preregistered identifier failed before collection because it was absent from `CORPORA`. It is an ecological validation sample, not a prevalence sample. Several protocol classes have zero human support. Entity clusters, especially the seven similar Luce detail pages, also make aggregate binary metrics sensitive to within-entity repetition.

## Durable artifacts

- Frozen predictions: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_predictions_v2.json`
- Blind review queue: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_review_queue_v2.json`
- Completed human review: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_v2.json`
- Evaluation: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_evaluation_v2.json`
- Prediction freeze manifest: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_prediction_freeze_v2.json`
- Preservation manifest: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_preservation_v2.json`
