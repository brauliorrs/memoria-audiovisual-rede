# Modelo de memória e evolução temporal

## Objetivo

A plataforma deve preservar não apenas o estado atual de instituições, tecnologias, fornecedores, contratos, fluxos de dados, sistemas de IA e riscos, mas também a história de suas mudanças ao longo do tempo.

O modelo temporal adota três camadas complementares:

1. **snapshot**: estado observado de uma entidade em uma data;
2. **evento**: mudança identificada entre estados ou documentada por fonte externa;
3. **versão curatorial**: interpretação validada que explica o significado da mudança.

## Princípio central

Nenhum estado anterior é sobrescrito. Correções, reclassificações e mudanças empíricas devem gerar novos registros vinculados ao registro anterior.

## Tipos de tempo

- `observed_at`: quando a plataforma observou a evidência;
- `valid_from`: quando o estado passou a valer, quando conhecido;
- `valid_to`: quando deixou de valer, quando conhecido;
- `recorded_at`: quando o registro foi incorporado à plataforma;
- `reviewed_at`: quando houve validação humana;
- `source_published_at`: data de publicação da fonte, quando disponível.

Essas datas não são equivalentes e não devem ser fundidas.

## Entidades temporalizadas

Todas as entidades da camada Estado–tecnologia podem evoluir:

- instituição;
- tecnologia;
- relação instituição–tecnologia;
- fornecedor;
- contrato;
- fluxo de dados;
- sistema de IA;
- evidência;
- avaliação de risco;
- classificação institucional;
- disponibilidade de API, padrão ou mecanismo de interoperabilidade.

## Eventos controlados

- `created`;
- `first_observed`;
- `updated`;
- `reclassified`;
- `activated`;
- `deactivated`;
- `suspended`;
- `resumed`;
- `provider_changed`;
- `technology_changed`;
- `contract_awarded`;
- `contract_extended`;
- `contract_ended`;
- `access_restricted`;
- `access_opened`;
- `api_added`;
- `api_removed`;
- `interoperability_added`;
- `interoperability_removed`;
- `ai_announced`;
- `ai_piloted`;
- `ai_operationalised`;
- `ai_discontinued`;
- `risk_increased`;
- `risk_reduced`;
- `evidence_corrected`;
- `record_merged`;
- `record_split`;
- `possible_digital_extinction`;
- `digital_reappearance`.

## Identidade e versionamento

Cada entidade mantém um identificador estável, por exemplo `institution_id`. Cada estado temporal recebe:

- `version_id` único;
- `entity_id` estável;
- `version_number` crescente;
- `previous_version_id`, quando houver;
- `change_reason`;
- `change_type`;
- `superseded`;
- `validation_status`.

## Snapshots

Os snapshots devem ser imutáveis e identificados por:

- `snapshot_id`;
- `snapshot_date`;
- `scope`;
- `schema_version`;
- `data_contract_version`;
- `source_commit_sha`, quando aplicável;
- contagem de entidades e relações;
- status de validação;
- nota metodológica.

## Comparação longitudinal

A comparação entre snapshots poderá produzir:

- novas tecnologias detectadas;
- tecnologias desaparecidas;
- mudanças de fornecedor;
- início e término de contratos;
- alterações de API e interoperabilidade;
- mudanças no regime de acesso;
- transformação de fluxos de dados;
- adoção, expansão ou interrupção de IA;
- aumento ou redução de dependências e riscos;
- desaparecimento e reaparecimento de superfícies digitais.

## Correção histórica

Uma correção de erro não deve ser apresentada como mudança empírica. O campo `change_origin` distingue:

- `empirical_change`;
- `source_update`;
- `curatorial_correction`;
- `schema_migration`;
- `entity_resolution`.

## Publicação

Linhas do tempo públicas devem utilizar apenas versões `confirmed` ou `probable` com evidência suficiente. Registros `pending_review`, `inconclusive` ou `false_positive` permanecem na memória interna, mas não alimentam indicadores públicos.

## Produtos previstos

```text
data/history/
├── snapshots/
├── events/
├── entity_versions/
└── migrations/

data/output/
├── statetech_timeline.csv
├── statetech_entity_history.json
├── statetech_snapshot_manifest.json
└── statetech_change_summary.csv
```

Este documento define apenas a arquitetura temporal. Nenhuma coleta ou comparação foi executada.