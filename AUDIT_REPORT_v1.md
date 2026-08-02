# Repository Audit Report v1

**Repository:** `brauliorrs/memoria-audiovisual-rede`  
**Audited branch:** `feature/fase2-adaptador-auditoria-infraestrutura`  
**Pull request:** #5  
**Audit date:** 2026-08-02

## 1. Audit scope

This audit verifies the current state of Pull Request #5 using the files reported by GitHub for the branch, the pull-request metadata and the latest GitHub Actions run associated with the audited commit.

The audit distinguishes four states:

- **Verified:** present in the audited branch or confirmed by a successful automated check.
- **Implemented but not empirically validated:** code and tests exist, but real-world detector accuracy has not yet been reviewed.
- **Missing:** the expected repository file was not found.
- **Pending merge:** present only in the feature branch and therefore not yet visible on the default `main` branch.

## 2. Branch and visibility status

The international documentation and the Phase 2 implementation are present in the feature branch used by Pull Request #5. They have **not been merged into `main`**.

This explains why the changes may not appear when the GitHub mobile application opens the repository on its default branch. To inspect them before the merge, the reader must open Pull Request #5 or switch to:

```text
feature/fase2-adaptador-auditoria-infraestrutura
```

**Status:** Pending merge.

## 3. Pull request status

At the audited commit, Pull Request #5 is:

- open;
- not a draft;
- not merged;
- reported as mergeable by GitHub;
- composed of 199 changed files and 167 commits relative to `main`.

The pull-request description is outdated. It still states that the complete test suite needs to be stabilised and identifies an earlier publication-revision task as the next increment, although later increments and successful checks are already present.

**Required correction:** update the PR title and body before merge so that they reflect the actual scope and current validation status.

## 4. Automated quality checks

The latest `Quality Checks` workflow associated with the audited commit completed successfully.

The following steps passed:

- dependency installation;
- Python module compilation;
- unit tests;
- deployment snapshot check.

**Status:** Automated structural validation passed.

This does not yet constitute empirical validation of detectors against real archive websites.

## 5. International documentation

The following files are verified in the audited branch:

```text
README.md
README.pt-BR.md
docs/research/README.md
docs/research/00_introduction.md
docs/research/01_research_problem.md
docs/research/02_scientific_framework.md
docs/research/03_methodological_framework.md
docs/research/04_system_architecture.md
docs/research/05_corpus_policy.md
docs/research/06_analytics.md
docs/research/07_scientific_indicators.md
docs/research/08_operational_validation.md
docs/research/09_roadmap.md
docs/research/10_future_research.md
docs/research/11_publications_and_outputs.md
docs/research/12_reuse_and_collaboration.md
docs/research/executive_summary.md
```

**Status:** Produced and verified in the feature branch; pending merge into `main`.

## 6. Scientific and methodological documentation

The repository contains documented structures for:

- the scientific problem and research questions;
- digital-infrastructure observation;
- provenance and evidence;
- snapshots and longitudinal comparison;
- human review and curatorial governance;
- publication versions and active-publication registry;
- corpus eligibility and exclusion of paid commercial image or video banks;
- analytics, methodological versioning and persistence;
- scientific indicators and sensitivity analysis;
- operational validation and roadmap.

There is substantial overlap between `docs/research/`, `docs/analytics/` and `docs/digital-infrastructure-alignment/`. The overlap is not necessarily incorrect, because the folders address different audiences, but it now requires an editorial cross-reference review to avoid contradictions and repeated definitions.

**Status:** Documented; editorial consistency review pending.

## 7. Code architecture

The audited branch includes dedicated packages for:

```text
src/memoria_audiovisual/digital_infrastructure/
src/memoria_audiovisual/analytics/
```

Verified implementation areas include:

- adapters and ingestion;
- evidence, provenance and validation;
- content-addressed raw artefacts;
- ledger and index stores;
- entity decisions and curatorial review;
- parameter coverage;
- preflight and postflight validation;
- event triage and event review;
- historical migration;
- public derived views;
- publication revisions;
- active-publication registry;
- public-delivery projection;
- analytics engine and registry;
- analytical storage;
- access and interoperability indicators;
- composite index and sensitivity analysis.

**Status:** Implemented and covered by automated tests; real-world operational validation pending.

## 8. Scientific indicators

The branch contains implementations and documentation for:

