# Validação pré-execução da revisão periódica

Antes de qualquer requisição de rede, o workflow executa:

```text
scripts/preflight_statetech_periodic_review.py
```

O preflight bloqueia a coleta quando identifica:

- `snapshot_id` inválido ou já existente;
- arquivo estrutural obrigatório ausente;
- registro central de schemas inválido, duplicado ou apontando para arquivo inexistente;
- JSON Schema que não possa ser lido como JSON;
- corpus solicitado inexistente ou sem `source_url`;
- branch histórica indicada como existente sem memória restaurada;
- ledger, manifesto ou índice JSONL corrompido;
- snapshot duplicado no índice;
- snapshot indexado sem `parameter_coverage.json` correspondente;
- diretório de estado sem permissão de escrita.

O resultado é salvo em:

```text
data/statetech/preflight/<snapshot_id>.json
```

Somente um relatório com `ok: true` permite avançar para a auditoria. O relatório também é preservado na branch `statetech-history` e incluído no artefato operacional temporário.

## Códigos iniciais

```text
PRE-001  snapshot_id inválido
PRE-002  snapshot já existente
PRE-003  arquivo estrutural ausente
PRE-004  corpus desconhecido
PRE-005  corpus sem URL
PRE-006  memória histórica não restaurada
PRE-007  JSONL corrompido
PRE-010  estado sem permissão de escrita
PRE-011–015  inconsistências no registro e nos schemas
PRE-016–018  inconsistências no índice de snapshots
```

A seleção manual de corpora também deixou de ser interpolada diretamente como fragmento de shell. O workflow converte a entrada em um array de argumentos, reduzindo risco de interpretação indevida pela linha de comando.

Nenhuma coleta ou teste foi executado durante a implementação estrutural deste componente.
