# Modelo de fluxos de dados

## Objetivo

Representar movimentos observáveis de metadados, mídia, autenticação, analytics e outros dados entre instituições, sistemas e plataformas.

## Unidade `DataFlow`

- `data_flow_id`;
- `source_entity_id` e `source_entity_type`;
- `destination_entity_id` e `destination_entity_type`;
- `data_flow_type`;
- `data_exchange_method`;
- `data_format`;
- `transfer_frequency`;
- `purpose`;
- `personal_data_signal`;
- `cross_border_data_flow`;
- `third_party_processing`;
- `automated_decision_signal`;
- `evidence_id`;
- `validation_status`.

## Tipos iniciais

- ingestão e exportação de metadados;
- sincronização de catálogo;
- consulta por API;
- exportação em lote;
- streaming de mídia;
- distribuição/sindicação de conteúdo;
- autenticação federada;
- rastreamento analítico;
- transferência manual.

## Métodos iniciais

`REST`, `GraphQL`, `OAI-PMH`, `IIIF`, `SPARQL`, `SFTP`, `RSS/Atom`, `embed`, `redirect`, `webhook`, `manual_upload`, `unknown`.

## Regras

- não classificar link simples como fluxo de dados sem observar intercâmbio relevante;
- diferenciar hospedagem da mídia, incorporação e redirecionamento;
- tratar analytics de terceiros como fluxo próprio quando houver evidência;
- marcar fluxos transfronteiriços apenas quando origem/destino ou residência forem sustentados;
- não inferir tratamento de dados pessoais apenas pela presença de cookies;
- permitir direção `unknown` quando a evidência comprovar integração, mas não seu sentido.