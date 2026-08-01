# Fase 2 — adaptação da auditoria e ingestão

## Objetivo

Conectar a auditoria heurística de infraestrutura digital ao núcleo de dados e proveniência da Fase 1, sem publicar resultados automaticamente.

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

O manifesto append-only registra `prepared`, `running`, `completed` e `failed`. Após cada registro concluído, a respectiva combinação `entity_type:natural_key` é acrescentada ao manifesto. Uma nova chamada com o mesmo conteúdo e a mesma versão do adaptador recupera as chaves concluídas e processa apenas as restantes.

Essa retomada reduz duplicações causadas por interrupção, mas não transforma o JSONL em transação ACID.

## Executor com três modos

O script `scripts/audit_digital_infrastructure.py` passou a oferecer três modos explícitos.

### `legacy`

É o modo padrão e preserva o comportamento anterior:

```text
coleta
→ DataFrame
→ digital_infrastructure_audit.csv
→ digital_infrastructure_audit.json
```

Nenhuma configuração adicional é exigida.

### `preview`

```text
coleta
→ adaptação
→ validação integral
→ resumo do plano
→ nenhum commit no ledger
```

Exige `--snapshot-id`. O coordenador é criado sem stores de artefato e manifesto, evitando persistência do núcleo. Um resumo JSON pode ser solicitado com `--result-output`.

Exemplo:

```powershell
python scripts/audit_digital_infrastructure.py --mode preview --snapshot-id snapshot_2026_q3 --limit 5 --result-output data/output/statetech_preview.json
```

### `ledger`

```text
coleta
→ adaptação e validação
→ preservação do artefato bruto
→ manifesto retomável
→ StatetechDataService
→ ledger append-only
```

Também exige `--snapshot-id`. Os caminhos padrão são:

```text
data/statetech/ledger.jsonl
data/statetech/raw_artifacts/
data/statetech/ingestion_batches.jsonl
```

Eles podem ser substituídos por `--ledger-path`, `--artifact-dir` e `--batch-manifest`.

Exemplo:

```powershell
python scripts/audit_digital_infrastructure.py --mode ledger --snapshot-id snapshot_2026_q3 --corpus europeana ina
```

## Arquivos principais

```text
scripts/audit_digital_infrastructure.py
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
src/memoria_audiovisual/statetech/ingestion.py
src/memoria_audiovisual/statetech/raw_artifacts.py
src/memoria_audiovisual/statetech/ingestion_batches.py
tests/test_audit_digital_infrastructure_modes.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_ingestion.py
tests/test_statetech_ingestion_artifacts.py
```

## Garantias metodológicas

1. Ausência de detecção não é ausência tecnológica.
2. Nenhuma detecção é confirmada automaticamente.
3. O modo histórico permanece o padrão seguro.
4. `preview` não modifica o ledger.
5. `ledger` exige snapshot explícito.
6. Todos os contratos são validados antes do início do commit.
7. A entrada bruta pode ser preservada de forma imutável e verificável.
8. O manifesto permite retomada sem repetir chaves já concluídas.
9. O serviço central continua responsável pela integridade referencial.

## Limites atuais

- nenhuma coleta ou migração histórica foi executada durante o desenvolvimento;
- tecnologias e fornecedores ainda não são materializados como entidades relacionais;
- a retomada depende de stores locais configurados em conjunto;
- o manifesto é append-only local, não um coordenador distribuído;
- alteração da versão do adaptador gera um novo lote para a mesma fonte;
- não há política automática de retenção dos artefatos brutos;
- o executor coleta primeiro e somente depois inicia preview ou commit;
- o modo ledger ainda não cria entidades relacionais a partir dos sinais pendentes.

## Próximo incremento

Criar a camada de materialização curatorial para transformar apenas observações confirmadas em entidades relacionais de tecnologia, API, protocolo, formato de metadados, mecanismo de busca, restrição e sistema de IA. Sinais `pending_review`, `inconclusive` ou `false_positive` não poderão ser promovidos.
