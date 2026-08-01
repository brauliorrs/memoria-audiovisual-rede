# Fase 2 — adaptação da auditoria e ingestão

## Objetivo

Conectar a auditoria heurística de infraestrutura digital ao núcleo de dados e proveniência da Fase 1, sem publicar resultados automaticamente.

## Fluxo implementado

```text
CORPORA existente
→ revisão periódica das superfícies públicas
→ DigitalInfrastructureAuditAdapter
→ observação explícita para cada parâmetro esperado
→ matriz de cobertura por corpus e snapshot
→ preview ou commit controlado
→ ledger e revisão curatorial
→ comparação longitudinal
→ materialização relacional controlada
```

## Cobertura dos corpora existentes

A auditoria continua partindo do registro `CORPORA`; não cria um corpus paralelo. Cada nova execução aplica os detectores atuais também aos corpora incorporados antes da ampliação Estado–tecnologia.

Os sete grupos obrigatórios são:

```text
technology
api_service
metadata_format
interoperability
search
restriction
ai_evidence
```

O adaptador produz ao menos uma observação para cada grupo e snapshot. Assim, ausência de linha deixa de ser confundida com ausência do parâmetro.

Estados possíveis:

```text
detected       → valor encontrado
not_detected   → detector executado, sem sinal positivo
not_assessable → superfície ou evidência insuficiente
error           → falha de coleta ou processamento
missing_observation → lacuna estrutural de execução antiga ou incompleta
```

Para fontes inacessíveis, todos os grupos são registrados como `unknown` com revisão `not_assessable`. Para fontes alcançáveis sem sinal, o grupo recebe `not_detected`.

## Matriz de cobertura e comparação longitudinal

O módulo `parameter_coverage.py` gera uma linha por corpus, snapshot e grupo. Ele permite identificar:

```text
baseline_created
unchanged
appeared
disappeared
changed
not_assessable
error
still_missing
```

Dessa forma, o mesmo ciclo periódico usado para acompanhar apagamento, desaparecimento e alteração do acervo também pode completar os parâmetros ausentes dos corpora antigos e comparar a infraestrutura digital entre snapshots.

A primeira execução com os detectores ampliados cria a linha de base. As execuções seguintes distinguem adoção, desaparecimento e mudança de tecnologias, APIs, formatos, interoperabilidade, busca, restrições e sinais de IA.

## Revisão e materialização

O script `scripts/review_statetech_observations.py` exporta filas em CSV/JSON e importa decisões para o ledger append-only. Observações sensíveis exigem duas confirmações independentes.

Somente detecções positivas confirmadas, com quórum suficiente, instituição resolvida e evidência existente, podem ser encaminhadas ao `CuratorialMaterializer`. Registros `not_detected`, `unknown` ou `not_assessable` permanecem como memória metodológica e nunca geram entidades tecnológicas.

## Preparação histórica

O `HistoricalMigrationAnalyzer` permanece disponível apenas para CSV/JSON anteriores que se queira incorporar como observações retrospectivas. Ele não é necessário para que os corpora existentes recebam os novos parâmetros: isso ocorre naturalmente na próxima revisão periódica.

## Arquivos principais

```text
scripts/audit_digital_infrastructure.py
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
src/memoria_audiovisual/statetech/parameter_coverage.py
src/memoria_audiovisual/statetech/curatorial_review.py
src/memoria_audiovisual/statetech/materialization.py
src/memoria_audiovisual/statetech/historical_migration.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_parameter_coverage.py
```

## Garantias metodológicas

1. O corpus existente continua sendo a unidade de origem.
2. Todos os grupos de parâmetros recebem estado explícito em cada nova revisão.
3. Não detecção não é confundida com detector não executado.
4. A primeira rodada ampliada cria a linha de base dos corpora antigos.
5. Rodadas seguintes podem indicar aparecimento, desaparecimento ou mudança.
6. Nenhuma detecção é confirmada automaticamente.
7. Somente detecções positivas confirmadas podem ser materializadas.
8. Migração histórica permanece opcional e separada da revisão normal do corpus.

## Limites atuais

- nenhuma coleta, teste ou comparação empírica foi executada durante o desenvolvimento;
- o agendamento periódico existente ainda precisa chamar o modo `ledger` com `snapshot_id` explícito;
- a matriz está implementada como componente, mas ainda não é exportada automaticamente pelo executor;
- não existe interface gráfica;
- artefatos e manifestos permanecem locais.

## Próximo incremento

Integrar a matriz de cobertura ao resultado do executor e ao ciclo periódico, salvando por snapshot o relatório de completude e, quando houver snapshot anterior, o relatório de mudanças Estado–tecnologia junto aos demais indicadores de memória.
