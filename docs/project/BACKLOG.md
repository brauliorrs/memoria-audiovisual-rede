# Project Backlog

This backlog separates future improvements from the frozen scope required for the first international scientific presentation of the platform.

## Current Priority — Frozen Scope

### Language MVP+

1. Detect hybrid-language phrases in public interface text.
2. Audit visible Streamlit components.
3. Generate a concise report grouped by page or module.
4. Review the Home page in Portuguese, English and Spanish.
5. Review the Research module in Portuguese, English and Spanish.
6. Review the Analytics module in Portuguese, English and Spanish.
7. Perform manual validation of the main presentation path in all three languages.
8. Confirm readiness for the first scientific presentation.

New features that do not block the presentation must not enter this scope.

## High Priority — Visual Architecture and Responsiveness

**Status:** Backlog

**Objective:** reduce visual pollution and reorganize the analytical interface around vertical reading, progressive disclosure and responsive use on mobile phones and tablets.

Core rule:

> Large corpora, wide datasets and analytically dense sections must default to a vertical presentation. Horizontal layouts should be limited to short comparisons and small groups of summary metrics.

Required work:

1. inventory the visual structure of every page and tab;
2. identify excessive columns, wide tables and side-by-side charts;
3. reduce the number of metrics displayed on the same row;
4. prioritise top-to-bottom reading and progressive detail;
5. replace unnecessarily wide corpus tables with vertical records, cards, lists or compact essential-column views;
6. move secondary fields to details, expanders or unit-specific views;
7. avoid mandatory horizontal scrolling on primary mobile routes;
8. validate layouts on mobile, tablet and desktop widths;
9. define reusable Streamlit patterns for metrics, tables, charts and large corpora;
10. prototype the Overview page and one large-corpus page before applying changes globally.

The detailed backlog, acceptance criteria and responsive rules are documented in:

`docs/project/VISUAL_ARCHITECTURE_BACKLOG.md`

**Priority:** high, connected to the public showcase, Streamlit performance and scientific presentation quality.

## After the First Scientific Presentation

### Scientific Internationalization Audit — SIA

**Status:** Backlog

**Objective:** evolve the Language MVP+ into a complete scientific internationalization quality system.

Potential future scope:

- multilingual coverage metrics by page, module and component;
- semantic terminology validation;
- inspection of constants and deeply nested structures;
- structured-data and dataclass inspection;
- translation provenance and review status;
- automatic terminology consistency checks;
- translation quality indicators;
- a complete internationalization quality gate;
- migration of all public interface text to semantic translation keys.

**Reason for postponement:** these capabilities are useful for long-term maintenance but do not block the first scientific presentation. They will be reconsidered only after the initial contact and presentation cycle.

## Backlog Rule

An idea remains in the backlog when it improves the platform but does not prevent a clear, credible and linguistically consistent presentation of the current research infrastructure.
