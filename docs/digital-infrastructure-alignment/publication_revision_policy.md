# Política de revisão derivada da publicação

## Objetivo

Permitir que revisões humanas concluídas depois do fechamento de uma rodada sejam incorporadas à visão pública sem modificar a coleta, a triagem ou a primeira versão pública do snapshot.

## Regra de imutabilidade

Os arquivos iniciais permanecem em:

```text
data/digital_infrastructure/public/<snapshot_id>/events.json
data/digital_infrastructure/public/<snapshot_id>/manifest.json
```

Eles não podem ser sobrescritos. Cada regeneração cria uma revisão derivada:

```text
data/digital_infrastructure/public/<snapshot_id>/revisions/
├── revision_0001/
│   ├── events.json
│   └── manifest.json
├── revision_0002/
│   ├── events.json
│   └── manifest.json
└── ...
```

## Fonte da regeneração

A revisão é reconstruída a partir de:

1. eventos longitudinais originais do snapshot;
2. ledger append-only atualizado com as decisões humanas;
3. mesmas regras de quórum e elegibilidade usadas na visão pública inicial.

Não é permitido editar diretamente o arquivo público anterior para acrescentar ou retirar eventos.

## Manifesto

Cada revisão registra:

- `snapshot_id`;
- `publication_revision` sequencial;
- `revision_id`;
- revisão anterior substituída;
- justificativa;
- responsável pela solicitação;
- eventos adicionados, removidos e alterados;
- decisões humanas utilizadas;
- data de geração.

A substituição ocorre apenas no sentido editorial: versões anteriores continuam preservadas e recuperáveis.

## Uso operacional

```powershell
python scripts/regenerate_digital_infrastructure_public_view.py `
  --snapshot-id snapshot_2026_09 `
  --events data/digital_infrastructure/triage/snapshot_2026_09.json `
  --ledger data/digital_infrastructure/ledger.jsonl `
  --output-root data/digital_infrastructure/public `
  --reason "Incorporação de decisões curatoriais concluídas após o fechamento" `
  --requested-by "curator_id"
```

## Restrições

- a visão pública inicial precisa existir;
- `snapshot_id`, justificativa e solicitante são obrigatórios;
- eventos de outro snapshot são rejeitados;
- a numeração de revisão é sequencial;
- uma revisão existente não pode ser sobrescrita;
- a regeneração não executa nova coleta;
- a regeneração não altera o ledger, os snapshots ou os relatórios de cobertura.
