# MAR — VAL-007 handoff checkpoint

Date: 2026-09-14
Branch: `presentation/rpv-1`
Repository: `brauliorrs/memoria-audiovisual-rede`

## Current state

VAL-007 is the independent ecological validation of M3 surface typing protocol `2.2.0` (`MAR-T2A-M3-VAL-007-PROTOCOL`).

The blind human review is complete and frozen before model comparison.

- Human review file: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_v2_2.json`
- Human review completion commit: `5004d01422c1645ab07df5cd1c149569a81ce07c`
- Human review final blob SHA: `a9f8fc78107424ffd33add5830ed743185d1fbaf`
- Human review status: `completed`
- Units reviewed: `31/31`
- Human item-level true: `14`
- Human non-item-level: `16`
- Human ambiguous: `1`
- Completion date recorded in artifact: `2026-09-08`

Human review freeze manifest was created in a separate commit, before predictions were opened:

- Freeze manifest: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_freeze_v2_2.json`
- Freeze manifest commit: `2a13cbed58df1901e0e024f2b748b64ff0301597`
- Queue coverage at freeze: 31 IDs, 0 duplicates, 0 missing queue IDs, 0 extra IDs
- Model predictions were not opened before the human review freeze.

The authoritative VAL-007 source remains GitHub Actions run `33673923717`, job `100393939906`, artifact `9863619119`. A later automatic rerun is non-authoritative and must remain ignored.

## Frozen source artifacts

- Review queue: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_review_queue_v2_2.json`
  - repo blob: `aed13cc50b5bc62e12d2f05191bc6bb2eb357e24`
  - SHA256: `2c764eab221dbe595ada50eda1cd2b843e976fca25d8a57f39380724727d8fa8`
- Predictions: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_predictions_v2_2.json`
  - repo blob: `00966f1e5f44e041eade11edff7c37ff2dd7cd2f`
  - SHA256: `4bb277ba99324622d66bee279c7ab2d6bdbbd4755c7ef5f4cc12ef991f67aec1`
- Prediction freeze: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_prediction_freeze_v2_2.json`
- Preservation manifest: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_preservation_v2_2.json`
- Validation protocol: `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_2.json`

## Important methodological state

Predictions were opened only after the human-review freeze. No tuning, relabeling, substitution, post-hoc rule changes, or development use of VAL-007 is permitted before the formal pass/fail result is recorded.

The current task is to compute and persist the preregistered metrics and gate decision. The first comparison already shows that item-level recall is the likely critical failure mode, but **do not treat that observation as the final result until the complete metrics are calculated and recorded**.

## Preregistered acceptance gates

Fine-grained surface classification:

- weighted F1 >= `0.50`
- every human class with support >= 5 must have recall >= `0.50`

Item-level M4 gate:

- precision >= `0.80`
- recall >= `0.70`
- specificity >= `0.85`
- any entity with >= 2 human item units cannot miss all of them
- all item-level criteria must pass before M4 scaling can be considered

Access-state agreement:

- agreement >= `0.90`
- access agreement cannot compensate for semantic/item-level failure

These are operational gates, not population confidence intervals or prevalence estimates.

## Human labels to preserve exactly

The authoritative human labels are the 31 records in `m3_surface_type_independent_human_review_v2_2.json`. Do not correct or reinterpret any surprising labels without explicit user instruction.

Final class totals after unit 31:

- item-level true: 14
- non-item-level: 16
- ambiguous: 1

The last five decisions were:

- unit 27 Memoryscapes clip 6782 EN -> `G audiovisual_item`
- unit 28 Memoryscapes clip 6782 IT -> `G audiovisual_item`
- unit 29 Memoryscapes clip 6771 -> `G audiovisual_item`
- unit 30 Memoryscapes clip 1565 -> `G audiovisual_item`
- unit 31 Memoryscapes archive filtered by author -> `D search_or_index`

## Next action in a new chat

1. Read this checkpoint plus the protocol, human review freeze, frozen human review, and frozen predictions.
2. Verify prediction/human unit-ID alignment for all 31 units.
3. Compute the preregistered fine-grained metrics, item-level confusion matrix/precision/recall/specificity, entity-level miss condition, and access-state agreement.
4. Apply the gates exactly as preregistered.
5. Persist a VAL-007 evaluation artifact/report and update the experiment registry.
6. Decide formally whether M3 protocol 2.2.0 passes and whether M4 scaling remains blocked or may proceed.
7. Do not tune the classifier using VAL-007 before the validation result is frozen.

## Broader MAR status reminder

- T1 DONE: 55 active corpora; 49 success, 6 auditable failure; no silent exclusion.
- T2 DONE/FROZEN: 55 active, 385 coverage states, 9 indicators; experimental AI excluded from official baseline.
- M1 collection detection: in progress.
- M2 public video detection: in progress.
- M3 surface/unit role resolution: protocol 2.2.0 under VAL-007 final metric/gate closure.
- M4 item-level candidate resolution: pilot 0/2; **do not scale until M3 passes VAL-007**.
- M5 corpus belonging: in progress.
- M6 public item observability: in progress.

This checkpoint is a continuity aid only; frozen artifacts and preregistered protocol remain authoritative.
