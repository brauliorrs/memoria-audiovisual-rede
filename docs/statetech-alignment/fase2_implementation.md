# Fase 2 — adaptação da auditoria e ingestão

## Objetivo

Conectar a auditoria heurística de infraestrutura digital ao núcleo de dados e proveniência da Fase 1, sem publicar resultados automaticamente.

## Fluxo implementado

```text
InfrastructureAudit
→ DigitalInfrastructureAuditAdapter
→ observações normalizadas por sinal
→ IngestionCoordinator
→ preview ou commit controlado
→ artefato bruto e manifesto
→ ledger
→ fila de revisão CSV/JSON
→ decisões humanas append-only
→ dupla revisão quando sensível
→ materialização relacional controlada
```

## Interface operacional de revisão

O script `scripts/review_statetech_observations.py` exporta a fila em CSV/JSON e importa decisões validadas para o ledger append-only. Observações sensíveis exigem duas confirmações de revisores distintos; conflitos de interesse podem impedir que uma confirmação conte para o quórum.

## Materialização

Somente observações com detecção positiva, decisão `confirmed`, quórum suficiente, instituição resolvida e evidência existente podem ser encaminhadas ao `CuratorialMaterializer`. Fornecedores não são inferidos pela mera detecção de tecnologia. Restrições continuam fora da materialização até existir contrato de domínio próprio.

## Preparação da migração histórica

O módulo `HistoricalMigrationAnalyzer` e o script `scripts/prepare_statetech_historical_migration.py` analisam CSV ou JSON legados exclusivamente em modo `dry-run`.

```text
arquivo histórico
→ leitura sem persistência
→ normalização mínima
→ verificação de campos obrigatórios
→ detecção de chaves duplicadas
→ contagem de sinais migráveis
→ identificação de campos desconhecidos
→ relatório JSON de compatibilidade
```

Exemplo:

```powershell
python scripts/prepare_statetech_historical_migration.py --input data/output/digital_infrastructure_audit.json --report data/migration/historical_report.json --fail-on-blocked
```

O relatório classifica cada linha como:

```text
compatible
review_required
blocked
```

Códigos iniciais:

- `MIG-001`: campos obrigatórios ausentes;
- `MIG-002`: registro sem sinais tecnológicos migráveis;
- `MIG-003`: chave histórica duplicada;
- `MIG-004`: campo não reconhecido, preservado somente no artefato bruto.

A chave de comparação inicial usa `corpus_code|source_url`. Todas as ocorrências de uma chave duplicada são bloqueadas para impedir seleção silenciosa de uma versão. Campos desconhecidos não são descartados nem promovidos automaticamente.

O dry-run não cria artefatos de ingestão, manifestos, entidades, evidências ou transações no ledger. O único arquivo produzido é o relatório solicitado pelo operador.

## Arquivos principais

```text
scripts/audit_digital_infrastructure.py
scripts/review_statetech_observations.py
scripts/prepare_statetech_historical_migration.py
src/memoria_audiovisual/statetech/curatorial_review.py
src/memoria_audiovisual/statetech/review_files.py
src/memoria_audiovisual/statetech/materialization.py
src/memoria_audiovisual/statetech/historical_migration.py
tests/test_statetech_curatorial_review.py
tests/test_statetech_review_files.py
tests/test_statetech_historical_migration.py
```

## Garantias metodológicas

1. Nenhuma detecção é confirmada automaticamente.
2. Revisões são append-only e possuem cadeia explícita de substituição.
3. Observações sensíveis exigem dois revisores distintos.
4. Somente o estado curatorial vigente e suficiente libera materialização.
5. Fornecedores não são inferidos pela mera detecção de tecnologia.
6. A migração histórica começa obrigatoriamente por dry-run.
7. Duplicidades e campos ausentes bloqueiam a migração automática.
8. Campos desconhecidos são reportados e preservados no arquivo de origem.

## Limites atuais

- nenhuma coleta, migração histórica ou teste foi executado durante o desenvolvimento;
- o analisador não grava no ledger e ainda não gera plano executável de ingestão;
- a equivalência entre colunas históricas de diferentes versões ainda depende de regras explícitas;
- não existe interface gráfica;
- a importação de revisões não oferece rollback global do lote;
- não há assinatura digital das decisões;
- artefatos e manifestos permanecem locais.

## Próximo incremento

Criar um plano de migração versionado a partir de relatórios sem bloqueios, com mapeamento explícito de colunas, snapshot histórico obrigatório, hash do arquivo de origem e comando separado de `apply` protegido por confirmação. O modo `apply` não deverá ser executado durante o desenvolvimento estrutural.
