# Fase 2 — adaptação da auditoria e ingestão

## Objetivo

Conectar a auditoria heurística de infraestrutura digital ao núcleo de dados e proveniência da Fase 1, sem executar coleta e sem publicar resultados.

## Fluxo implementado

```text
InfrastructureAudit
→ DigitalInfrastructureAuditAdapter
→ observações normalizadas por sinal
→ IngestionCoordinator
→ preview validado ou commit controlado
→ artefato bruto imutável
→ manifesto de lote
→ StatetechDataService
→ ledger
```

## Adaptador da auditoria

A saída agregada do coletor é desmembrada em uma observação por valor detectado. Cada observação recebe identificador, chave natural, snapshot, detector, evidência e proveniência.

| Campo legado | Grupo normalizado |
|---|---|
| `cms` | `technology` |
| `api_types` | `api_service` |
| `metadata_formats` | `metadata_format` |
| `interoperability_protocols` | `interoperability` |
| `search_mechanisms` | `search` |
| `access_restrictions` | `restriction` |
| `ai_cataloguing_evidence` | `ai_evidence` |

Detecções automáticas permanecem `pending_review`. Fontes inacessíveis geram `unknown` e `not_assessable`, nunca ausência tecnológica. Evidências textuais de IA recebem confiança baixa e não confirmam uso operacional.

## Coordenador de ingestão

O `IngestionCoordinator` oferece dois modos:

- `preview`: adapta e valida o lote sem gravar entidades no ledger;
- `commit`: pré-valida o lote e encaminha cada registro ao serviço central.

Chaves naturais duplicadas dentro de um mesmo lote são bloqueadas antes da persistência.

## Artefato bruto

Quando `RawArtifactStore` e `BatchManifestStore` são configurados, a entrada original é serializada de forma canônica e preservada antes do commit.

```text
conteúdo bruto
→ JSON canônico
→ SHA-256
→ artifact_id content-addressed
→ arquivo imutável e deduplicado
```

O mesmo conteúdo produz sempre o mesmo `artifact_id`. O identificador do artefato é acrescentado a `input_artifact_ids` da proveniência de cada registro persistido.

## Manifesto e retomada idempotente

O `batch_id` é derivado de:

```text
adapter_name
+ adapter_version
+ source_artifact_id
```

O manifesto append-only registra os estados:

```text
prepared
running
completed
failed
```

Após cada registro concluído, a respectiva combinação `entity_type:natural_key` é acrescentada ao manifesto. Se a ingestão for interrompida, uma nova chamada com o mesmo conteúdo e a mesma versão do adaptador:

1. localiza o mesmo lote;
2. recupera as chaves já concluídas;
3. não grava novamente esses registros;
4. continua a partir dos registros restantes;
5. encerra o lote como `completed` ou registra nova falha.

Essa retomada evita duplicação causada por interrupção do processo, mas não substitui a integridade do serviço central nem transforma o JSONL em transação ACID.

## Arquivos principais

```text
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
src/memoria_audiovisual/statetech/ingestion.py
src/memoria_audiovisual/statetech/raw_artifacts.py
src/memoria_audiovisual/statetech/ingestion_batches.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_ingestion.py
tests/test_statetech_ingestion_artifacts.py
```

## Garantias metodológicas

1. Ausência de detecção não é ausência tecnológica.
2. Nenhuma detecção é confirmada automaticamente.
3. Adaptadores não coletam, persistem ou publicam.
4. Preview não modifica o ledger.
5. Todos os contratos são validados antes do início do commit.
6. A entrada bruta pode ser preservada de forma imutável e verificável.
7. O manifesto permite retomada sem repetir chaves já concluídas.
8. O serviço central continua responsável pela integridade referencial.

## Limites atuais

- o executor existente ainda não oferece modos `preview` e `ledger`;
- nenhuma coleta ou migração histórica foi executada;
- tecnologias e fornecedores ainda não são materializados como entidades relacionais;
- a retomada depende de stores locais configurados em conjunto;
- o manifesto é append-only local, não um coordenador distribuído;
- alteração da versão do adaptador gera um novo lote, mesmo para a mesma fonte;
- não há ainda política automática de retenção dos artefatos brutos.

## Próximo incremento

Adaptar o executor da auditoria para oferecer explicitamente:

```text
legacy  → CSV/JSON atuais
preview → validação e plano sem commit
ledger  → artefato bruto, manifesto e persistência controlada
```

Depois, materializar tecnologias, APIs e protocolos confirmados como entidades relacionais, sem promover sinais pendentes automaticamente.
