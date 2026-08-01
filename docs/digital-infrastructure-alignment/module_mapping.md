# Mapeamento entre documentação, schemas e módulos de código

| Domínio | Documentação e contratos | Módulo futuro sugerido | Responsabilidade |
|---|---|---|---|
| Entidades | schemas de instituição, tecnologia, fornecedor e relações | `src/digital_infrastructure/domain/` | modelos, IDs e invariantes |
| Proveniência | política e schema de proveniência | `src/digital_infrastructure/provenance/` | fonte, aquisição, transformação e agentes |
| Evidências | protocolo e schema de evidência | `src/digital_infrastructure/evidence/` | registro, classificação e acesso |
| Integridade | regras e relatório de integridade | `src/digital_infrastructure/integrity/` | chaves, coerência e bloqueios |
| Curadoria | governança, workflow e ações | `src/digital_infrastructure/curation/` | filas, decisões e trilha humana |
| Qualidade | política, scoring e aptidão | `src/digital_infrastructure/quality/` | qualidade, maturidade e fitness for use |
| Tempo | eventos, snapshots e migrações | `src/digital_infrastructure/timeline/` | versões, ciclos e comparações |
| Indicadores | política, catálogo e resultados | `src/digital_infrastructure/indicators/` | cálculo, cobertura e supressão |
| Ética e risco | políticas e avaliações | `src/digital_infrastructure/compliance/` | riscos, revisão e restrições |
| Publicação | manifestos, API e catálogo | `src/digital_infrastructure/publication/` | datasets, API e painel |
| Ingestão | auditoria técnica e conectores | `src/digital_infrastructure/ingestion/` | coletores, adaptadores e normalização |

## Regra de dependência

Fluxo permitido:

`ingestion → provenance/evidence → domain → integrity → curation → quality → timeline → indicators → publication`

`compliance` atua transversalmente e pode bloquear qualquer etapa posterior.

## Regra arquitetural

Módulos de publicação não devem importar diretamente coletores. Todo produto público deve ser produzido apenas a partir de snapshots fechados e registros aptos para o uso declarado.
