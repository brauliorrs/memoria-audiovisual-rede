# Integração da cobertura infraestrutura digital ao ciclo periódico

## Finalidade

A revisão periódica dos corpora existentes passa a produzir, além das observações técnicas, uma matriz explícita de cobertura dos sete grupos de parâmetros e uma comparação com o snapshot anterior.

## Fluxo

```text
CORPORA ativos
→ auditoria periódica
→ observações normalizadas
→ matriz de cobertura por corpus e snapshot
→ persistência do relatório do snapshot
→ localização do snapshot anterior
→ relatório de mudanças
```

## Saídas por snapshot

```text
data/digital_infrastructure/coverage/
├── snapshot_coverage_index.jsonl
└── <snapshot_id>/
    ├── parameter_coverage.json
    └── parameter_changes.json
```

O primeiro snapshot não possui `parameter_changes.json`, pois cria a linha de base. A partir da segunda rodada, o relatório longitudinal registra `unchanged`, `appeared`, `disappeared`, `changed`, `error`, `not_assessable`, `still_missing` ou `baseline_created`.

## Regras

1. O modo `ledger` salva automaticamente a cobertura.
2. O modo `preview` calcula a cobertura, mas só a grava quando usado com `--write-coverage`.
3. Um relatório de snapshot existente não é sobrescrito.
4. A ausência de observação permanece distinta de `not_detected`.
5. Corpora antigos são completados pela próxima rodada normal, sem recriação de identidade.
6. O índice de cobertura é append-only e permite localizar a rodada anterior.

## Exemplo futuro

```powershell
python scripts/audit_digital_infrastructure.py `
  --mode ledger `
  --snapshot-id snapshot_2026_08
```

A execução produzirá as observações no ledger, o relatório de cobertura e, havendo rodada anterior, o relatório de mudanças infraestrutura digital.

## Limite atual

A integração está implementada no executor da auditoria. O workflow periódico já existente ainda precisa chamar explicitamente esse executor em modo `ledger` e fornecer um `snapshot_id` único para cada rodada.
