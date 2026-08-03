# Registro de publicação pública vigente

Cada snapshot pode possuir uma versão pública inicial e revisões derivadas posteriores. Nenhuma versão histórica é apagada ou sobrescrita.

O estado operacional atual é mantido em:

```text
data/digital_infrastructure/public/active_publications.json
```

O histórico append-only de ativações é preservado em:

```text
data/digital_infrastructure/public/publication_activation_history.jsonl
```

Para cada snapshot, o registro vigente informa:

- tipo da publicação (`initial` ou `revision`);
- número da revisão, sendo `0` para a versão inicial;
- identificador da publicação;
- caminhos dos eventos e do manifesto;
- quantidade de eventos;
- responsável, justificativa e data da ativação;
- publicação anteriormente vigente.

A ativação valida a existência dos arquivos, o snapshot declarado, a contagem de eventos e, para revisões, o número e o identificador da revisão. Uma mesma versão não pode ser ativada novamente.

A versão vigente é uma referência operacional. Ela não modifica os arquivos da versão inicial nem das revisões anteriores. O arquivo de estado atual pode ser reconstruído a partir do histórico de ativações e dos manifestos preservados.

## CLI

Versão inicial:

```bash
python scripts/activate_digital_infrastructure_publication.py \
  --snapshot-id snapshot_2026_09 \
  --publication-kind initial \
  --activated-by periodic-workflow \
  --reason "Visão pública inicial validada"
```

Revisão:

```bash
python scripts/activate_digital_infrastructure_publication.py \
  --snapshot-id snapshot_2026_09 \
  --publication-kind revision \
  --revision-number 1 \
  --activated-by curator_id \
  --reason "Revisão curatorial tardia consolidada"
```
