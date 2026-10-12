# KAVI #82 — decisão HOLD: fuso não especificado em `resumptionToken.expires`

Data: 2026-10-12. Escopo: API REST de busca Finna, instituição/faceta `building:"0/KAVI/"`, formato `0/Video/`. Referências: issue #59, PRs #61–#65.

## Evidência reproduzida

- No Quality Checks #2009 (run `38255001378`), o ensaio vivo de **uma página inicial + duas retomadas** abortou com `resume_cursor_expiration_timezone_missing`, exit code 2. A análise precedente tinha validado duas páginas com um executor sem esse gate de validade.
- O relatório público `kavi-finna-three-batch-redacted-probe` (artifact id `11749581677`) contém somente `status=HOLD`, código da falha e flags negativas. Não expõe token, IDs, páginas brutas ou mídia.
- A documentação oficial da API Finna (<https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish> e <https://www.kiwi.fi/spaces/Finna/pages/51842373/Finnan%2Bavoin%2Brajapinta%2BFinna%2BAPI>) documenta `resumptionToken` e os campos `token` e `expires`, **mas não estabelece o fuso nem o significado de um valor `expires` sem offset**.
- A mesma documentação identifica a Biblioteca Nacional da Finlândia como responsável pela API e o e-mail oficial `finna-posti@helsinki.fi` para consultas.
- **Não usar OAI-PMH como justificativa para supor UTC.** O padrão OAI-PMH possui timestamps UTC em XML, mas este é um endpoint JSON da API REST de busca, com contrato distinto.

## Decisão de engenharia

**HOLD fail-closed, não contornar.** Não anexar UTC nem `Europe/Helsinki` automaticamente a uma string timezone-naive. O parser atual aceita uma data explícita `Z` ou offset (ISO 8601), e rejeita datas sem timezone antes de qualquer busca de continuação.

Enquanto o fuso e a semântica do campo não forem confirmados:
- **Não executar novamente o ensaio vivo automático no CI.** O workflow foi alterado para manter testes sintéticos, mas remover a invocação branch-gated com `--execute` e o upload de artefato vivo.
- Não executar full harvest nem iniciar a análise nº 83; não alterar ou promover o corpus.
- Não tentar inferir fuso somente pela localização física da Finna, timezone do runner, horário HTTP `Date`, protocolo OAI-PMH ou suposições sobre horário de verão.
- Preservar relatórios existentes como evidência de falha segura e evolução do protocolo.

## Solicitação ao mantenedor oficial (antes da correção)

**Destinatário:** `finna-posti@helsinki.fi`.

**Subject:** Finna REST API search — timezone of `resumptionToken.expires`

> Hello Finna API maintainers,
>
> We are testing bounded metadata-only pagination through `https://api.finna.fi/v1/search` with the officially documented `resumptionToken` mechanism. The JSON response includes `resumptionToken.token` and `resumptionToken.expires`. In a live test, the `expires` datetime was provided **without an explicit UTC offset or timezone marker**.
>
> Could you confirm the authoritative timezone/clock semantics of `expires` when no offset is included? Is it always UTC, Europe/Helsinki local time, or dependent on server/session configuration? Could you also point us to the authoritative documentation or implementation and clarify whether the token expiration window and validity across separate requests are guaranteed?
>
> We are intentionally blocking further pagination rather than assuming a timezone. We do not need to share opaque tokens or record identifiers.
>
> Thank you.

**Este documento registra somente a mensagem proposta; não equivale a envio ou confirmação do fornecedor.**

## Critérios para retirar o HOLD

1. Receber documentação/código oficial inequívoco ou resposta do mantenedor que confirme o fuso, inclusive tratamento de horário de verão, formatos e eventual expiração de token.
2. Registrar URL/versão/data da evidência, interpretação aprovada e casos-limite, especialmente horários ambíguos ou inexistentes em transições DST, se aplicáveis.
3. Implementar um parser **fonte-específico** e restrito que rejeite qualquer variante não comprovada; preservar teste de regressão de formatos sem timezone enquanto não forem explicitamente aprovados.
4. Exigir Quality Checks verde, nova revisão e somente depois restaurar uma única sonda viva de três páginas, com mídia e promoção bloqueadas.
5. Tratar eventual deriva de totais entre páginas como HOLD independente, sem editar o checkpoint ou pular IDs.

**Estado:** PR #65 permanece Draft. Issue #59 / análise nº 82 continua aberta. Resultados sob custódia, licenças e incorporação: não verificados.
