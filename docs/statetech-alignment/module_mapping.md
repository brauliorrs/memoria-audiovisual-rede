# Mapeamento entre documentação, schemas e módulos de código

| Domínio | Documentação e contratos | Módulo futuro sugerido | Responsabilidade |
|---|---|---|---|
| Entidades | schemas de instituição, tecnologia, fornecedor e relações | `src/statetech/domain/` | modelos, IDs e invariantes |
| Proveniência | política e schema de proveniência | `src/statetech/provenance/` | fonte, aquisição, transformação e agentes |
| Evidências | protocolo e schema de evidência | `src/statetech/evidence/` | registro, classificação e acesso |
| Integridade | regras e relatório de integridade | `src/statetech/integrity/` | chaves, coerência e bloqueios |
| Curadoria | governança, workflow e ações | `src/statetech/curation/` | filas, decisões e trilha humana |
| Qualidade | política, scoring e aptidão | `src/statetech/quality/` | qualidade, maturidade e fitness for use |
| Tempo | eventos, snapshots e migrações | `src/statetech/timeline/` | versões, ciclos e comparações |
| Indicadores | política, catálogo e resultados | `src/statetech/indicators/` | cálculo, cobertura e supressão |
| Ética e risco | políticas e avaliações | `src/statetech/compliance/` | riscos, revisão e restrições |
| Publicação | manifestos, API e catálogo | `src/statetech/publication/` | datasets, API e painel |
| Ingestão | auditoria técnica e conectores | `src/statetech/ingestion/` | coletores, adaptadores e normalização |

## Regra de dependência

Fluxo permitido:

`ingestion → provenance/evidence → domain → integrity → curation → quality → timeline → indicators → publication`

`compliance` atua transversalmente e pode bloquear qualquer etapa posterior.

## Regra arquitetural

Módulos de publicação não devem importar diretamente coletores. Todo produto público deve ser produzido apenas a partir de snapshots fechados e registros aptos para o uso declarado.
