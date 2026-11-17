# MAR — controle de ativação de coleta na integração de catálogo

Antes de mesclar o PR #95 em `main`, a auditoria dos workflows identificou que `.github/workflows/pipeline.yml` tinha `push: main` e executava `scripts/run_pipeline.py`, que inclui coletores institucionais. Isso conflita com o HOLD do Archives Portal Europe e com a política de não iniciar coletas amplas por mudanças no catálogo.

**Correção:** retirar exclusivamente o gatilho `push: main` do pipeline de coleta; preservar `workflow_dispatch` com campo `confirm_collection` obrigatório e condicional do job que exige o texto literal `RUN_AUTHORIZED`. Qualquer execução manual continua sujeita às autorizações de fonte e ao escopo documentado; o texto não substitui a auditoria. O workflow `quality.yml` continua obrigatório para PR e push em `main`.

**Impacto:** merges de código no catálogo não iniciam coletor nem baixam mídia; nenhuma rotina de backup/Neon nem `organism-monthly.yml` foi alterada. O job mensal continua um risco operacional separado a ser gerenciado por suas próprias regras de escopo. O PR #93/P0 não é liberado.

**Testes:** `tests/test_pipeline_activation_gate.py` garante a ausência de gatilhos automáticos no pipeline, confirmação manual e preservação do CI. Retrocesso: reverter somente esta alteração de workflow em PR revisado, nunca reativar implicitamente sem autorização.
