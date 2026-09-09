# Plano técnico por fases — estado consolidado

## Finalidade

Este documento preserva a sequência de dependências usada para construir a infraestrutura digital e registra o estado atual de cada fase. O backlog vigente está em [`implementation_backlog.md`](implementation_backlog.md); o roadmap científico e público está em [`../research/09_roadmap.md`](../research/09_roadmap.md).

Os estados usados aqui são:

- **implementada estruturalmente:** código, contratos e testes controlados existem;
- **em validação operacional:** depende de execução e inspeção sobre corpora reais;
- **parcialmente implementada:** parte do contrato existe, mas faltam componentes declarados;
- **planejada:** ainda não integra a linha operacional ativa.

## Princípios permanentes

- contratos e persistência precedem publicação;
- coleta, transformação, validação, snapshot, indicador e publicação permanecem separados;
- detecção automática não equivale a fato institucional verificado;
- dados ausentes, erros e estados não avaliáveis não são convertidos silenciosamente em zero ou ausência;
- versões históricas e decisões curatoriais devem permanecer rastreáveis.

## Fase 0 — consolidação estrutural

**Estado: implementada estruturalmente.**

Inclui schemas, identificadores estáveis, registro de versões, mapa de dependências e critérios de aceite. Alterações incompatíveis continuam sujeitas a versionamento e migração documentada.

## Fase 1 — núcleo de dados e proveniência

**Estado: implementada estruturalmente.**

Inclui entidades, evidências, proveniência, ledger append-only, integridade relacional, decisões curatoriais e recuperação controlada. A implementação não equivale a validação de todas as fontes reais.

## Fase 2 — ingestão e adaptação da auditoria

**Estado: implementada estruturalmente; em validação operacional.**

Inclui adaptador da auditoria, modos de pré-visualização e commit, artefatos brutos, cobertura por parâmetro, filas de revisão e integração com o núcleo persistente. Permanecem necessárias inspeção manual e medição de falsos positivos e falsos negativos.

## Fase 3 — validação, qualidade e aptidão

**Estado: implementada estruturalmente; em validação operacional.**

Inclui regras de integridade, qualidade, maturidade, aptidão para uso, preflight, postflight e trilha de auditoria. As classificações ainda precisam ser confrontadas com amostras heterogêneas de instituições reais.

## Fase 4 — memória e comparação longitudinal

**Estado: implementada estruturalmente; primeiro ciclo longitudinal oficial pendente.**

Inclui snapshots, manifestos, comparação temporal, triagem de eventos, revisão humana e migração de schemas. A comprovação operacional exige ao menos dois snapshots controlados e persistência histórica verificada.

## Fase 5 — indicadores

**Estado: parcialmente implementada; validação empírica pendente.**

O registro computável, o motor analítico, os resultados versionados, a cobertura e a análise de sensibilidade estão implementados para os indicadores ativos. Novas famílias, especialmente evidências públicas de IA, fornecedores, contratos, fluxos e riscos, permanecem propostas até receberem metodologia executável, cobertura e validação.

Fontes ativas:

```text
data/templates/analytics/indicator_registry.json
data/templates/analytics/methodology_registry.json
src/memoria_audiovisual/analytics/
```

## Fase 6 — publicação e acesso

**Estado: parcialmente implementada.**

Existem visão pública derivada, revisão editorial, registro da publicação ativa, projeções e produtos versionados. Permanecem pendentes a API pública somente leitura, páginas relacionais completas, catálogo público estável de downloads e a definição da vitrine independente do observatório analítico.

## Fase 7 — expansão analítica

**Estado: exploratória.**

Fornecedores, contratos, fluxos de dados, IA, automação, dependências e riscos possuem modelos e protocolos documentais, mas não devem ser apresentados como indicadores operacionais consolidados sem evidência, metodologia computável e validação.

## Próximo portão técnico

A próxima decisão não depende de criar uma nova fase estrutural. Depende de concluir:

1. auditoria editorial e documental;
2. validação controlada dos detectores;
3. verificação dos denominadores e indicadores ativos;
4. execução longitudinal de dois snapshots;
5. consolidação das branches e baseline estável;
6. decisão arquitetural da vitrine pública.
