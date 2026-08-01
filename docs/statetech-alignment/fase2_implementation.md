# Fase 2 — adaptação da auditoria e ingestão

## Objetivo

Conectar a auditoria heurística de infraestrutura digital ao núcleo de dados e proveniência concluído na Fase 1, sem executar coleta e sem publicar resultados.

## Fluxo implementado

```text
InfrastructureAudit
→ DigitalInfrastructureAuditAdapter
→ uma observação normalizada por sinal
→ evidência vinculada
→ proveniência vinculada
→ AdaptedRecord
→ IngestionCoordinator
→ pré-visualização validada ou commit controlado
→ StatetechDataService
```

## Adaptador da auditoria

A saída agregada do coletor é desmembrada em uma observação por valor detectado. Cada observação recebe `observation_id`, chave natural, snapshot, detector, versão, evidência e proveniência.

Regras metodológicas:

1. Toda detecção permanece `pending_review` até decisão curatorial.
2. Fontes inacessíveis geram `unknown` e `not_assessable`, nunca ausência tecnológica.
3. Evidências textuais de IA recebem confiança baixa e não significam uso operacional confirmado.
4. O adaptador transforma dados, mas não grava no ledger e não publica.
5. A auditoria original permanece preservada.

## Coordenador de ingestão

O `IngestionCoordinator` separa dois modos:

### Preview

```text
adaptar
→ validar o adaptador
→ validar todos os contratos
→ detectar chaves duplicadas no lote
→ devolver plano de ingestão
→ não modificar o ledger
```

### Commit

```text
adaptar
→ pré-validar o lote completo
→ encaminhar cada registro ao StatetechDataService
→ persistir entidade, evidências e proveniência
→ devolver entity_id e version_id
```

A pré-validação impede que um erro de contrato encontrado no meio do lote inicie a persistência. Ainda assim, o commit ocorre registro a registro, porque a unidade transacional da Fase 1 é uma entidade com suas evidências e proveniência. Uma falha externa durante a escrita de um lote pode, portanto, exigir retomada controlada.

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
src/memoria_audiovisual/statetech/ingestion.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_ingestion.py
```

## Garantias atuais

- ausência de detecção não é convertida em ausência de tecnologia;
- nenhuma detecção é confirmada automaticamente;
- preview não persiste dados;
- todos os registros são validados antes do início do commit;
- chaves naturais duplicadas no mesmo lote são rejeitadas;
- adaptadores não acessam diretamente o ledger;
- o serviço central permanece responsável pela integridade e persistência.

## Limites atuais

- não altera o script de coleta;
- não executa auditoria;
- não cria instituições, tecnologias ou fornecedores como entidades relacionais;
- não preserva ainda o artefato bruto da resposta HTTP;
- não resolve automaticamente URLs de evidência específicas para cada sinal;
- não migra os CSV/JSON históricos;
- não oferece retomada automática de lote parcialmente persistido.

## Próximos incrementos

1. Preservar a saída bruta da auditoria como artefato de proveniência com hash.
2. Adaptar o executor para oferecer modo legado, preview e ledger.
3. Criar manifesto de lote e mecanismo de retomada idempotente.
4. Materializar tecnologias, APIs e protocolos confirmados como entidades relacionais.
5. Preparar migração controlada de arquivos históricos, sem execução automática.