- Audiovisual Archive Access Index;
- API coverage;
- interoperability coverage;
- IIIF coverage;
- OAI-PMH coverage;
- Dublin Core coverage;
- Schema.org coverage;
- JSON-LD coverage;
- composite interoperability index;
- interoperability-index sensitivity analysis.

The access index uses eligible audiovisual archives as its population and excludes paid commercial image or video banks from the scientific corpus.

**Status:** Implemented and tested with controlled fixtures; empirical denominator and detector accuracy still need manual validation on real corpora.

## 9. Corpus policy

The repository verifies a separation between:

```text
Discovery Registry
→ classification
→ eligibility decision
→ scientific corpus
→ observation and analytics
```

Paid commercial image or video banks are catalogued but excluded from the research corpus and from analytical denominators.

**Status:** Implemented and documented.

## 10. Workflows

The feature branch contains three Phase 2 workflows:

```text
.github/workflows/digital-infrastructure-periodic-review.yml
.github/workflows/digital-infrastructure-publication-revision.yml
.github/workflows/digital-infrastructure-activate-publication.yml
```

They cover periodic observation, publication regeneration and explicit activation of a public version.

The periodic workflow is configured for monthly execution as well as manual dispatch. It preserves durable state in the `digital-infrastructure-history` branch.

**Status:** Workflow definitions verified; end-to-end execution with live corpora still requires controlled operational validation.

## 11. Nomenclature refactoring

A legacy path named:

```text
docs/statetech-alignment/module_mapping.md
```

appears in the pull-request changed-file list because it is being **deleted**. Its patch confirms complete removal in the feature branch.

The current implementation paths use the generic expression `digital_infrastructure` / `digital-infrastructure-alignment`.

**Status:** Legacy file removal verified in the PR diff.

## 12. Repository governance files

The following expected files were checked directly in the audited branch and were not found:

```text
LICENSE
CITATION.cff
CONTRIBUTING.md
```

They are therefore not yet part of the repository presentation package.

The existence of `CODE_OF_CONDUCT.md`, `SECURITY.md` and a formal governance document was not confirmed in this audit and must be checked before international release.

**Status:** Incomplete.

## 13. Main risks identified

### Critical before merge

1. The PR description no longer represents the actual content and validation state.
2. The feature branch has accumulated 167 commits and 199 changed files, making review and rollback difficult.
3. The documentation is not yet visible on the default branch.
4. The repository lacks a verified licence, citation file and contribution guide.

### Important before external presentation

1. Review the English README for claims that imply empirical validation rather than implementation readiness.
2. Verify all internal links in the Research Handbook.
3. Resolve terminology differences among the research, analytics and digital-infrastructure documentation.
4. Add exact contact, ORCID and citation metadata only after confirming them.
5. Run a controlled real-world validation sample and publish the resulting validation protocol and findings.

### Important before the first official collection

1. Validate false positives and false negatives for every detector group.
2. Manually verify the access index classification.
3. Confirm that paid commercial banks are excluded in actual corpus metadata, not only in unit-test fixtures.
4. Exercise the periodic workflow end to end without publishing unreviewed claims.
5. Confirm restoration and persistence in `digital-infrastructure-history`.

## 14. Overall assessment

| Area | Assessment |
|---|---|
| Core Phase 2 architecture | Verified in branch |
| Automated quality checks | Passed |
| Research Handbook | Verified in branch |
| English and Portuguese landing pages | Verified in branch |
| Scientific indicators | Implemented and unit-tested |
| Empirical detector validation | Pending |
| End-to-end live workflow validation | Pending |
| Repository governance package | Incomplete |
| Default-branch visibility | Pending merge |
| PR description accuracy | Outdated |

## 15. Recommended next sequence

1. Update the PR title and description to reflect the complete Phase 2 scope.
2. Add or decide the repository licence before inviting external reuse.
3. Add `CITATION.cff` and `CONTRIBUTING.md`.
4. Perform an editorial and link audit of the English documentation.
5. Execute a controlled validation with a small, representative corpus sample.
6. Record false positives, false negatives and manual decisions.
7. Only after these corrections, perform the final merge review.

## 16. Audit conclusion

The documentation and implementation previously discussed are genuinely present in Pull Request #5, but only in its feature branch. The latest automated quality workflow is green. The project is technically much more advanced than the current PR description indicates.

The work is not yet ready to be declared fully validated or internationally released because empirical detector validation, repository governance files and final editorial review remain incomplete.
