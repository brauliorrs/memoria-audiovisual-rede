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

## Inventário científico derivado

O arquivo `inventory.json` é regenerado diretamente de `CORPORA` e resume apenas dimensões estruturais comuns:

- total de unidades;
- agregadores e instituições;
- corpora ativos e inativos;
- habilitação de atualização mensal;
- completude dos campos estruturais obrigatórios.

O inventário não altera o corpus e não possui autoridade sobre sua composição. Em caso de divergência, a fonte canônica e o manifesto prevalecem.

Regeneração e validação:

```bash
python scripts/build_reference_corpus_inventory.py
python scripts/build_reference_corpus_inventory.py --check
```

## Artefatos derivados futuros

Snapshots de cobertura, resultados dos indicadores e registros de proveniência serão produzidos no Sprint 2C. Eles devem referenciar a versão e o hash do manifesto.

## Validação do manifesto

```bash
python scripts/audit_reference_corpus_manifest.py
```
