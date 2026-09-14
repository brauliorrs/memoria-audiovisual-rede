# M3 surface typing independent validation — protocol 2.2.0

## Status

Independent ecological blind validation **MAR-T2A-M3-VAL-007** completed on 2026-09-08. The protocol was preregistered before execution, and predictions from authoritative workflow run `33673923717` were frozen before human review. The 31 human decisions were completed in commit `5004d01422c1645ab07df5cd1c149569a81ce07c` and separately frozen in commit `2a13cbed58df1901e0e024f2b748b64ff0301597` before the prediction file was opened for comparison.

The completed human-review artifact has Git blob `a9f8fc78107424ffd33add5830ed743185d1fbaf` and SHA-256 `673b5d11e731bc45d0d9415696bc355ce6772ffd4de24ba8a2d9b0c73dae49eb`. Queue coverage at freeze was exact: zero duplicate IDs, zero missing queue IDs and zero extra IDs.

This experiment does not modify the official T2 baseline and is not a prevalence study.

## Preregistered operational gates

Fine-grained M3 acceptance required both:

- weighted F1 >= **0.50**;
- recall >= **0.50** for every human class with support >=5.

The M4 item-level gate required all of:

- precision >= **0.80**;
- recall >= **0.70**;
- specificity >= **0.85**;
- for every entity with at least two human item-level units, the classifier must not miss all of them.

Access-state agreement required >= **0.90**, but access success could not compensate for semantic or item-level failure.

## Sample

All six preregistered unseen corpora are represented:

- BBC Archive: 6 units
- Bulgarian National Television: 6
- Cinemateca Portuguesa: 6
- Cinémathèque française / HENRI: 6
- FINA / Ninateka: 1
- Home Movies / Memoryscapes: 6

FINA/Ninateka yielded only one eligible observed surface under the deterministic preregistered discovery and exclusion rules. No replacement or post-hoc substitution was used.

Human reference distribution:

- `institutional_landing_page`: 1
- `archive_landing_page`: 6
- `search_or_index`: 9
- `audiovisual_item`: 14
- `unknown`: 1
- `homepage`, `news_or_editorial`, `item_record`, `restricted_or_unavailable`: 0
- item-level true: 14
- item-level false: 16
- item-level ambiguous: 1

## Results

### Fine-grained surface type

Exact surface-type agreement was **7/31 (22.58%)**. Weighted F1 was **0.2828**. Macro F1 across all nine protocol classes was **0.1575**; macro F1 restricted to human-supported classes was **0.2835**.

Human-supported classes:

| Human class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| `institutional_landing_page` | 0.1667 | 1.0000 | 0.2857 | 1 |
| `archive_landing_page` | 1.0000 | 0.3333 | 0.5000 | 6 |
| `search_or_index` | 1.0000 | 0.1111 | 0.2000 | 9 |
| `audiovisual_item` | 1.0000 | 0.1429 | 0.2500 | 14 |
| `unknown` | 0.1000 | 1.0000 | 0.1818 | 1 |

The weighted-F1 gate **failed**: 0.2828 < 0.50.

All three human classes with support >=5 also failed the preregistered recall requirement:

- `archive_landing_page`: **33.33%** recall;
- `search_or_index`: **11.11%**;
- `audiovisual_item`: **14.29%**.

Therefore fine-grained M3 2.2.0 is **not independently validated**.

### Binary item-level discrimination

The one human `unknown` unit is excluded from binary item/non-item metrics, leaving 30 assessable units.

- TP: 2
- TN: 16
- FP: 0
- FN: 12
- precision: **100.00%** — passes
- recall: **14.29%** — fails
- F1: **25.00%**
- specificity: **100.00%** — passes
- accuracy: **60.00%**

The classifier remains extremely conservative: it produced no item-level false positives but missed **12 of 14** human item-level surfaces.

The preregistered entity-failure rule also failed. Three entities with at least two human item-level units had all such items missed:

- Cinemateca Portuguesa: 0/2 detected;
- Cinémathèque française / HENRI: 0/5;
- Home Movies / Memoryscapes: 0/4.

BBC passed this entity rule with 2/2 human items detected. BNT had only one human item and therefore does not trigger the >=2 rule.

Consequently the **M4 item-level gate is not met**, and M4 must not be scaled.

### Access state

Access-state agreement was **31/31 (100%)**, above the preregistered 90% threshold. This supports keeping access-state inference separate from semantic surface typing, but it does not compensate for the failed M3 and item-level gates.

## Entity diagnostics

