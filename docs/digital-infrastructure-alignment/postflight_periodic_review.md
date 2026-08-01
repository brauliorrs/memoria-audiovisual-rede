# Pós-flight da revisão periódica infraestrutura digital

## Finalidade

O pós-flight é a barreira entre uma coleta aparentemente concluída e a consolidação da rodada na branch `digital-infrastructure-history`. Ele não corrige dados nem altera relatórios: apenas verifica se os produtos da rodada são semanticamente coerentes.

## Momento de execução

```text
preflight
→ coleta e ingestão
→ cobertura e comparação
→ verificação de arquivos
→ pós-flight semântico
→ commit na branch histórica
```

Se o pós-flight retornar erro, a branch histórica não é atualizada.

## Verificações

O validador confirma:

- correspondência do `snapshot_id` entre comando, resumo, cobertura e índice;
- presença dos sete grupos para cada corpus;
- inexistência de `missing_observation` em uma rodada declarada concluída;
- pelo menos uma observação associada a cada grupo;
- número esperado de linhas: corpora multiplicados por sete parâmetros;
- coerência entre `source_count`, corpora cobertos e número de lotes;
- coerência entre `record_count`, observações da cobertura, commits e retomadas;
- presença única do snapshot no índice de cobertura;
- coerência de `corpus_count` e `parameter_count` no manifesto;
- presença, no manifesto persistido, dos lotes informados no resumo;
- legibilidade estrutural do ledger, do índice e do manifesto JSONL.

## Relatório

O relatório é preservado em:

```text
data/digital_infrastructure/postflight/<snapshot_id>.json
```

Estrutura resumida:

```json
{
  "snapshot_id": "snapshot_2026_08_01T201700Z",
  "ok": true,
  "corpus_count": 12,
  "coverage_row_count": 84,
  "observation_count": 97,
  "issues": []
}
```

## Códigos iniciais

- `POST-001`: arquivo ausente, JSON ou JSONL inválido;
- `POST-002`: divergência de snapshot no resumo;
- `POST-003`: linha de cobertura estruturalmente inválida;
- `POST-004`: grupo sem observação;
- `POST-005`: cobertura sem observação associada;
- `POST-006`: grupos incompletos ou inconsistentes por corpus;
- `POST-007`: lista de lotes inválida;
- `POST-008`: divergência entre fontes e corpora cobertos;
- `POST-009`: dimensão incorreta da matriz de cobertura;
- `POST-010`: divergência da contagem de observações;
- `POST-011`: commits e retomadas não fecham o total;
- `POST-012`: divergência entre lotes e fontes;
- `POST-013`: snapshot ausente ou duplicado no índice;
- `POST-014`: manifesto divergente dos relatórios;
- `POST-015`: lote do resumo ausente no manifesto persistido.

## Limite

A validação estrutural do ledger confirma que o arquivo pode ser lido como JSONL. Uma auditoria profunda da cadeia de entidades, versões, evidências e proveniência permanece responsabilidade do auditor de integridade da Fase 1.
