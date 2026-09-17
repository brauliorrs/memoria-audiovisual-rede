# Onda 1 — namespace e contratos do núcleo

## Escopo

Este recorte torna `memoria_audiovisual.digital_infrastructure` o namespace canônico do núcleo já validado na `main`, sem importar as extensões longitudinais dos PRs #5 ou #7.

São migrados: IDs e versões, modelos/proveniência, contratos e validação, evidências, persistência append-only, locking/ledger, integridade, decisões curatoriais e serviço de dados.

`memoria_audiovisual.statetech` permanece temporariamente como camada de compatibilidade que reexporta os mesmos objetos canônicos. Os demais módulos ainda residentes em `statetech` continuam operacionais e passam a consumir o núcleo por esses shims.

## Invariantes preservadas

- O namespace lógico padrão de `stable_id` continua sendo `statetech`; o caminho Python novo não altera IDs históricos.
- O registro físico de schemas continua em `schemas/statetech/schema_registry.json` nesta onda; sua eventual migração exige gate separado.
- Persistência e ledger continuam append-only.
- `pending_review` continua sendo o estado padrão para entidade, proveniência e evidência.
- A URL individual continua participando da identidade de evidência.
- As invariantes da Porta 2 permanecem protegidas pelos testes `test_digital_infrastructure_audit.py` e `test_digital_infrastructure_phase2.py`.
- O adaptador de auditoria corrigido na Porta 2 não é substituído pela versão antiga existente no PR #5.

## Fora de escopo

Não entram nesta onda: ingestão longitudinal, raw artifact store, batches, coverage, materialização, analytics, publicação científica, UI, T2A/IA ou artefatos históricos dos mega-PRs.

## Gate

A onda só pode avançar quando a suíte completa, o teste de compatibilidade de namespace, o contrato da Porta 2, a checagem de dependências e o deployment snapshot estiverem verdes no mesmo HEAD.
