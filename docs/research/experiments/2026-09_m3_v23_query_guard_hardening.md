# M3 2.3.0-dev — query guard hardening

Date: 2026-09-14
Parent: `aaf11778f26bbbaa43aa1aa9e13e4d7f06455864` (`presentation/rpv-1`).
Scope: continuation of `MAR-T2A-M3-CAL-008`, development only.

## Preserved scientific state

VAL-007 remains closed and frozen. M3 2.2.0 failed its independent gates;
M4 scaling remains blocked. This patch changes neither the frozen classifier,
human labels, predictions, evaluation, access implementation nor official T2 baseline.
The previously published CAL-008 replay report remains a historical development
record, not a new independent result.

## Reproduced problems and change

Synthetic negative controls reproduced two false item promotions in the existing
candidate: `/films/family-history/?q=family` and `/Ficha.aspx?note=Video`.

- Explicit search parameters and singular/plural bracketed facet/filter parameters
  take precedence over candidate audiovisual upgrades, even with embedded media.
- Author/category filters cannot upgrade a non-item decision through embedded media.
  Previously resolved item decisions with author metadata retain their semantics.
- Audiovisual query values are interpreted only under type-bearing keys: `type`,
  `media_type`, `mediatype`, `content_type`, and `contenttype` (case insensitive).
  Search text, arbitrary notes and campaign parameters do not declare media type.
- Access state and access evidence are copied unchanged from the frozen base.

These rules use no institution names, item IDs or observed slugs.
Seven synthetic negative controls were added; they are development evidence only.

## Verification

Executed locally with the pinned repository requirements and pytest:

```bash
PYTHONPATH=src python -m pytest tests/test_surface_typing.py tests/test_surface_typing_v23_candidate.py tests/test_surface_type_review_queue.py -q
PYTHONPATH=src python -m pytest -q
```

- Focused suite: 58 passed.
- Full suite: 774 passed, 2 subtests passed.
- One pre-existing invalid-escape SyntaxWarning in `digital_infrastructure_audit.py`.
- All four known-data regression sets (17 + 33 + 36 + 31 units) retain their
  existing test constraints; no new independent metric is claimed.

## Next boundary

The candidate remains `2.3.0-dev` and is not promoted to the production classifier.
The next independent protocol needs a frozen implementation, preregistered unseen
entities and deterministic sampling, exclusions for all known development data,
sealed predictions, and a blind human-review freeze before prediction disclosure.
The numerical gates suggested in conversation are proposals, not approved changes
to the preregistered gates. No new validation identifier is assigned by this patch.
