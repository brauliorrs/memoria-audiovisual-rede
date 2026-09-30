# Matriz de sobreposição: PRs #5, #7 e #8

Esta matriz identifica pontos que não podem ser reconciliados por merge automático ou escolha integral de um lado.

| Área | PR #8 | PR #5 | PR #7 | Regra de reconciliação |
|---|---|---|---|---|
| Coleta heurística | `src/memoria_audiovisual/digital_infrastructure_audit.py` | consumida pelo adaptador novo | altera o mesmo coletor | preservar comportamento do #8 e reaplicar mudanças de #7 somente com regressão específica |
| Executor de auditoria | `scripts/audit_digital_infrastructure.py` | reestrutura para `legacy/preview/ledger` | herda #5 | reconstruir sobre a `main`; não aceitar versão integral de #5 |
| Adaptador | `statetech/digital_infrastructure_adapter.py` | cria `digital_infrastructure/digital_infrastructure_adapter.py` v1.1.0 | herda exatamente o blob de #5 | namespace novo deve portar invariantes do #8 antes de migrar consumidores |
| Revisão humana | `statetech/digital_infrastructure_review.py` e latest-ledger views | `digital_infrastructure/curatorial_review.py` + pipeline longitudinal | herda #5 | manter append-only e latest-version semantics como contrato |
| Service/ledger | modifica `statetech/service.py` | renomeia/expande para `digital_infrastructure` | herda #5 | migrar com shim; sem troca big-bang |
| Materialização | views `curated/publishable` do ledger | `CuratorialMaterializer` relacional | herda #5 | materializador só recebe decisões humanas válidas e última versão do ledger |
| CI | altera `quality.yml` e adiciona Porta 2 gate | workflows próprios | altera fortemente `quality.yml` | compor gates; nunca substituir gate do #8 pelo workflow de #7 |
| Schemas | contrato da Porta 2 no namespace atual | migra schema registry para `digital_infrastructure` | estende registry para experimentos | migração versionada; compatibilidade temporária e testes de registry |
| Baseline oficial | não autoriza baseline novo | prepara publicação/analytics | materializa T2 e T2A | baseline só após núcleo reconciliado; IA permanece fora das dependências oficiais |
| Artefatos experimentais | não aplicável | infraestrutura para histórico | grande volume de freezes, filas e avaliações | importar por último, depois do código validador, com commit/hash/protocolo verificados |

## Sobreposição direta de arquivos

Entre #8 e #5 há conflito direto confirmado em `scripts/audit_digital_infrastructure.py`; há ainda conflitos semânticos em adapter/service/ledger devido à mudança de namespace de #5.

Entre #8 e a camada adicional de #7 há conflito direto confirmado em:

- `.github/workflows/quality.yml`;
- `src/memoria_audiovisual/digital_infrastructure_audit.py`.

A camada #7 também depende do adaptador antigo de #5, portanto possui conflito semântico herdado mesmo quando o arquivo não aparece no diff #7→#5.

## Classificação dos componentes antigos

### Portar cedo

- contratos, IDs, evidence/provenance, ledger e service de #5;
- ingestão e cobertura de #5, após o namespace canônico passar os testes do #8.

### Portar depois do núcleo

- materialização relacional;
- preflight/postflight;
- publicação/versionamento;
- analytics.

### Portar somente após baseline reconciliada

- `scientific_infrastructure` de #7;
- i18n/UI;
- materialização do baseline operacional.

### Portar por último

- runtime e experimentos T2A/IA;
- freezes, review queues, avaliações e raw artifacts;
- workflows experimentais específicos.

## Regra para resolução manual

Em arquivos/áreas marcados como conflito direto ou semântico, a revisão deve comparar comportamento e contrato. É proibido resolver escolhendo apenas a versão de #5/#7 ou apenas a de #8 sem teste de regressão que demonstre a preservação das invariantes.
