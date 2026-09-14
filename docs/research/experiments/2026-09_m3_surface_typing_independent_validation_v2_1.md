# M3 surface typing independent validation — protocol 2.1.0

## Status

Independent ecological blind validation **MAR-T2A-M3-VAL-005** completed on 2026-09-02. Predictions from authoritative workflow run `32911622199` were frozen before human review. The 36 human decisions were completed and committed at `f15066782cf42648d1d266d77be66fd4c80f1686`, then separately frozen in commit `0bdb1133b3da111906b6c33ea33ce12b2c4a4315` before the prediction file was opened for comparison.

This experiment does not modify the official T2 baseline and is not a prevalence study.

## Sample

The preregistration named six unseen corpora: DFF, Filmarchiv Austria, EUscreen, Czech Television, CICLIC and Cinéam. All six completed collection. The deterministic global review cap of 36 units produced reviewed units from five entities; Filmarchiv Austria did not enter the final queue. This is a sample-composition limitation under the preregistered cap, not a post-freeze replacement or protocol deviation.

Human reference distribution:

- `institutional_landing_page`: 1
- `archive_landing_page`: 1
- `search_or_index`: 19
- `news_or_editorial`: 1
- `item_record`: 1
- `audiovisual_item`: 13
- `homepage`, `restricted_or_unavailable`, `unknown`: 0
- item-level true: 14
- item-level false: 22

## Results

### Fine-grained surface type

Exact surface-type agreement was **6/36 (16.67%)**. Weighted F1 was **0.2295**. Macro F1 across all nine protocol classes was **0.0999**; macro F1 restricted to human-supported classes was **0.1499**.

Human-supported class results:

| Human class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| `institutional_landing_page` | 0.0000 | 0.0000 | 0.0000 | 1 |
| `archive_landing_page` | 0.0000 | 0.0000 | 0.0000 | 1 |
| `search_or_index` | 0.5000 | 0.0526 | 0.0952 | 19 |
| `news_or_editorial` | 0.2000 | 1.0000 | 0.3333 | 1 |
| `item_record` | 0.0000 | 0.0000 | 0.0000 | 1 |
| `audiovisual_item` | 1.0000 | 0.3077 | 0.4706 | 13 |

The strongest fine-grained result is the precision of `audiovisual_item` (100%), but recall is only **30.77%**. `search_or_index` recall is only **5.26%**.

### Binary item-level discrimination

For item-level (`item_record` or `audiovisual_item`) versus non-item-level:

- TP: 4
- TN: 22
- FP: 0
- FN: 10
- precision: **100.00%**
- recall: **28.57%**
- F1: **44.44%**
- specificity: **100.00%**
- accuracy: **72.22%**

The classifier is conservative: it generated no item-level false positives, but missed **10 of 14** human item-level surfaces. This recall is operationally insufficient for M4 candidate resolution.

### Access state

Access-state agreement was **36/36 (100%)**. This supports keeping access-state inference independent from semantic surface typing, but it cannot compensate for semantic-role errors.

## Comparison with protocol 2.0.0

Protocol 2.1.0 improved exact surface agreement from **9.09%** to **16.67%** and weighted F1 from **0.1203** to **0.2295**. Binary precision improved from **77.78%** to **100%**, and specificity from **90.48%** to **100%**.

However, the preregistered operational criterion required materially improved item-level recall and acceptable false-positive behavior before M4 scaling. Recall instead fell from **58.33%** to **28.57%**, binary F1 from **66.67%** to **44.44%**, and binary accuracy from **78.79%** to **72.22%**.

Therefore the M4 item-level gate is **not met**.

## Error patterns

**DFF:** six of seven human audiovisual-item trailer pages were predicted `unknown`; only one was recognized as `audiovisual_item`. This is the largest false-negative cluster.

**Cinéam:** three human audiovisual items were predicted `unknown`; several non-item navigation surfaces were also unresolved as `unknown`.

**Czech Television:** binary item-level discrimination was 8/8 correct, but non-item semantic roles remained confused among `homepage`, `institutional_landing_page` and `unknown`.

**CICLIC:** item-level discrimination was mostly preserved, but search/index surfaces were frequently mapped to archive landing, editorial or unknown.

**EUscreen:** all four units were correct at the binary item-level boundary, while three of four fine-grained roles were mismatched.

Across the full sample, only **1 of 19** human `search_or_index` surfaces was classified exactly as `search_or_index`.

## Scientific decision

**Do not accept protocol 2.1.0 as independently validated for fine-grained M3 surface typing, and do not scale M4.**

The correct next step is a new protocol version focused first on item-level false negatives—especially DFF-style `/video/<slug>` pages and Cinéam item surfaces—and on robust recognition of search/index semantics. Any correction must be versioned after this frozen result and tested on another new prediction-frozen independent ecological sample.

The 50 known development units remain development/regression evidence only and must not be used to claim independent performance.

## Limitations

The sample contains 36 units from five effective review entities and is too small for broad generalisation. Filmarchiv Austria completed collection but received no unit after the preregistered deterministic global cap. The sample is not a prevalence sample. Several protocol classes are absent or have support of one. Repeated route families—especially seven DFF trailer pages—make aggregate metrics sensitive to within-entity clustering.

## Durable artifacts

- Preregistered protocol: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_1.json`
- Prediction freeze: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_prediction_freeze_v2_1.json`
- Frozen predictions: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_predictions_v2_1.json`
- Blind review queue: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_review_queue_v2_1.json`
- Completed human review: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_v2_1.json`
- Human-review freeze: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_freeze_v2_1.json`
- Evaluation: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_evaluation_v2_1.json`
