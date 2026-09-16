# Porta 2 — integração contratual da auditoria de infraestrutura

## Finalidade

A Porta 2 decide se a auditoria heurística pode deixar a etapa exclusivamente estrutural e seguir para uma **execução piloto controlada**, sem ainda autorizar baseline oficial nem publicação de novos indicadores científicos.

A aprovação exige que a automação seja incapaz de transformar, por si só, uma detecção em afirmação científica.

## Critérios de passagem

| Critério | Evidência esperada | Estado candidato |
|---|---|---|
| Contrato | Cada detecção satisfaz `schemas/digital_infrastructure_audit.schema.json` | implementado |
| Separação analítica | observação, detecção e revisão não são confundidas | implementado |
| Revisão inicial | toda coleta automática inicia em `pending_review` | implementado |
| Evidência | cada detecção possui evidência identificável e proveniência | implementado |
| Integridade | IDs de evidência são únicos por detecção | implementado |
| Longitudinalidade | ledger append-only preserva versões e snapshots | implementado |
| Revisão humana | decisão cria nova versão e preserva a versão automática | implementado |
| Bruto × curado | saídas automatizadas e revisadas são distintas | implementado |
| Publicação | somente `confirmed` e `probable` podem entrar na superfície publicável | implementado |
| Não detecção | superfície indisponível gera `unknown`, não ausência tecnológica | implementado |
| CI | testes impedem promoção automática e verificam contrato | implementado; sujeito ao resultado dos checks |
| Interface | Streamlit não dispara coleta e novos indicadores permanecem bloqueados antes da curadoria | mantido |

## Artefatos da rodada

O executor mantém os arquivos legados por compatibilidade e produz:

```text
data/output/digital_infrastructure_audit_raw.csv
data/output/digital_infrastructure_audit_raw.json
data/output/digital_infrastructure_audit_curated.csv
data/output/digital_infrastructure_audit_curated.json
data/output/digital_infrastructure_audit_publishable.csv
data/output/digital_infrastructure_audit_publishable.json
data/output/digital_infrastructure_audit_ledger.jsonl
```

A camada `raw` contém a observação automática. A camada `curated` só recebe decisões humanas concluídas e exclui `false_positive`. A camada `publishable` aceita apenas `confirmed` e `probable`.

## Regra de longitudinalidade

O ledger nunca substitui a observação anterior. Uma revisão humana referencia a versão automática por `previous_version_id` e cria nova proveniência. Snapshots distintos permanecem simultaneamente disponíveis para comparação futura.

A persistência longitudinal exige conservar/versionar o ledger entre rodadas oficiais. Artefatos temporários de CI servem para validação técnica, não substituem o registro longitudinal do baseline.

## Barreira de segurança científica

A execução automatizada deve falhar se:

1. produzir registro bruto com `review_status` diferente de `pending_review`;
2. produzir registros curados ou publicáveis sem revisão humana;
3. não conseguir validar um registro contra o contrato estrutural;
4. não gerar ledger e evidências auditáveis.

## O que a aprovação autoriza

A aprovação da Porta 2 autoriza somente:

- execução piloto em amostra diversa;
- inspeção dos falsos positivos e falsos negativos;
- revisão humana seguindo `VALIDATION_PROTOCOL.md`;
- cálculo de precisão, revocação e F1 quando houver referência humana suficiente;
- ajuste dos detectores antes do baseline.

A aprovação **não autoriza**:

- tratar o piloto como baseline oficial;
- executar automaticamente o ciclo integral como resultado científico;
- publicar sinais `pending_review` no painel;
- converter `not_detected` em ausência de tecnologia;
- ativar indicadores de IA sem validação humana.

## Decisão

O estado deste documento é **candidato à aprovação** enquanto os checks da branch/PR não forem concluídos. Com os testes da Porta 2 e os checks gerais verdes, a Porta 2 pode ser marcada como **APROVADA PARA PILOTO CONTROLADO**. O baseline T2 continua dependendo da validação humana posterior do piloto.
