# KAVI #82 — continuação supervisionada pelo servidor com `expires` sem fuso

**Data:** 13/10/2026. **Estado:** proposta de gate limitado, sem sonda viva automática.  
Dependências: PRs #64, #66, #67, #68 já integrados; PR #65 (Draft e baseado em código anterior), issue #59 aberta.

## Problema e fonte do contrato

No ensaio vivo de três invocações do PR #65, a continuação foi bloqueada com `resume_cursor_expiration_timezone_missing`. Isso demonstra um timestamp sem indicação de fuso na API e a rejeição do nosso cliente, **não** expiração do token. O código do controlador oficial da Finna (`NatLibFi/NDL-VuFind2`, branch `dev`) usa `getExpiry()->format(VUFIND_DATABASE_DATETIME_FORMAT)`. A instância pública ainda não tem fuso autoritativo documentado.

A auditoria da implementação oficial identificou também a assinatura combinada **HTTP 400**, JSON `status=ERROR`, `statusMessage="Invalid or expired token"` em uma solicitação de continuação. A implementação da API não discrimina token **inválido** de token **expirado**. Ver `docs/engineering/kavi-082-upstream-token-error-contract.md`.

## Política aprovada para ensaio restrito

`execute_verified_batch(..., allow_naive_server_validation=True)` autoriza **somente quando `max_pages=1`** que uma data ISO-8601 sem offset permita o envio do token opaco para validação do **servidor**, após:

1. Auditoria offline de checkpoint parcial, hashes brutos, sequência, IDs, escopo institucional e direitos conservadores.
2. Contagem independente do preflight registrada fora do checkpoint, novamente conferida no `stage_metadata`.
3. Verificação do cursor exato da última resposta bruta SHA-256, sob `FileWriteLock`, imediatamente antes do `fetch_page` real, após throttling.
4. Controle do origin/robots por `Guard`, sem bypass de limite de resposta ou tentativa adicional automática.

O parser local **não presume UTC nem Europe/Helsinki** como timezone oficial. A forma da data ainda precisa ser válida; campos `expires` ausentes, datas malformadas, hash alterado, cursor divergente e **datas com fuso explícito já vencidas** continuam em HOLD. A aprovação por retorno HTTP/JSON adequado autoriza **somente persistir e auditar a próxima página**. Não confirma que todo o índice é estável.

Em erro HTTP 400 com a assinatura oficial, `finna_token_invalid_or_expired_unresolved` causa **HOLD** e conserva a tentativa anterior como checkpoint parcial; não gera novo epoch, não repete a mesma requisição dentro do executor e não altera qualquer registro bruto. Falhas HTTP 429/5xx, transporte, JSON ou total divergente são julgadas separadamente; nenhum erro permite restart por suposição.

**Não existe autorização de reinício automático:** o PR #66 limita novo epoch a uma ocorrência e requer prova externa de expiração e autorização humana. A assinatura combinada do PR #68 **não** atende a esse requisito.

## Escopo concreto de teste

O script `scripts/probe_kavi_finna_three_batch_resume.py` reutiliza o mesmo coletor e realiza até **três invocações independentes**, cada uma limitada a **uma página**, num **diretório local persistente, novo e explicitamente fornecido** pelo operador quando usar `--execute`:

- 1ª: novo índice/cursor oficial, sem token enviado na retomada.
- 2ª: uma continuação por token, com auditoria anterior e posterior.
- 3ª: uma nova continuação, usando o novo token e novo preflight.

**Não há execução automática viva no CI.** Sem `--execute`, o script realiza apenas dry-run. Com `--execute`, exige também `--directory data/staging/<diretorio_novo_para_o_ensaio>` e recusa reutilizar qualquer diretório existente. Esse diretório **não é apagado** após sucesso ou falha, permitindo revisão forense do checkpoint parcial e de seus hashes. Não é gerado arquivo do corpus principal. Os testes de unidade usam diretórios sintéticos descartáveis e não fazem requests reais. A sonda viva deverá ser explicitamente limitada e executada apenas depois de CI, revisão Codex e aprovação do protocolo; não entrar no cron ou em gatilho de toda PR.

## Evidência negativa exigida

- Opt-in não pode liberar lotes de 2 a 25 páginas, nem contornar `expected_total` externo.
- É proibido continuar quando `expires` tiver offset explícito vencido ou formato inválido.
- Rejeição oficial ambígua é **HOLD** sem retry nem promoção; checkpoint fica parcial e auditável.
- Mesmo com timestamp sem fuso, a permissão de cada cursor é verificada sob lock. Ausência do cursor, repetição ou divergência abortam.
- Saída pública contém apenas números e hashes agregados; jamais URLs, tokens, IDs individuais ou raw JSON.
- Flags `promotion_authorized=false`, `media_downloaded=false` permanecem invariantes.

## Decisão de produção

O runner normal `scripts/run_kavi_finna_metadata_staging.py` conserva o padrão **fail-closed**, sem habilitar opt-in implicitamente. Só a sonda delimitada demonstra o novo caminho. A comparação UTC vs Europe/Helsinki é ferramenta offline auxiliar, não diagnóstico comprovado do relógio da API e não cria duas requisições.

Este PR não resolve nem dispensa a política de snapshot mutável e de particionamento para grandes índices. **Issue #59 e análise #82 continuam abertas; análise #83 bloqueada** até adjudicação de completude, custódia e direitos. Não baixar mídia nem promover ao MAR.
