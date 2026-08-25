# M3 Blind Surface-Typing Validation v1

## Experiment identity

- **Experiment ID:** `MAR-T2A-M3-BLIND-001`
- **Stage:** `t2a_mar_surface_typing_validation`
- **Scientific layer:** intelligence/automation of MAR
- **Primary role:** blind human calibration of public-surface typing
- **Sample observation date:** 2026-08-19
- **Human-review completion date:** 2026-08-24
- **Status:** `completed_calibration_only`
- **Prevalence sample:** no
- **Official baseline modification:** no

## Validation question

Can the M3 mechanism distinguish the observable role of a public web surface and, in particular, separate item-level audiovisual surfaces from general, institutional, archive, search/index and editorial pages?

The operational taxonomy at the start of the experiment was:

- `homepage`;
- `institutional_landing_page`;
- `archive_landing_page`;
- `search_or_index`;
- `news_or_editorial`;
- `item_record`;
- `audiovisual_item`;
- `restricted_or_unavailable`;
- `unknown`.

Only `item_record` and `audiovisual_item` were considered item-level classes.

## Context

This experiment followed the first Gate 2 candidate review for archive-level AI evidence. That pilot produced two candidate URLs, one from ECPAD and one from INA, but neither represented an eligible audiovisual item-level observation. This exposed a surface-resolution problem upstream of later Gate 2 decisions and motivated M3 as a dedicated validation stage.

The purpose of M3 was therefore not to detect institutional AI or AI-modified content. It was to test whether MAR correctly understands the role of the public surface being observed.

## Software and implementation context

The deterministic surface classifier is implemented in:

```text
src/memoria_audiovisual/digital_infrastructure/surface_typing.py
```

The queue builder is:

```text
scripts/build_surface_type_review_queue.py
```

The controlled public-surface explorer is implemented in:

```text
src/memoria_audiovisual/digital_infrastructure/ai_surface_discovery.py
```

The scientific branch used for the durable human-review record is:

```text
presentation/rpv-1
```

The structural implementation of M3 was incorporated into that branch before the human review.

## Real-surface sample construction

The real sample was obtained through a temporary live probe executed by the GitHub Actions **Quality Checks** workflow.

- **Workflow run ID:** `32291088792`
- **Job ID:** `96191802582`
- **Probe identifier:** `M3_LIVE_BLIND_QUEUE_V1`
- **Run identifier used by the probe:** `m3-live-probe-v1`

The probe used the following exploration policy:

```text
max_depth = 1
max_pages_per_entity = 4
timeout_seconds = 8
respect_robots_txt = true
```

Five entities were selected to expose heterogeneous surface behaviour:

- INA;
- ECPAD;
- ARCHIPOP;
- BFI;
- Europeana.

The resulting blind queue contained **17 units**:

| Entity | Surfaces in queue | Fetched by collector |
|---|---:|---:|
| INA | 4 | 4 |
| ECPAD | 4 | 1 |
| ARCHIPOP | 4 | 4 |
| BFI | 4 | 4 |
| Europeana | 1 | 0 |
| **Total** | **17** | **13** |

The ECPAD child routes were observed by the collector as `redirect_outside_scope`. Europeana was recorded as `blocked_by_robots`. These collection states were preserved rather than converted into substantive negative scientific findings.

## Blind-review protocol

The reviewer classified each of the 17 units without seeing the deterministic prediction.

The human decision recorded:

- surface class;
- item-level status;
- explanatory note where relevant;
- access state separately when the review revealed that access and surface role were different dimensions.

The durable human-review artifact is:

```text
data/digital_infrastructure/ai_experiments/mar_surface_type_human_review_v1.json
```

The human-only conclusion was persisted separately before any diagnostic comparison:

```text
data/digital_infrastructure/ai_experiments/mar_surface_type_human_review_conclusion_v1.json
```

## Human-review result

All **17/17 units** were resolved by the human review. No unit remained `unknown`.

### Item-level result

- item-level: **4**
- non-item-level: **13**

### Surface-type distribution

| Human class | Count |
|---|---:|
| `homepage` | 3 |
| `institutional_landing_page` | 1 |
| `archive_landing_page` | 1 |
| `search_or_index` | 7 |
| `news_or_editorial` | 1 |
| `item_record` | 0 |
| `audiovisual_item` | 4 |
| `restricted_or_unavailable` | 0 |
| `unknown` | 0 |

These counts describe the **validation sample only**. They must not be interpreted as prevalence estimates for the MAR corpus.

## Methodological findings produced by human review

### 1. Surface role and access state are independent dimensions

A BFI URL represented a specific audiovisual item, while playback from the reviewer location returned a geographical restriction:

```text
Playback Denied: Location
PLAYER_ERR_GEO_RESTRICTED
Video is unavailable from your current location.
```

The scientifically appropriate representation was therefore:

```text
surface_type = audiovisual_item
is_item_level = true
access_state = geo_restricted
```

A restriction on playback does not transform an identifiable item surface into a general `restricted_or_unavailable` surface.

### 2. `robots.txt` is a collection condition, not a surface class

The Europeana root was blocked for the automated collector by `robots.txt`, but the human reviewer could open and identify the site as a homepage.

Therefore collection policy and human-observed surface role must remain distinct.

### 3. Thematic result pages belong to `search_or_index`

The ECPAD pages for themes such as the First World War and Second World War displayed multiple archival files associated with a thematic term. Human review classified them as `search_or_index`, not as individual items and not merely as generic archive landing pages.

This finding refined the operational meaning of `search_or_index`: the class includes thematic result/index pages that aggregate multiple records under a specific subject or term.

### 4. Lexical cues alone are insufficient

Pages containing words such as `archives`, `collections` or `presse` can play different observable roles. Surface role cannot be determined reliably from isolated lexical tokens without stronger contextual and structural evidence.

