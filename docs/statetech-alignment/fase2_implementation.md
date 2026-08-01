# Fase 2 — adaptação da auditoria e ingestão

## Objetivo do primeiro incremento

Conectar a auditoria heurística de infraestrutura digital já existente ao núcleo de dados e proveniência concluído na Fase 1, sem executar coleta e sem publicar resultados.

## Fluxo implementado

```text
InfrastructureAudit
→ DigitalInfrastructureAuditAdapter
→ uma observação normalizada por sinal
→ evidência vinculada
→ proveniência vinculada
→ AdaptedRecord
→ StatetechDataService (etapa seguinte)
```

## Decisões metodológicas

1. A saída agregada do coletor é desmembrada em uma observação por valor detectado.
2. Cada observação recebe `observation_id`, chave natural, snapshot, detector e versão.
3. Toda detecção permanece `pending_review` até decisão curatorial.
4. Fontes inacessíveis geram estado `unknown` e `not_assessable`, nunca ausência tecnológica.
5. Evidências textuais de IA recebem confiança baixa e não significam uso operacional confirmado.
6. O adaptador transforma dados, mas não grava no ledger e não publica.
7. A auditoria original permanece preservada; este incremento adiciona uma camada de compatibilidade.

## Mapeamento inicial

| Campo legado | Grupo normalizado |
|---|---|
| `cms` | `technology` |
| `api_types` | `api_service` |
| `metadata_formats` | `metadata_format` |
| `interoperability_protocols` | `interoperability` |
| `search_mechanisms` | `search` |
| `access_restrictions` | `restriction` |
| `ai_cataloguing_evidence` | `ai_evidence` |

## Arquivos

```text
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
tests/test_statetech_digital_infrastructure_adapter.py
```

## Limites deste incremento

- não altera o script de coleta;
- não executa auditoria;
- não grava no ledger;
- não cria instituições, tecnologias ou fornecedores como entidades relacionais;
- não resolve automaticamente URLs de evidência específicas para cada sinal;
- não calcula confiança com regras diferenciadas por detector;
- não migra os CSV/JSON históricos.

## Próximos incrementos

1. Criar um coordenador de ingestão que envie `AdaptedRecord` ao serviço central.
2. Validar cada registro contra o schema antes do commit.
3. Criar entidades relacionais para tecnologias, APIs e protocolos confirmados.
4. Preservar a saída bruta da auditoria como artefato de proveniência.
5. Adaptar o executor para oferecer modo legado e modo ledger.
6. Preparar migração controlada de arquivos históricos, sem executá-la automaticamente.
