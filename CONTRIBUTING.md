# Contributing to Memória Audiovisual em Rede

Thank you for considering a contribution to **Memória Audiovisual em Rede**.

The project is a scientific research infrastructure. Contributions must therefore preserve methodological transparency, provenance, reproducibility and the distinction between automatically detected evidence and verified institutional facts.

## Ways to contribute

Contributions may include:

- corrections to documentation and translations;
- reports of broken links, unstable routes or changed access conditions;
- proposals for new archive or aggregator candidates;
- improvements to collectors, detectors, schemas and validation routines;
- tests and controlled validation cases;
- methodological critiques and indicator proposals;
- reproducibility checks and dataset documentation.

## Before opening a contribution

1. Check whether the proposed entity belongs in the Discovery Registry or the Scientific Corpus.
2. Do not treat a public webpage, automated detection or search result as a verified institutional fact without evidence and review.
3. Record the source URL, observation date, acquisition method and relevant limitations.
4. Do not bypass authentication, paywalls, robots.txt or technical access restrictions.
5. Do not add personal data unless it is strictly necessary, publicly available and methodologically justified.
6. Preserve historical records; do not silently overwrite prior observations.

## Development workflow

1. Create a focused branch.
2. Keep changes limited to one coherent purpose.
3. Add or update tests when behaviour changes.
4. Run the validation suite:

```bash
python -m compileall -q app src scripts tests
python -m unittest discover -s tests -v
python scripts/check_deployment_ready.py
python scripts/check_markdown_links.py
```

5. Describe the scientific or operational rationale in the pull request.
6. State whether the change affects schemas, indicators, denominators, eligibility, public outputs or historical compatibility.

## New corpus candidates

A proposal for a new archive, institution or aggregator should include:

- official name and URL;
- country or territorial scope;
- entity type;
- audiovisual relevance;
- public routes observed;
- access restrictions;
- evidence of collectable audiovisual records or a justified negative result;
- relationship to existing aggregators;
- recommended status: discovery only, protocolled candidate or eligible corpus.

New candidates do not enter analytical denominators until eligibility and assessability have been reviewed.

## Indicators and analytical methods

Any new indicator must document:

- scientific question;
- population and unit of analysis;
- numerator and denominator;
- eligibility and exclusion rules;
- non-assessable states;
- formula and version;
- interpretation and limitations;
- validation requirements;
- provenance of each published result.

Sensitive or ambiguous claims require human review.

## Documentation hierarchy

Use `docs/research/` as the canonical scientific narrative. Use `docs/analytics/` for computational indicator specifications and `docs/digital-infrastructure-alignment/` for technical implementation and governance details. See `docs/DOCUMENTATION_GOVERNANCE.md`.

## Licensing

By contributing, you agree that software contributions are licensed under the MIT License and original documentation or project-produced data contributions are licensed under CC BY 4.0, as described in `LICENSE`.

## Conduct and review

Contributions may be declined when they lack evidence, weaken reproducibility, introduce unsupported institutional claims, mix discovery records with the scientific corpus, or conflict with legal and ethical constraints.