| Entity | Units | Exact surface accuracy | Human item units | Item units detected | Item-level accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| BBC | 6 | 83.33% | 2 | 2 | 100.00% |
| BNT | 6 | 0.00% | 1 | 0 | 83.33% |
| Cinemateca Portuguesa | 6 | 33.33% | 2 | 0 | 60.00%* |
| Cinémathèque française | 6 | 0.00% | 5 | 0 | 16.67% |
| FINA / Ninateka | 1 | 0.00% | 0 | 0 | 100.00% |
| Home Movies / Memoryscapes | 6 | 0.00% | 4 | 0 | 33.33% |

\* Five binary-assessable units because one human surface was `unknown`.

## Main failure patterns

**Observation-root fallback is too dominant.** BNT's archive root, Cinemateca Digital, HENRI, Ninateka and Memoryscapes archive/filter surfaces were repeatedly predicted `homepage` even when the human semantic role was archive or search/index.

**Cinémathèque française / HENRI:** all five reviewed `/henri/film/...` surfaces were human `audiovisual_item`, but all five were predicted `institutional_landing_page`. The descendant institutional-root signal dominated item specificity.

**Cinemateca Portuguesa:** both reviewed `Ficha.aspx?...type=Video` surfaces were human `audiovisual_item` and had public Vimeo media in collected context, yet both were predicted `unknown`.

**Memoryscapes:** all four reviewed `/clips/...` surfaces were human `audiovisual_item` and exposed public Vimeo/MP4 media, yet all four were predicted `unknown`.

**Search/index:** only **1 of 9** human `search_or_index` surfaces was classified exactly; six were mapped to `homepage`.

**BBC:** unlike the other architectures, BBC performed strongly: 5/6 exact surface roles and 2/2 human audiovisual items detected. The failure is therefore not uniform across sites; it is architecture-dependent.

## Comparison with protocol 2.1.0

Protocol 2.2.0 modestly improved fine-grained metrics relative to VAL-005:

- exact agreement: **16.67% → 22.58%**;
- weighted F1: **0.2295 → 0.2828**.

However, the operationally critical item-level result worsened:

- precision: **100% → 100%**;
- recall: **28.57% → 14.29%**;
- F1: **44.44% → 25.00%**;
- specificity: **100% → 100%**;
- accuracy: **72.22% → 60.00%**.

Thus protocol 2.2.0 does not solve the item under-detection that blocks M4.

## Development result versus independent validation

The post-VAL-005 development diagnostic **MAR-T2A-M3-CAL-006** produced item-level recall of 71.43% and F1 of 83.33% on previously human-labelled development material. Those 86 known URLs were explicitly development-only and excluded from VAL-007.

On the new preregistered unseen sample, item recall fell to **14.29%** and F1 to **25.00%**. The correct scientific interpretation is that the development-set gains **did not generalize**. CAL-006 must not be cited as independent validation evidence.

## Scientific decision

**Protocol 2.2.0 is not independently validated for fine-grained M3 surface typing, and the M4 gate is not met. Do not scale M4.**

VAL-007 must remain frozen unchanged as the authoritative independent result. No human label or protocol 2.2.0 rule should be revised after seeing these predictions.

Any corrective work belongs to a later protocol version. The next version should specifically address architecture-aware item specificity, the dominance of observation-root/institutional fallbacks, item recognition for HENRI `/film/`, Cinemateca `Ficha.aspx?...type=Video`, and Memoryscapes `/clips/`, plus search/index semantics. It must then undergo a new preregistered, prediction-frozen independent ecological validation before M4 scaling can be reconsidered.

## Limitations

The sample contains 31 units from six entities and is too small for broad generalisation. FINA/Ninateka contributes only one unit. Four protocol classes have zero human support, and two classes have support of one, so sparse-class results are descriptive only. Repeated route families—five HENRI film pages and four Memoryscapes clip pages—make aggregate metrics sensitive to within-entity clustering. The sample is not a prevalence sample, and the acceptance thresholds are operational gates rather than population-level confidence intervals.

Human labels are authoritative for this blind validation and were completed and frozen before predictions were opened.

## Durable artifacts

- Preregistered protocol: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_2.json`
- Prediction freeze: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_prediction_freeze_v2_2.json`
- Frozen predictions: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_predictions_v2_2.json`
- Blind review queue: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_review_queue_v2_2.json`
- Completed human review: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_v2_2.json`
- Human-review freeze: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_freeze_v2_2.json`
- Evaluation: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_evaluation_v2_2.json`
