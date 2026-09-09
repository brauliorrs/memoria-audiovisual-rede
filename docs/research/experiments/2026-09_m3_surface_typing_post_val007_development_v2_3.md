# M3 surface typing — post-VAL-007 development candidate 2.3.0-dev

## Status

**Development/calibration only. Not an independent validation.**

Experiment: `MAR-T2A-M3-CAL-008`  
Candidate: `2.3.0-dev`  
Source failed validation: `MAR-T2A-M3-VAL-007` / protocol `2.2.0`

The independent VAL-007 result remains unchanged and authoritative: protocol 2.2.0 failed the preregistered fine-grained and item-level gates and therefore does not permit M4 scaling. Only after that result and its blind human review were frozen were the VAL-007 labels reused as development evidence for the next protocol generation.

## Why a separate candidate module was used

The frozen 2.2.0 classifier was not edited. The new logic lives in:

`src/memoria_audiovisual/digital_infrastructure/surface_typing_v23_candidate.py`

It is a wrapper over the frozen 2.2.0 implementation. This keeps the failed independent result reproducible and prevents a later development change from silently altering the model that produced VAL-007.

## Generic corrections introduced

The candidate addresses architectural error families observed after VAL-007 without hard-coding institutions, item identifiers or exact observed slugs:

- audiovisual route families now include singular/plural `film`, `video`, `movie`, `audio` and `clip` forms;
- trailing-slash audiovisual detail routes retain their semantic detail segment;
- fiche/detail pages may infer audiovisual type from query **values**, such as a generic `type=Video` pattern;
- directly observable public media can confirm an otherwise generic audiovisual detail route;
- author/creator/category/genre/tag query filters can identify an index surface;
- configured crawler roots are no longer assumed to be semantic homepages when generic index/browse evidence is present;
- unresolved multilingual collection routes can become `archive_landing_page`, but an already resolved institutional landing decision is preserved.

The last restriction was added after the first CI run revealed that an initially broader collection rule would regress an older INA calibration unit.

## Regression evidence

The development suite now covers 117 previously known units:

| Development set | Units | Role | Result |
|---|---:|---|---|
| Original M3 blind calibration | 17 | development regression | exact replay preserved |
| Former VAL-003 | 33 | former independent, now development | exact replay preserved |
| Former VAL-005 | 36 | former independent, now development | safe binary floor preserved: FP=0, TN=22, TP≥10, FN≤4 |
| Failed VAL-007 | 31 | post-validation development | new generic recovery gates passed |

These sets are no longer eligible to provide independent evidence for protocol 2.3.0.

## VAL-007 development replay

The following numbers are deliberately reported as **in-sample post-validation development diagnostics**. They must not be presented as independent performance.

### Fine-grained surface role

- exact agreement: **25/31 = 80.65%**;
- weighted F1: **0.8663**;
- macro F1 over human-supported classes: **0.8009**;
- macro F1 over all nine protocol classes: **0.4450**.

For the three human classes with support at least five:

| Human class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| `archive_landing_page` | 6 | 1.000 | 0.500 | 0.667 |
| `search_or_index` | 9 | 1.000 | 0.778 | 0.875 |
| `audiovisual_item` | 14 | 1.000 | 0.929 | 0.963 |

The remaining six exact errors are concentrated in BBC/BNT semantic boundaries rather than the audiovisual route families that dominated the failed independent result.

### Item-level gate diagnostic

The one human `unknown` unit remains excluded from the binary item calculation.

- TP = **13**;
- TN = **16**;
- FP = **0**;
- FN = **1**;
- precision = **100%**;
- recall = **92.86%**;
- F1 = **96.30%**;
- specificity = **100%**;
- accuracy = **96.67%**.

Recovery of human item-level units by entity:

- BBC: 2/2;
- BNT: 0/1;
- Cinemateca Portuguesa: 2/2;
- Cinémathèque française: 5/5;
- FINA/Ninateka: 0/0;
- Memoryscapes: 4/4.

Thus the candidate would satisfy the old VAL-007 numerical item gate **on the same labels used to design it**. That fact is useful only as a regression target; it is not evidence that the rule generalises.

### Access state

Access-state agreement remains 31/31. This again supports keeping semantic role and access state as separate dimensions, but does not validate the semantic classifier.

## Remaining development errors

Six semantic mismatches remain in the 31-unit replay:

1. BBC complaints surface: human `archive_landing_page`, candidate `unknown`;
2. BNT FIAT/IFTA surface: human `archive_landing_page`, candidate `unknown`;
3. BNT request-error surface: human `search_or_index`, candidate `restricted_or_unavailable`;
4. one BNT `/news/` surface: human `search_or_index`, candidate `news_or_editorial`;
5. one BNT `/news/` surface: human `archive_landing_page`, candidate `news_or_editorial`;
6. one BNT `/news/` audiovisual surface: human `audiovisual_item`, candidate `news_or_editorial`.

These residual cases should not be repaired by corpus-specific IDs or slugs. Any further change must have a defensible generic semantic rule and must preserve all current regression constraints.

## Quality checks

Final green run:

- workflow run: `34298716962`;
- job: `102300853568`;
- tests: **767 passed, 2 subtests passed**;
- experiment-registry schema validator: passed for the existing registry;
- methodology consistency: passed;
- scientific integrity: passed;
- deployment snapshot check: passed.

An earlier development run failed two tests and was intentionally not promoted. One failure exposed an over-broad collection override; the other showed that a synthetic test expected `search_or_index` where the frozen 2.2.0 semantics already supported `archive_landing_page`. Both were narrowed before the green run.

## Scientific interpretation

The candidate has solved the dominant **known** failure families strongly enough to justify preparing a new independent test. It has **not** validated protocol 2.3.0.

The apparent improvement from VAL-007 — exact agreement from 22.58% to 80.65%, and item recall from 14.29% to 92.86% — is an expected development-replay comparison after observing the failed validation labels. It must not be interpreted as out-of-sample improvement.

## Next independent gate

Before any new human review begins, the next protocol must:

1. freeze the final 2.3.0 implementation;
2. preregister a new set of unseen entities and deterministic sampling rules;
3. exclude all **117 known development units/URLs** represented by the 17 + 33 + 36 + 31 development sets;
4. generate and freeze predictions before human labels are entered;
5. complete and freeze the blind human review before opening predictions;
6. apply acceptance thresholds without post-hoc entity replacement, class balancing or tuning;
7. keep M4 scaling blocked unless **all** preregistered M3 item-level criteria pass.

## Governance note

The current master `experiment_registry_v1.json` still validates structurally but has not yet been extended with VAL-007 and this CAL-008 record. This is a provenance/governance gap to close before the next independent validation; it does not alter either scientific result.
