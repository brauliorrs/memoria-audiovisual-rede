# KAVI-082 — evidência oficial sobre rejeição de `resumptionToken` (13/10/2026)

## Resultado da auditoria de implementação

**Fonte primária:** repositório oficial `NatLibFi/NDL-VuFind2`, branch `dev`, consultada em 13/10/2026. Os arquivos abaixo são material de implementação oficial, **não atestado de que a instalação pública já foi atualizada para o mesmo commit**.

| Evidência no upstream | Caminho e blob SHA Git |
|---|---|
| `doCursorSearch()`: resultado nulo de `loadResumptionToken()` gera `ApiException(INVALID_OR_EXPIRED_TOKEN, 400)` | [SearchApiController.php](https://github.com/NatLibFi/NDL-VuFind2/blob/dev/module/VuFindApi/src/VuFindApi/Controller/SearchApiController.php), SHA `a76b59b43a1ff29dcd7cabcc375d4e5a7707a240` |
| Mensagem exata `Invalid or expired token` | [ApiException.php](https://github.com/NatLibFi/NDL-VuFind2/blob/dev/module/VuFindApi/src/VuFindApi/Controller/ApiException.php), SHA `e30213b749b8a5a679d9dff208e192b5882475b8` |
| `output` define HTTP 400, corpo JSON com `status=ERROR` e `statusMessage` | [ApiTrait.php](https://github.com/NatLibFi/NDL-VuFind2/blob/dev/module/VuFindApi/src/VuFindApi/Controller/ApiTrait.php), SHA `7d4854cb7c3586a207bbbdbc4497dc7003e4e720`; [ApiInterface.php](https://github.com/NatLibFi/NDL-VuFind2/blob/dev/module/VuFindApi/src/VuFindApi/Controller/ApiInterface.php), SHA `c33cce7a04eb9619808119b45f6425f6f89046d6` |
| `loadResumptionToken`: ausência **ou expiração** devolve nulo; `createResumptionToken(..., $lifetime=86400)`, 24h por padrão | [ResumptionTokenTrait.php](https://github.com/NatLibFi/NDL-VuFind2/blob/dev/module/VuFind/src/VuFind/ResumptionToken/ResumptionTokenTrait.php), SHA `6058b49ac8e5690e5ded0b667d1d593e85a2a1e1` |
| Busca no banco exige `expires > now`; não diferencia token inexistente de expirado no retorno ao cliente | [OaiResumptionService.php](https://github.com/NatLibFi/NDL-VuFind2/blob/dev/module/VuFind/src/VuFind/Db/Service/OaiResumptionService.php), SHA `78c5bd07c366999e2e257b9199b58850d9f4fb54` |

**Conclusão substancial:** a assinatura pública **HTTP 400 + JSON `status: ERROR` + `statusMessage: Invalid or expired token`**, se retornada numa **continuação** por token, comprova **rejeição por token inválido *ou* expirado**, **não expiração inequívoca**. Não existe, neste caminho de código, uma resposta exclusiva para expiração. A validade padrão de 24h não permite concluir o motivo de um erro específico e pode variar com versão/configuração da implantação.

### Sobre `expires` sem timezone

O controlador formata `getExpiry()->format(VUFIND_DATABASE_DATETIME_FORMAT)`, sem offset na string produzida. O arquivo `local/config/finna/config.ini.sample` na branch `dev` contém `timezone = "Europe/Helsinki"`, mas isso é **configuração de exemplo**, não prova do timezone de cada instância ou do relógio de armazenamento. Não assumir Europe/Helsinki/UTC como contrato da API pública. O PR #65 permanece Draft/HOLD pelo gate de data sem fuso.

## Desenvolvimento conectado ao classificador, sem promoção

- `Guard` (compartilhado) mantém comportamento anterior por padrão, mas admite opção `capture_error_400_json=True` **apenas no adaptador Finna**. Captura no máximo **8192 bytes** do corpo de erro, só se HTTP 400 e content-type JSON; continua validando robots e origem, sem redirects não autorizados e sem gravar token, URL ou mensagem em logs.
- `classify_provider_token_response` aceita **somente** a assinatura completa acima e **apenas numa requisição de continuação**. Não faz match por fragmento `expired`, HTTP 400 isolado ou JSON semelhante; recusa MIME impróprio, corpo excessivo, status de sucesso ou erro não exclusivo.
- Rejeições específicas recebem código estável `finna_token_invalid_or_expired_unresolved` e categoria `token_invalid_or_expired_unresolved`, **sempre** `token_expiration_confirmed=false`, `restart_authorized=false`, `media_downloaded=false`, `promotion_authorized=false`.
- `stage_metadata` e `kavi_finna_batch_gate` continuam abortando diante desta rejeição. `restart_after_confirmed_expiry` (PR #66) **não é chamado**, porque requer `provider_confirmed_token_expired`, uma evidência que a resposta conjugada não fornece.

## O que falta para autorizar um reinício

Não confundir `token_invalid_or_expired_unresolved` com `provider_confirmed_token_expired`. Opções futuras **separadas** exigem adjudicação humana de causa provável, evidências externas da validade do token, eventual posição do provedor e política formal de custo/limite de tentativas; mesmo assim, não chamar a hipótese de confirmação oficial. O reinício pode ser submetido a aprovação excepcional com fundamento operacional documentado em protocolo novo, preservando o epoch antigo e o teto de 1 reinício, mas **não é autorizado por este PR**.

## Validação

Testes sintéticos e determinísticos (sem HTTP público) cobrem corpo de erro 400 exato, status incorreto, campo diferente, substring, MIME incompatível, erro JSON malformado, tamanho excessivo, tentativa inicial `resumptionToken=*` e falhas de transporte. Teste de `Guard` garante que, por padrão, ele não captura erro HTTP, e que no modo Finna lê no máximo 8KiB e nunca expõe cursor em mensagem.

**Proibições mantidas:** nenhum endpoint de mídia, nenhuma incorporação automática ao MAR, nenhuma sonda viva do PR #65, nenhuma enumeração total dos ~138 mil registros, nenhuma análise nº 83. Issue #59 / nº 82 aberta.
