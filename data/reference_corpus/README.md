# Scientific Reference Corpus Manifest

Este diretório identifica o **Corpus de Referência Científica v1.0** sem duplicar os dados canônicos da plataforma.

A fonte única do corpus permanece no objeto `CORPORA`, definido em:

```text
src/memoria_audiovisual/corpora.py
```

O `manifest.json` congela a identidade desse estado por meio de:

- versão do manifesto;
- caminho e seletor da fonte canônica;
- revisão Git de origem;
- hash Git blob do conteúdo;
- quantidade esperada de unidades;
- versões dos registros de indicadores e metodologias.

## Política de versionamento

Qualquer alteração no conteúdo de `CORPORA` que pretenda compor um novo baseline científico exige uma nova versão do manifesto. O estado v1.0 não deve ser atualizado silenciosamente.

## Fonte única

Não existe uma cópia `corpus_reference_v1.0.json`. Essa ausência é deliberada: o manifesto referencia a fonte canônica e impede a criação de uma segunda fonte de verdade.

## Artefatos derivados

Snapshots de cobertura, resultados dos indicadores e registros de proveniência serão produzidos no Sprint 2C. Eles não pertencem a este manifesto e devem referenciar sua versão e hash.

## Validação

```bash
python scripts/audit_reference_corpus_manifest.py
```
