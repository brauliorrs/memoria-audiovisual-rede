# Modelo de proveniência dos dados

## Objetivo

Cada registro da camada Estado–tecnologia deve preservar uma cadeia auditável desde a fonte original até a versão publicada. A proveniência não é um campo acessório: ela é parte do próprio dado científico.

## Cadeia mínima de proveniência

```text
fonte original
    ↓
ato de obtenção
    ↓
artefato bruto
    ↓
transformação
    ↓
registro estruturado
    ↓
validação humana
    ↓
versão temporal
    ↓
produto publicado
```

## Unidade de proveniência

Cada etapa recebe um `provenance_id` único e referencia:

- entidade ou relação afetada;
- fonte utilizada;
- método de obtenção;
- artefato bruto ou trecho de evidência;
- transformação aplicada;
- agente humano ou automatizado responsável;
- data e hora;
- versão do código, schema e contrato de dados;
- status de validação;
- vínculo com versões anteriores e posteriores.

## Fontes

Campos mínimos:

- `source_id`;
- `source_type`;
- `source_url`;
- `source_title`;
- `publisher_or_authority`;
- `source_published_at`;
- `accessed_at`;
- `language`;
- `jurisdiction`;
- `license_or_terms`;
- `content_hash`;
- `archive_url`, quando houver;
- `availability_status`.

Tipos de fonte:

- portal institucional;
- página técnica;
- API;
- documento de contratação;
- portal de compras públicas;
- relatório institucional;
- política de privacidade;
- termos de uso;
- documentação de software;
- comunicado de imprensa;
- artigo científico;
- registro comercial público;
- observação direta da interface;
- cabeçalhos HTTP e metadados da página.

## Métodos de obtenção

Valores controlados:

- `manual_review`;
- `web_scraping`;
- `api_request`;
- `bulk_download`;
- `document_extraction`;
- `http_inspection`;
- `metadata_inspection`;
- `public_procurement_query`;
- `repository_import`;
- `curatorial_entry`.

Cada ato de obtenção deve registrar:

- `acquisition_id`;
- `method`;
- `tool_or_script`;
- `tool_version`;
- `parameters`;
- `started_at`;
- `completed_at`;
- `operator_type`;
- `operator_id`;
- `result_status`;
- `raw_artifact_path`;
- `raw_artifact_hash`.

## Transformações

Toda transformação deve ser explícita e reprodutível.

Campos:

- `transformation_id`;
- `input_artifact_ids`;
- `output_record_ids`;
- `transformation_type`;
- `script_or_rule`;
- `code_commit_sha`;
- `parameters`;
- `schema_version_before`;
- `schema_version_after`;
- `executed_at`;
- `agent_type`;
- `agent_id`;
- `notes`.

Tipos:

- normalização;
- deduplicação;
- resolução de entidade;
- classificação;
- extração de campo;
- conversão de formato;
- agregação;
- enriquecimento;
- migração de schema;
- correção curatorial.

## Revisão humana

A revisão deve preservar:

- `review_id`;
- `reviewer_id`;
- `reviewed_at`;
- `decision`;
- `confidence`;
- `evidence_ids`;
- `review_note`;
- `previous_status`;
- `new_status`;
- `conflict_of_interest_note`, quando aplicável.

Decisões possíveis:

- `confirmed`;
- `probable`;
- `inconclusive`;
- `false_positive`;
- `not_assessable`;
- `needs_more_evidence`.

## Proveniência temporal

A proveniência deve se conectar ao modelo de memória por meio de:

- `entity_id` estável;
- `version_id`;
- `event_id`;
- `snapshot_id`;
- `previous_provenance_id`;
- `supersedes_provenance_id`;
- `change_origin`.

Assim, a plataforma distingue:

- mudança real no mundo observado;
- mudança na fonte;
- correção de erro;
- reclassificação metodológica;
- migração técnica do modelo de dados.

## Agentes

Agentes podem ser:

- pesquisador;
- revisor;
- script;
- workflow;
- API externa;
- modelo de IA auxiliar;
- processo de migração.

Nenhum modelo de IA pode ser registrado como revisor final. Decisões publicáveis exigem responsabilidade humana identificada.

## Imutabilidade e correções

Registros de proveniência são imutáveis. Uma correção cria novo evento e novo registro, preservando o anterior como supersedido.

## Produtos previstos

```text
data/provenance/
├── sources.csv
├── acquisitions.csv
├── transformations.csv
├── reviews.csv
├── agents.csv
└── provenance_links.csv

data/history/
├── snapshots/
├── events/
└── entity_versions/
```

## Regra de publicação

Um registro só poderá alimentar produto público quando possuir:

1. fonte identificada;
2. método de obtenção documentado;
3. evidência ou artefato rastreável;
4. transformação conhecida, quando houver;
5. status de validação compatível;
6. vínculo com versão temporal e snapshot;
7. schema e contrato de dados versionados.

Este documento define somente a arquitetura. Nenhuma coleta, transformação ou validação foi executada.