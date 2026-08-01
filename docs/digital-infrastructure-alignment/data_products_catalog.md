# Catálogo estrutural de produtos de dados

## Finalidade

Organizar os produtos previstos para a camada de infraestrutura e relações infraestrutura digital, sem pressupor que todos serão disponibilizados na primeira versão pública.

## Produtos internos

| Produto | Conteúdo | Acesso | Retenção |
|---|---|---|---|
| Raw acquisition archive | Artefatos brutos e respostas das fontes | interno | conforme política de retenção |
| Heuristic detection register | Sinais automáticos ainda não revisados | interno | longo prazo |
| Curatorial review register | Decisões, justificativas e falsos positivos | interno | permanente |
| Integrity report | Erros, alertas e exceções | interno | por ciclo |
| Entity resolution register | Fusões, separações e reconciliação de entidades | interno | permanente |

## Produtos públicos curados

| `product_type` | Formato | Unidade principal | Periodicidade esperada |
|---|---|---|---|
| `institution_registry` | CSV/JSON/API | instituição | anual |
| `technology_registry` | CSV/JSON/API | tecnologia | anual |
| `provider_registry` | CSV/JSON/API | fornecedor | anual |
| `institution_technology_relations` | CSV/JSON/API | relação | trimestral/anual |
| `procurement_contracts` | CSV/JSON/API | contrato | trimestral/anual |
| `data_flows` | CSV/JSON/API | fluxo | anual |
| `ai_systems` | CSV/JSON/API | sistema de IA | trimestral/anual |
| `risk_assessments` | CSV/JSON/API | avaliação | anual |
| `timeline_events` | CSV/JSON/API | evento | contínuo por snapshot |
| `indicator_results` | CSV/JSON/API/painel | indicador | por snapshot |
| `snapshot_manifest` | JSON | snapshot | todo fechamento |
| `comparison_report` | JSON/CSV/painel | par de snapshots | por comparação |

## Pacotes científicos

Cada publicação científica poderá gerar um pacote versionado contendo:

- manifesto;
- dados curados utilizados;
- dicionário de variáveis;
- schemas;
- definições de indicadores;
- relatório de cobertura;
- relatório de integridade;
- notas de comparabilidade;
- citação recomendada;
- licença.

## Dependências entre produtos

```text
snapshot_manifest
├── institution_registry
├── technology_registry
├── provider_registry
├── relations
├── contracts
├── data_flows
├── ai_systems
├── risk_assessments
├── timeline_events
└── indicator_results
```

Um produto derivado deverá referenciar os produtos-base usados em sua geração.

## Identificação

Formato recomendado:

```text
mar:<product_type>:<scope>:<snapshot_id>:v<publication_version>
```

Exemplo estrutural:

```text
mar:indicator_results:europe:snap-2027-annual:v1.0.0
```

## Estado editorial

Todo produto terá um dos estados:

- `draft`;
- `under_review`;
- `approved`;
- `published`;
- `superseded`;
- `withdrawn`;
- `archived`.

## Requisitos de citação

O produto publicado deverá oferecer:

- título;
- autores ou equipe responsável;
- ano;
- versão;
- snapshot;
- URL persistente ou DOI, quando disponível;
- licença;
- data de acesso sugerida para recursos dinâmicos.
