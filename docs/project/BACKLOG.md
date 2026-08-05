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

## High Priority — Corpus Intake and Index Refresh Policy

**Status:** Backlog

**Objective:** establish a predictable, auditable and scientifically controlled rule for incorporating new corpora and recalculating continental and global indicators.

### Proposed threshold rule

A new index refresh round should be opened whenever **20 new eligible and validated corpora from the same continent** have been incorporated since the last completed round for that continent.

The count must be cumulative by continent and must not mix corpora from different continental groups merely to reach the threshold.

### Eligibility conditions for counting toward the threshold

A corpus only counts toward the group of 20 when it has:

1. stable institutional identity and continent assignment;
2. minimum required metadata completed;
3. evidence and provenance recorded;
4. structural validation completed;
5. evaluability status defined;
6. inclusion decision approved under the corpus governance rules;
7. no unresolved blocking integrity issue.

Entries that are duplicated, pending review, not assessable, excluded, experimental or still awaiting evidence do not count toward the threshold.

### Actions triggered by reaching 20 corpora

When a continent reaches the threshold, the platform should initiate a controlled refresh round containing at least:

1. opening of a new observation cycle for the affected continent;
2. freezing of the eligible corpus list for that round;
3. execution of collection and validation procedures;
4. recalculation of continental indicators;
5. recalculation of global indicators affected by the new continental denominator;
6. generation of updated coverage, eligibility and non-assessability statistics;
7. comparison with the previous continental snapshot;
8. review of material changes and possible methodological distortions;
9. publication decision through the existing editorial and governance gates;
10. preservation of the previous results as an immutable historical version.

### Exceptions that may anticipate a round

The threshold of 20 is the ordinary operational trigger, not an absolute prohibition. A refresh may be opened earlier when there is:

- a methodological change that affects comparability;
- correction of a material error in published results;
- incorporation of a strategically relevant national or regional block;
- substantial change in the evaluability of the existing corpus;
- documented event that materially affects access, infrastructure or preservation conditions;
- need to synchronise a scientific publication, report or formal research milestone.

Every anticipated round must record its justification and must not be presented as equivalent to a regular 20-corpus round without explicit disclosure.

### Rules for incomplete accumulation

- fewer than 20 validated corpora remain in a continental intake queue;
- queued corpora may appear in the inventory as pending incorporation but do not alter published indices;
- the queue must record continent, eligibility state, validation state and date of entry;
- counts restart from zero only after a round is formally closed for that continent;
- corpora excluded during the round return neither to the denominator nor to the next count unless revalidated.

### Decisions still required

1. confirm whether 20 is the definitive threshold after simulation with current corpus sizes;
2. define treatment for transcontinental institutions and international aggregators;
3. define whether small continents or regions require a proportional alternative threshold;
4. establish the exact indicator set recalculated at continental and global levels;
5. define whether the round includes only new corpora or also reobserves the existing continental corpus;
6. define maximum waiting time when a continent does not reach 20 additions;
7. create an automated counter and round-readiness report;
8. integrate the trigger with snapshot, analytics and publication workflows.

### Acceptance criteria

- the platform can report how many validated corpora remain before the next round for each continent;
- only eligible corpora increment the counter;
- a round freezes its corpus composition and methodology before calculation;
- continental and affected global denominators are explicitly versioned;
- previous indices remain recoverable;
- early rounds require documented justification;
- the public interface displays the reference date, corpus size and methodological version of every index.

**Priority:** high, because the rule directly affects longitudinal comparability, index stability and the scientific governance of platform growth.

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
