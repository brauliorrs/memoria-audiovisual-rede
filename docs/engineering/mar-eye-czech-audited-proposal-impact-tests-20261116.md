# MAR — pacote de proposta documental Eye/Czech → admissão PR #95

## Auditoria pré-implementação (16/11/2026)

**Dependências:** PR #96 fornece `reconcile_eye`, `screen_czech_episode` e `preview` com evidência JSON local fixada por SHA-256. PR #95 define a porta de publicação `mar_admitted/<corpus>.csv + .manifest.json`, 12 campos CSV e regras de direitos. PRs #95 e #96 permanecem drafts; este PR é empilhado sobre #96, sem incorporar main ou ativar backup.

**Constatação:** os probes históricos não fornecem nesta tarefa novos JSONs com hashes e logs auditados. Logo, o único resultado legítimo da execução sem evidências é HOLD. O gerador deve funcionar *somente* sobre evidências reais, nunca inventar fichas.

**Contrato de saída:** gerar no diretório fornecido explicitamente pelo operador, inicialmente vazio e fora de `data/output/`, dois arquivos: `<corpus>.candidate.csv` (12 campos exatos do contrato PR95, porém `record_review_status=pending_independent_review`) e `<corpus>.proposal.json` (estado HOLD, rastreio de evidência SHA, fingerprint e classificação dos deltas). Nunca criar `data/output/mar_admitted`, nem `approved_for_publication=true` ou `approved_metadata_only`. Toda proposta deve depender do resultado do PR96 **recalculado** do JSON original e da baseline histórica Eye, de forma que autorrelatórios não passem por validação.

**Fichas Eye:** somente novas fichas, classificadas `new` por URL, são candidatas à admissão. Alterações `changed` de registros legados não devem entrar como duplicatas no PR95; exigir fluxo de atualização curatorial separado. `unchanged` e `not_observed` não entram. Identidade `record_id` e campos validados pela reconciliação. Limite máximo: 100 por lote de evidência, sem download de mídia.

**Czech:** somente o episódio validado como `candidate_for_review` produz linha candidata. Não afirmar playback atual, direitos nem custódia. Uma página vazia gera HOLD sem CSV publicável.

**Gate humano e jurídico:** a futura promoção para `mar_admitted` exige revisão manual independente, autenticação de evidências de origem, confirmação de URL, campo `source_run_url` real auditável, novo manifesto de aprovação SHA-256 sobre os bytes aprovados e aprovação de PR. Não fornecer botão para promover automaticamente. Um SHA informado pela mesma pessoa que produziu JSON indica integridade do arquivo, não independência da validação da fonte.

**Testes previstos:** P1 Eye novos vs alterados, duplicação e exclusão; P2 Czech candidato vs HOLD; P3 bytes/ordem determinísticos; P4 rejeitar SHA incorreto; P5 impedir saída dentro de `data/output` ou sobrescrita; P6 CSV pendente não aceito pela porta #95; P7 nunca gerar `approved_for_publication`, `source_run_url` inventado ou URLs de mídia; P8 CI geral verde, não alterar fluxos existentes.

**Rollback:** excluir gerador e testes; nenhum dataset atual, secret, job ou configuração do banco é alterado.
