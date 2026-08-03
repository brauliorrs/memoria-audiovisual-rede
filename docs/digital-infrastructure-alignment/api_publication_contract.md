# Contrato estrutural da API pública

## Escopo

A API pública será uma interface somente leitura para dados curados e produtos agregados. Esta documentação define sua arquitetura futura, sem implementar endpoints.

## Princípios

- versionamento explícito no caminho;
- respostas vinculadas a snapshot;
- ausência de acesso à camada bruta;
- paginação e filtros previsíveis;
- metadados de cobertura e proveniência em toda resposta;
- compatibilidade preservada dentro da mesma versão principal.

## Base path prevista

```text
/api/v1/
```

## Endpoints previstos

```text
GET /api/v1/snapshots
GET /api/v1/snapshots/{snapshot_id}
GET /api/v1/institutions
GET /api/v1/institutions/{institution_id}
GET /api/v1/technologies
GET /api/v1/providers
GET /api/v1/relations
GET /api/v1/contracts
GET /api/v1/data-flows
GET /api/v1/ai-systems
GET /api/v1/risks
GET /api/v1/events
GET /api/v1/indicators
GET /api/v1/indicators/{indicator_id}/results
GET /api/v1/comparisons/{comparison_id}
```

## Envelope de resposta

Toda resposta deverá conter:

```json
{
  "meta": {
    "api_version": "v1",
    "snapshot_id": "...",
    "schema_version": "...",
    "generated_at": "...",
    "coverage": {},
    "provenance": {},
    "limitations": []
  },
  "data": [],
  "pagination": {}
}
```

## Filtros transversais

Quando aplicáveis:

- `snapshot_id`;
- `country`;
- `institution_type`;
- `public_private_status`;
- `stack_layer`;
- `provider_id`;
- `validation_status`;
- `observed_from`;
- `observed_to`;
- `limit`;
- `cursor`.

## Regras de exposição

A API não deverá:

- retornar registros pendentes;
- expor documentos protegidos ou artefatos brutos;
- transformar `null` em ausência afirmada;
- combinar snapshots incompatíveis sem aviso;
- apresentar avaliação de risco sem regra e versão associadas.

## Erros previstos

- `400` filtro inválido;
- `404` entidade ou snapshot inexistente;
- `409` comparação incompatível;
- `422` consulta metodologicamente não publicável;
- `429` limite de uso;
- `503` produto temporariamente indisponível.

## Cache e reprodutibilidade

Snapshots fechados poderão receber cache de longa duração, pois são imutáveis. Consultas ao snapshot corrente deverão informar explicitamente que o ciclo ainda não está fechado e não serão tratadas como publicação científica estável.

## Descontinuação

Campos e endpoints não serão removidos dentro de uma versão principal sem período de depreciação documentado. Alterações incompatíveis exigirão nova versão principal da API.
