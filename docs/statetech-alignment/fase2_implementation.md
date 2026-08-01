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
→ revisão curatorial append-only
→ materialização relacional controlada
```

## Componentes já implementados

- adaptador da auditoria para observações, evidências e proveniência;
- modos `legacy`, `preview` e `ledger` no executor;
- preservação content-addressed da entrada bruta;
- manifesto de lote com retomada idempotente;
- materialização de observações confirmadas em tecnologia, relações e sistemas de IA;
- manutenção de restrições fora de contratos relacionais incompatíveis.

## Revisão curatorial append-only

O `CuratorialReviewService` registra cada decisão como novo evento no ledger. Revisões anteriores não são alteradas ou apagadas.

Cada revisão preserva:

```text
observation_id
review_id
reviewer_id
reviewer_role
decision
justification
evidence_ids
conflict_of_interest_status
reviewed_at
supersedes_review_id
```

Decisões admitidas:

```text
confirmed
probable
inconclusive
false_positive
not_assessable
needs_evidence
```

Uma nova revisão de uma observação já decidida precisa declarar explicitamente qual revisão anterior substitui. Assim, o estado atual é reconstruído a partir da cadeia histórica, sem sobrescrita.

Decisões `confirmed`, `probable` e `false_positive` exigem ao menos uma evidência vinculada. A justificativa textual é obrigatória em qualquer decisão.

## Fila de revisão

A exportação da fila reúne, por observação:

- instituição e corpus;
- grupo do detector;
- valor detectado;
- confiança automática;
- URL da evidência;
- estado curatorial atual.

Por padrão, observações já revisadas são excluídas. Elas podem ser incluídas para auditoria ou revalidação.

## Liberação para materialização

A revisão não materializa diretamente. O serviço aplica a decisão mais recente à observação e somente libera para o `CuratorialMaterializer` quando:

```text
review_status = confirmed
detection_status = detected
```

Além disso, a materialização continua exigindo `institution_id` resolvido e `evidence_id` existente. Decisões `probable`, `inconclusive`, `false_positive`, `not_assessable` ou `needs_evidence` permanecem fora da camada relacional.

## Materialização curatorial

Os grupos confirmados seguem este mapeamento:

| Grupo confirmado | Entidade gerada | Relação gerada |
|---|---|---|
| `technology` | `technology` | `institution_technology_relation` |
| `api_service` | `technology` | `institution_technology_relation` |
| `metadata_format` | `technology` | `institution_technology_relation` |
| `interoperability` | `technology` | `institution_technology_relation` |
| `search` | `technology` | `institution_technology_relation` |
| `ai_evidence` | `ai_system` | vínculo direto à instituição |

A materialização de IA permanece conservadora: função e estágio ficam `unknown` quando a evidência não sustenta classificação específica. Fornecedores não são inferidos pela simples detecção de uma tecnologia.

## Arquivos principais

```text
scripts/audit_digital_infrastructure.py
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
src/memoria_audiovisual/statetech/ingestion.py
src/memoria_audiovisual/statetech/raw_artifacts.py
src/memoria_audiovisual/statetech/ingestion_batches.py
src/memoria_audiovisual/statetech/curatorial_review.py
src/memoria_audiovisual/statetech/materialization.py
tests/test_audit_digital_infrastructure_modes.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_ingestion.py
tests/test_statetech_ingestion_artifacts.py
tests/test_statetech_curatorial_review.py
tests/test_statetech_materialization.py
```

## Garantias metodológicas

1. Ausência de detecção não é ausência tecnológica.
2. Nenhuma detecção é confirmada automaticamente.
3. Revisões são append-only e possuem cadeia explícita de substituição.
4. Decisões críticas exigem justificativa e evidência.
5. A fila separa observações pendentes das já revisadas.
6. Somente a decisão mais recente e confirmada pode liberar materialização.
7. Grupos sem contrato adequado não são forçados para entidades incompatíveis.
8. O serviço central continua responsável pela integridade referencial.

## Limites atuais

- nenhuma coleta ou migração histórica foi executada durante o desenvolvimento;
- ainda não existe interface gráfica ou CLI para o revisor humano;
- a identificação da instituição e das evidências continua dependendo de mapas explícitos;
- não foi implementada assinatura digital da decisão;
- a dupla revisão para casos de alto risco ainda não é aplicada automaticamente;
- restrições aguardam contrato de domínio próprio;
- stores e manifestos permanecem locais.

## Próximo incremento

Criar uma interface operacional de revisão em arquivo/CLI, com exportação da fila em CSV ou JSON, importação validada das decisões e exigência de dupla revisão para grupos ou riscos sensíveis antes da materialização.
