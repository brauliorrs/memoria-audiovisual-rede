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
→ commit controlado no ledger
→ comparação longitudinal
→ fila de revisão curatorial
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
detected            → valor encontrado
not_detected         → detector executado, sem sinal positivo
not_assessable       → superfície ou evidência insuficiente
error                → falha de coleta ou processamento
missing_observation  → lacuna estrutural de execução antiga ou incompleta
```

Para fontes inacessíveis, todos os grupos são registrados como `unknown` com revisão `not_assessable`. Para fontes alcançáveis sem sinal, o grupo recebe `not_detected`.

## Matriz de cobertura e comparação longitudinal

O módulo `parameter_coverage.py` gera uma linha por corpus, snapshot e grupo. O módulo `coverage_reports.py` persiste a cobertura por snapshot e compara a rodada atual com a anterior.

```text
data/statetech/coverage/
├── snapshot_coverage_index.jsonl
└── <snapshot_id>/
    ├── parameter_coverage.json
    ├── parameter_changes.json
    └── execution_summary.json
```

A primeira execução ampliada cria a linha de base. As execuções seguintes podem registrar:

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

Dessa forma, o mesmo ciclo periódico usado para acompanhar apagamento, desaparecimento e alteração do acervo também completa os parâmetros ausentes dos corpora antigos e compara a infraestrutura digital entre snapshots.

## Workflow periódico

O arquivo `.github/workflows/statetech-periodic-review.yml` conecta o executor ao GitHub Actions.

A execução está configurada para:

- rodar mensalmente no primeiro dia do mês, às 03:17 UTC;
- permitir execução manual com `workflow_dispatch`;
- gerar automaticamente um `snapshot_id` UTC quando ele não for informado;
- impedir duas rodadas concorrentes;
- restaurar o diretório `data/statetech` da rodada anterior;
- executar o auditor em modo `ledger`;
- verificar a presença dos produtos obrigatórios;
- salvar o estado atualizado para a rodada seguinte;
- publicar os relatórios do snapshot como artefato por 90 dias.

A memória entre runners efêmeros é preservada por cache versionado por execução, com restauração pela chave comum `statetech-state-`. O cache não é tratado como produto público: os relatórios de cada rodada também são publicados como artefatos independentes.

O operador pode limitar uma execução manual a corpora específicos ou fornecer um identificador próprio de snapshot. O identificador é validado antes da coleta e os relatórios de um snapshot já existente não podem ser sobrescritos.

## Ordem segura da rodada

```text
checkout
→ instalação de dependências
→ restauração da memória anterior
→ geração e validação do snapshot_id
→ auditoria dos corpora ativos
→ ledger e manifestos
→ cobertura e comparação longitudinal
→ verificação dos produtos
→ salvamento do estado
→ publicação do artefato
```

O estado só é salvo para a próxima rodada quando a execução termina com sucesso. A publicação do artefato usa `if: always()` para preservar relatórios diagnósticos quando eles existirem, inclusive em uma rodada parcialmente malsucedida.

## Revisão e materialização

O script `scripts/review_statetech_observations.py` exporta filas em CSV/JSON e importa decisões para o ledger append-only. Observações sensíveis exigem duas confirmações independentes.

Somente detecções positivas confirmadas, com quórum suficiente, instituição resolvida e evidência existente, podem ser encaminhadas ao `CuratorialMaterializer`. Registros `not_detected`, `unknown` ou `not_assessable` permanecem como memória metodológica e nunca geram entidades tecnológicas.

## Preparação histórica

O `HistoricalMigrationAnalyzer` permanece disponível apenas para CSV/JSON anteriores que se queira incorporar como observações retrospectivas. Ele não é necessário para que os corpora existentes recebam os novos parâmetros: isso ocorre naturalmente na próxima revisão periódica.

## Arquivos principais

```text
.github/workflows/statetech-periodic-review.yml
scripts/audit_digital_infrastructure.py
src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py
src/memoria_audiovisual/statetech/parameter_coverage.py
src/memoria_audiovisual/statetech/coverage_reports.py
src/memoria_audiovisual/statetech/curatorial_review.py
src/memoria_audiovisual/statetech/materialization.py
src/memoria_audiovisual/statetech/historical_migration.py
tests/test_statetech_digital_infrastructure_adapter.py
tests/test_statetech_parameter_coverage.py
tests/test_statetech_coverage_reports.py
```

## Garantias metodológicas

1. O corpus existente continua sendo a unidade de origem.
2. Todos os grupos de parâmetros recebem estado explícito em cada nova revisão.
3. Não detecção não é confundida com detector não executado.
4. A primeira rodada ampliada cria a linha de base dos corpora antigos.
5. Rodadas seguintes podem indicar aparecimento, desaparecimento ou mudança.
6. Relatórios históricos de snapshots não são sobrescritos.
7. O estado longitudinal é restaurado antes da nova coleta.
8. Nenhuma detecção é confirmada automaticamente.
9. Somente detecções positivas confirmadas podem ser materializadas.
10. Migração histórica permanece opcional e separada da revisão normal do corpus.

## Limites atuais

- nenhuma coleta, teste, workflow ou comparação empírica foi executada durante o desenvolvimento;
- o cache do GitHub Actions é infraestrutura operacional e não substitui uma política futura de armazenamento durável externo;
- artefatos do workflow têm retenção configurada em 90 dias;
- a seleção do snapshot anterior segue a ordem append-only do índice, sem inferir cronologia pelo texto do identificador;
- ainda não existe interface gráfica.

## Próximo incremento

Adicionar um validador pré-execução do ciclo periódico, capaz de verificar contratos, caminhos, identificadores, disponibilidade da memória anterior e consistência do índice de snapshots antes de permitir a coleta.
