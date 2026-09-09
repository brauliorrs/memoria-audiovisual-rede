# M3 surface typing post-validation calibration — protocol 2.2.0

## Status

Protocol **2.2.0** is a **development/calibration candidate only**. It was revised after the independent failure of protocol 2.1.0 in `MAR-T2A-M3-VAL-005`.

The three completed human-labelled sets now contain **86 unique URLs** (17 + 33 + 36). All 86 are development data for 2.2.0 and are prohibited from serving as independent performance evidence for this protocol.

## What changed

The 2.2 revision remains deterministic and avoids archive-specific ID memorisation. It adds:

- singular audiovisual-detail recognition when route structure and explicit audiovisual title markers agree;
- strong list/index evidence from Schema.org `ItemList`, filters, advanced-search language and pagination;
- removal of the generic `research` → search shortcut;
- precedence for direct audiovisual-object evidence before list inference;
- broader generic AJAX filter semantics for theme/format endpoints;
- optional per-entity caps in the blind-review queue builder so future samples can be balanced across corpora.

## Development regression

The original 17-unit calibration set and the 33-unit former 2.0 validation set remain regression/development fixtures.

The completed 36-unit VAL-005 set is also now reused **only for development diagnosis**. Under the current 2.2 candidate, its binary item-level development diagnostic is:

- TP: 10
- TN: 22
- FP: 0
- FN: 4
- precision: 100%
- recall: 71.43%
- F1: 83.33%
- specificity: 100%
- accuracy: 88.89%

All seven DFF human audiovisual-item trailer pages are recovered as `audiovisual_item`.

**These are not independent performance metrics.** The labels directly informed the revision.

## Unresolved boundaries

### Cinéam

Several detail URLs are technically near-identical: they use `_doc`, `page=1`, oEmbed media, descriptions and comparable route structure, yet the human review contains both D and G labels. Protocol 2.2 does not encode document IDs or slugs to reproduce those labels artificially.

### CICLIC

Magazine pages with embedded media include both a human `item_record` case and a human `news_or_editorial` case. Embedded media alone therefore remains insufficient to override editorial context.

## Engineering checks

Quality Checks run `33673383542`, job `100392132459`, completed successfully with **754 tests passed and 2 subtests passed**. This establishes engineering/regression integrity, not ecological validation.

## Scientific decision

Accept 2.2.0 only as the next M3 development candidate.

The next step is a new preregistered independent ecological validation with:
1. entirely unseen corpora;
2. all 86 known URLs excluded;
3. predictions frozen before human review;
4. a balanced per-entity sample;
5. no tuning after freeze;
6. a new human review completed before predictions are opened.

M4 remains **not cleared for scaling** until that new validation is completed and acceptable.
