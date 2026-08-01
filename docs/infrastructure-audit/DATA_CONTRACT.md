# Contrato de dados da auditoria de infraestrutura

## Objetivo

Este contrato separa três níveis que não devem ser confundidos:

1. **observação da rota**: resposta técnica da superfície pública;
2. **detecção heurística**: sinal produzido por regra automatizada;
3. **validação curatorial**: interpretação humana documentada.

## Identificação da observação

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `observation_id` | string | sim | Identificador estável da observação |
| `snapshot_id` | string | sim | Ciclo ou snapshot ao qual pertence |
| `observed_at` | datetime ISO 8601 | sim | Data e hora UTC da observação |
| `corpus_code` | string | sim | Código existente em `CORPORA` |
| `institution_name` | string | sim | Nome da unidade observada |
| `entity_level` | enum | sim | `aggregator`, `institution` ou outro nível documentado |
| `country` | string/null | não | País da unidade, quando disponível |
| `source_url` | URI | sim | Rota inicialmente solicitada |
| `final_url` | URI/null | não | Rota após redirecionamentos |
| `http_status` | integer/null | não | Código HTTP obtido |
| `collection_status` | enum | sim | `success`, `partial`, `blocked`, `timeout`, `error`, `not_attempted` |

## Registro de detecção

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `detector_group` | enum | sim | Grupo analítico do detector |
| `detected_value` | string | sim | Tecnologia, padrão, serviço ou restrição detectada |
| `detection_status` | enum | sim | `detected`, `not_detected`, `unknown`, `not_applicable` |
| `automatic_confidence` | enum | sim | `high`, `medium`, `low` |
| `detector_id` | string | sim | Nome estável da regra usada |
| `detector_version` | string | sim | Versão da regra ou do contrato |
| `evidence_source` | enum | sim | `header`, `html`, `metadata`, `link`, `form`, `script`, `text`, `url_pattern` |
| `evidence_value` | string/null | não | Trecho, chave ou padrão que originou o sinal |
| `evidence_url` | URI | sim | Rota concreta da evidência |

Valores de `detector_group`:

- `technology`;
- `api_service`;
- `metadata_format`;
- `interoperability`;
- `search`;
- `restriction`;
- `ai_evidence`.

## Validação curatorial

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `review_status` | enum | sim | Situação da revisão |
| `reviewed_at` | datetime/null | não | Data da revisão |
| `reviewer` | string/null | não | Identificador do revisor |
| `review_note` | string/null | não | Justificativa da decisão |
| `supporting_source` | URI/null | não | Documentação externa usada na triangulação |

Valores de `review_status`:

- `pending_review`;
- `confirmed`;
- `probable`;
- `inconclusive`;
- `false_positive`;
- `not_assessable`.

## Regras de qualidade

- `confirmed` exige evidência inequívoca na superfície ou documentação oficial complementar.
- `probable` exige mais de um sinal convergente ou um sinal forte sem confirmação documental.
- `not_detected` não pode ser convertido automaticamente em afirmação de inexistência.
- `ai_evidence` deve registrar declaração explícita; termos genéricos como “inteligente” ou “automático” não bastam.
- `restriction` descreve a superfície observada e não toda a política institucional.
- redirecionamentos devem preservar `source_url` e `final_url`.
- erros de rede devem ser diferenciados de bloqueios e de ausência de tecnologia.
- resultados brutos nunca são sobrescritos pela revisão humana.

## Chave e deduplicação

Chave lógica recomendada:

```text
snapshot_id + corpus_code + evidence_url + detector_id + detected_value
```

A deduplicação deve ocorrer apenas dentro do mesmo snapshot e da mesma evidência. Registros de snapshots diferentes devem permanecer para permitir análise longitudinal.

## Compatibilidade com CSV

Campos multivalorados devem ser serializados como JSON em uma célula ou normalizados em uma tabela longa. Para análise e validação, recomenda-se o formato longo: uma linha por detecção e evidência.

## Versionamento

Versão inicial deste contrato: `1.0.0`.

Alterações incompatíveis exigem incremento de versão principal. Inclusão de campos opcionais pode incrementar a versão secundária.