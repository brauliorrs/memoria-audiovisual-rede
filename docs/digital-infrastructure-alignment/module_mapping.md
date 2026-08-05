# Mapeamento entre documentação, contratos e módulos existentes

Este documento relaciona os domínios documentais aos módulos atualmente implementados. Ele não substitui a documentação interna do código nem implica que todos os componentes tenham sido validados empiricamente.

| Domínio | Documentação e contratos | Implementação principal | Responsabilidade |
|---|---|---|---|
| Entidades e IDs | schemas de instituição, tecnologia, fornecedor e relações | `src/memoria_audiovisual/digital_infrastructure/models.py`, `ids.py`, `contracts.py` | modelos, identificadores e invariantes |
| Proveniência | `data_provenance_model.md` e schema de proveniência | `evidence.py`, `raw_artifacts.py`, `ingestion.py` | fonte, aquisição, transformação e agentes |
| Evidências | `evidence_and_validation_protocol.md` e schema de evidência | `evidence.py`, `validation.py`, `review_files.py` | registro, classificação, validação e acesso |
| Integridade | `relational_integrity.md` e regras de integridade | `integrity.py`, `ledger.py`, `index.py`, `index_store.py` | coerência, referências, histórico e bloqueios |
| Curadoria | `curatorial_governance.md` e workflows de revisão | `curatorial_review.py`, `entity_decisions.py`, `event_review.py` | filas, decisões e trilha humana |
| Qualidade e aptidão | políticas de qualidade e fitness for use | `preflight.py`, `postflight.py`, `parameter_coverage.py`, `coverage_reports.py` | cobertura, qualidade operacional e bloqueios |
| Memória temporal | eventos, snapshots e migrações | `persistence.py`, `historical_migration.py`, `event_triage.py` | versões, ciclos, comparação e migração |
| Indicadores | Research Handbook e registros computáveis | `src/memoria_audiovisual/analytics/` | cálculo, cobertura, persistência e sensibilidade |
| Ética e risco | políticas e protocolos de risco | contratos, validação e revisão humana; indicadores de risco ainda não ativos | limites, revisão e contestabilidade |
| Publicação | políticas, manifestos e projeções públicas | `public_view.py`, `public_delivery.py`, `active_publication.py`, `publication_revision.py` | produtos derivados e publicação versionada |
| Ingestão | auditoria técnica e adaptadores | `adapters.py`, `digital_infrastructure_adapter.py`, `ingestion_batches.py` | adaptação, normalização e commits controlados |

## Fluxo arquitetural

```text
ingestão
→ evidência e proveniência
→ validação e integridade
→ revisão curatorial
→ snapshot e memória
→ analytics
→ revisão de publicação
→ visão pública derivada
```

As avaliações ética, jurídica e de risco atuam transversalmente e podem bloquear qualquer etapa posterior.

## Regras permanentes

- módulos de publicação não acessam diretamente coletores;
- produtos públicos são derivados de registros compatíveis com o uso declarado;
- resultados sensíveis preservam vínculo com evidência, snapshot e decisão humana;
- caminhos de código são referências de implementação, não garantias de validação empírica;
- propostas ainda não implementadas devem permanecer no backlog, não neste mapa de módulos existentes.
