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
→ revisão curatorial
→ materialização relacional controlada
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

## Artefato bruto e retomada

Quando `RawArtifactStore` e `BatchManifestStore` são configurados, a entrada original é serializada de forma canônica, identificada por SHA-256 e preservada antes do commit. O manifesto append-only registra `prepared`, `running`, `completed` e `failed`, permitindo retomada sem repetir chaves já concluídas.

Essa retomada reduz duplicações causadas por interrupção, mas não transforma o JSONL em transação ACID.

## Executor com três modos

O script `scripts/audit_digital_infrastructure.py` oferece:

```text
legacy  → CSV e JSON históricos
preview → coleta, adaptação e validação sem commit
ledger  → artefato bruto, manifesto e persistência controlada
```

`legacy` permanece como padrão. `preview` e `ledger` exigem `--snapshot-id`.

## Materialização curatorial

O `CuratorialMaterializer` atua depois da revisão humana. Ele não lê sinais pendentes como fatos e não confirma observações automaticamente.

Uma observação só pode ser promovida quando reúne simultaneamente:

```text
review_status = confirmed
detection_status = detected
institution_id resolvido
evidence_id existente
```

Grupos com contrato relacional disponível são materializados assim:

| Grupo confirmado | Entidade gerada | Relação gerada |
|---|---|---|
| `technology` | `technology` | `institution_technology_relation` |
| `api_service` | `technology` | `institution_technology_relation` |
| `metadata_format` | `technology` | `institution_technology_relation` |
| `interoperability` | `technology` | `institution_technology_relation` |
| `search` | `technology` | `institution_technology_relation` |
| `ai_evidence` | `ai_system` | vínculo direto à instituição |

A materialização de IA é deliberadamente conservadora: mesmo após confirmação da evidência, função e estágio de implantação permanecem `unknown` quando a observação não sustenta classificação mais específica.

O grupo `restriction` ainda não é promovido, porque não existe contrato relacional próprio adequado. Ele permanece na observação curada com decisão `not_materialized`, evitando encaixá-lo artificialmente como tecnologia.

Cada tentativa produz uma decisão explícita:

```text
promoted
blocked
not_materialized
```

Bloqueios registram razões como revisão não confirmada, detecção não positiva, ausência de instituição ou ausência de evidência.

## Arquivos principais

```text
scripts/audit_digital_infrastructure.py
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
src/memoria_audiovisual/statetech/ingestion.py
src/memoria_audiovisual/statetech/raw_artifacts.py
src/memoria_audiovisual/statetech/ingestion_batches.py
src/memoria_audiovisual/statetech/materialization.py
tests/test_audit_digital_infrastructure_modes.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_ingestion.py
tests/test_statetech_ingestion_artifacts.py
tests/test_statetech_materialization.py
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
9. Somente observações confirmadas podem alimentar entidades relacionais.
10. Grupos sem contrato adequado não são forçados para uma entidade incompatível.
11. O serviço central continua responsável pela integridade referencial.

## Limites atuais

- nenhuma coleta ou migração histórica foi executada durante o desenvolvimento;
- a materialização exige mapas explícitos de instituição e evidência;
- a camada ainda não oferece interface de revisão humana;
- fornecedores não são inferidos a partir da tecnologia detectada;
- restrições aguardam contrato de domínio próprio;
- a retomada depende de stores locais configurados em conjunto;
- não há política automática de retenção dos artefatos brutos.

## Próximo incremento

Criar o fluxo de revisão curatorial das observações, com decisão append-only, identificação do revisor, justificativa, vínculo às evidências e exportação de uma fila de revisão. Depois, conectar somente decisões aprovadas ao `CuratorialMaterializer`.
