# Modelo de proveniência dos dados

## Objetivo

Cada registro da infraestrutura digital deve preservar uma cadeia auditável desde a fonte observada até qualquer produto derivado ou publicado. A proveniência não é um campo acessório: ela integra o dado científico e condiciona sua aptidão para uso.

## Cadeia mínima

```text
fonte observada
→ ato de obtenção
→ artefato bruto ou trecho de evidência
→ transformação documentada
→ registro estruturado
→ revisão, quando exigida
→ versão temporal e snapshot
→ resultado analítico ou produto publicado
```

Nem toda observação percorre automaticamente toda a cadeia. Registros podem permanecer pendentes, inconclusivos, não avaliáveis ou excluídos.

## Unidade de proveniência

Cada registro de proveniência referencia, conforme aplicável:

- entidade, relação, observação ou resultado afetado;
- fonte e superfície examinada;
- método de obtenção;
- artefato bruto, hash ou trecho de evidência;
- transformação aplicada;
- agente humano ou automatizado responsável;
- data e hora;
- versão do código, schema, vocabulário e metodologia;
- status de validação;
- snapshot, execução ou lote;
- vínculo com versões anteriores, correções e registros substitutos.

## Fontes

Campos mínimos possíveis:

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

A indisponibilidade posterior de uma URL não apaga a observação histórica, mas pode alterar sua verificabilidade e aptidão para publicação.

## Métodos de obtenção

Valores controlados podem incluir:

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

Cada ato de obtenção deve registrar ferramenta, versão, parâmetros, período de execução, operador, resultado e referência ao artefato bruto quando ele puder ser preservado legitimamente.

## Transformações

Toda transformação relevante deve ser explícita e reprodutível. Entre os tipos possíveis estão:

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

Uma transformação registra entradas, saídas, regra ou script, versão do código, parâmetros, schemas envolvidos, agente e data. Alteração de metodologia científica deve ser versionada separadamente de simples mudança de implementação.

## Revisão humana

A revisão preserva:

- identificador e responsável;
- data;
- decisão;
- confiança;
- evidências utilizadas;
- nota de revisão;
- estado anterior e novo estado;
- conflito de interesse, quando aplicável;
- quorum ou segunda revisão, quando exigidos.

Nenhum modelo de IA pode atuar como revisor final de uma alegação publicável. Ferramentas automatizadas podem auxiliar triagem, extração e comparação, mas a responsabilidade humana permanece identificável.

## Proveniência temporal

A proveniência deve conectar-se à memória longitudinal por identificadores estáveis de entidade, versão, evento, snapshot e execução. Essa ligação permite distinguir:

- mudança no mundo observado;
- mudança ou indisponibilidade da fonte;
- correção de erro;
- reclassificação metodológica;
- migração técnica;
- alteração de cobertura;
- falha temporária da coleta.

## Imutabilidade e correções

Registros históricos não são sobrescritos silenciosamente. Uma correção cria novo registro, evento ou revisão e aponta para o item substituído. A visão pública vigente pode mudar, mas o histórico auditável permanece preservado.

## Implementação atual

O núcleo de proveniência, evidências, artefatos brutos, ledger, persistência, decisões curatoriais e snapshots está implementado em:

```text
src/memoria_audiovisual/digital_infrastructure/
schemas/digital_infrastructure/
data/digital_infrastructure/
```

Os caminhos físicos de produtos podem variar conforme execução, snapshot e política de retenção. Este documento define o contrato conceitual; schemas e código controlam os campos executáveis.

## Regra de publicação

Um registro somente pode alimentar produto público quando possuir, conforme a finalidade:

1. fonte identificável;
2. método de obtenção documentado;
3. evidência ou artefato rastreável;
4. transformação conhecida;
5. status de revisão compatível;
6. vínculo com snapshot, versão ou execução;
7. schema e metodologia identificados;
8. cobertura e limitações publicáveis;
9. avaliação ética, jurídica ou de sensibilidade quando necessária.

## Estado de validação

A arquitetura e os mecanismos de proveniência estão implementados e cobertos por testes estruturais. A validação operacional sobre corpora reais e a verificação da completude da cadeia em ciclos integrais permanecem em andamento.