## Critical protocol deviation: original predictions were not durably persisted

The live probe called:

```python
_predictions, review = build_surface_type_artifacts(...)
```

Thus automatic predictions were computed in the runner memory before the queue was printed.

However, the temporary probe deliberately serialized only the blind review queue. The `_predictions` object was neither printed nor written to a durable file.

The repository also contained a dedicated workflow intended to persist both:

```text
data/output/m3_surface_type_predictions_v1.json
data/output/m3_surface_type_review_queue_v1.json
```

and upload them as GitHub Actions artifacts. That workflow did not produce this 17-unit sample because its pull-request branch filter did not match the temporary PR base. The 17-unit sample instead came from the deliberately failing live probe inside Quality Checks.

The temporary probe was later removed from the PR without merge after the blind queue had been captured.

### Consequence

The original deterministic predictions for these exact observations are **not durably recoverable as a frozen prediction artifact**.

Therefore this experiment cannot support a valid claim of original-model accuracy, precision, recall, F1 or per-class performance.

This is not a reason to discard the experiment. It changes its scientific role from a complete validation run to a **blind human calibration experiment with a documented reproducibility deviation**.

## Diagnostic replay after human review

After the human review was formally closed, a compact replay was created using only fields preserved in the blind queue:

- `root_url`;
- `page_url`;
- `title`;
- `fetch_status`;
- `media_urls`.

The original discovery reports also contained richer fields such as page text, metadata text and structured text, but those inputs were not preserved with the durable blind queue. Therefore the replay is not equivalent to the original classifier execution.

The replay artifact is:

```text
data/digital_infrastructure/ai_experiments/mar_surface_type_compact_replay_diagnostic_v1.json
```

Its status is explicitly `diagnostic_only`.

For diagnostic purposes, the compact replay produced:

- exact surface-type match: **2/17 = 11.8%**;
- binary item-level accuracy: **14/17 = 82.4%**;
- item-level precision: **1.00**;
- item-level recall: **0.25**;
- item-level F1: **0.40**;
- item-level specificity: **1.00**.

These values **must not be reported as the performance of the original M3 run**.

They are useful only for locating weaknesses in the present deterministic rules when given the reduced field set.

## Diagnostic weaknesses exposed

The compact replay showed several high-priority calibration targets:

1. all seven human `search_or_index` units were missed in the reduced-field replay;
2. the mechanism can confuse configured root URLs on non-root paths with `institutional_landing_page` even when the observed role is a homepage;
3. archive vocabulary can dominate pages that humans identify as search/index or editorial surfaces;
4. `presse` and similar lexical markers can over-trigger editorial classification;
5. `blocked_by_robots` should not directly determine surface role;
6. item-level recognition is conservative, reducing false positives but creating false negatives when item evidence is not represented strongly enough in preserved fields.

## Scientific interpretation

The experiment supports the following conclusions:

- the nine-class human taxonomy is usable on the 17 observed units;
- the item-level/non-item-level distinction can be applied consistently by human review;
- surface role must be separated from collection and access states;
- thematic result pages require explicit representation in `search_or_index`;
- the deterministic rule set requires calibration before ecological performance can be claimed;
- the current 17 units should be treated as a **calibration set**, not reused as the independent final validation set after rule changes.

The experiment does **not** support:

- prevalence claims about MAR surface types;
- performance estimates for the original automatic run;
- claims about institutional use or non-use of AI;
- claims about AI participation in audiovisual content;
- claims about corpus membership from surface type alone.

## Decision after experiment

M3 remains implemented structurally but is not yet empirically validated for scientific activation.

The next step is:

1. revise the deterministic rules and representation of access/collection state;
2. freeze the revised classifier version;
3. construct a new independent real-surface sample;
4. persist automatic predictions before human review;
5. compute and record a SHA-256 integrity identifier for the frozen prediction artifact;
6. generate a separate blinded review queue;
7. complete human review without prediction exposure;
8. unblind only after human closure;
9. calculate per-class and item-level performance separately;
10. document residual error before deciding whether M3 is sufficiently calibrated for downstream M4–M6 use.

The 17 units from this experiment may be used for development and regression tests, but not as the sole post-calibration estimate of generalisation performance.

## Artifact inventory

### Blind sample and human review

```text
data/digital_infrastructure/ai_experiments/mar_surface_type_review_queue_v1.json
data/digital_infrastructure/ai_experiments/mar_surface_type_human_review_v1.json
data/digital_infrastructure/ai_experiments/mar_surface_type_human_review_conclusion_v1.json
```

### Diagnostic replay

```text
data/digital_infrastructure/ai_experiments/mar_surface_type_compact_replay_diagnostic_v1.json
```

### Implementation

```text
src/memoria_audiovisual/digital_infrastructure/surface_typing.py
scripts/build_surface_type_review_queue.py
src/memoria_audiovisual/digital_infrastructure/ai_surface_discovery.py
.github/workflows/t2a-mar-surface-type-sample.yml
```

### Historical execution references

- Quality Checks run: `32291088792`
- Quality Checks job: `96191802582`
- temporary live-probe commit: `bec95975cedb82c30aa77353ab9272015413b2bd`
- live-probe removal commit: `ba311ed08df2a77220c0630966740d3ac80f1883`

## Reproducibility lesson incorporated into MAR

For all future blind validation experiments, automatic predictions are scientific experimental products and must be treated as durable data, not as transient runner state.

The minimum valid chain is therefore:

```text
frozen software + frozen protocol + sample
→ persisted prediction artifact + integrity hash
→ blinded human artifact
→ closed human conclusion
→ unblinded comparison
→ performance report
→ methodological decision
```

This requirement is now part of the MAR experiment registry policy.
