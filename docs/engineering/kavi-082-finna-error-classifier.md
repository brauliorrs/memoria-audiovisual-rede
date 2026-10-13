# KAVI #82 — contrato conservador de classificação de falhas da API Finna

**Data:** 2026-10-13. **Escopo:** API REST `/v1/search`, `resumptionToken`, somente metadados.  
**Status:** incremento offline pronto para testes e revisão; NÃO autoriza reinício automático, novas sondas vivas nem promoção ao corpus.

## Evidência externa e limite epistêmico

A [documentação oficial Finna API (English)](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish) descreve iniciar `resumptionToken=*`, continuar com o token retornado e encerrar quando as páginas se esgotarem. Indica a [especificação OpenAPI](https://api.finna.fi/api/v1/?openapi) como referência mais atual. **Na investigação de 13/10/2026 não se obteve desta documentação um status/código de erro REST que identifique inequivocamente o vencimento do token.** A URL OpenAPI não foi acessível no mecanismo de consulta; **não** presumir que foi exaustivamente auditada. Não usar convenções OAI-PMH como evidência sobre o endpoint REST.

O primeiro ensaio vivo do PR #65 encerrou em `resume_cursor_expiration_timezone_missing`: isto identifica uma **rejeição local** do analisador de data sem offset, não uma rejeição do servidor e **não** comprova expiração.

## Classificação efetivamente implementada

`src/memoria_audiovisual/finna_response_classifier.py` classifica evidências estruturais; `kavi_finna_adapter.py` a utiliza antes de aceitar respostas HTTP e status JSON. A saída segura da CLI fornece categoria e código estável, sem echo de mensagens, IDs, URLs ou tokens retornados pelo servidor.

| Observação | Categoria | Interpretação |
|---|---|---|
| HTTP 200 + JSON `status:OK` | Sucesso | Só aceita como resposta válida, sujeita aos demais checks de integridade |
| HTTP 400/404/outros 4xx | `client_error_unverified` | Não assumir token expirado |
| HTTP 403 | `access_denied` | Não tentar contornar |
| HTTP 429 | `rate_limited` | Potencial nova tentativa manual, jamais reinício por expiração |
| HTTP 500–599 | `upstream_failure` | Potencial nova tentativa manual, jamais reinício por expiração |
| HTTP 3xx inesperado | `unexpected_redirect` | Bloqueio e investigação |
| HTTP 200 + JSON `status:ERROR` | `api_rejection_unverified` | Mesmo que `statusMessage` contenha `expired` |
| Falha de rede, JSON inválido ou tipo incorreto | `transport_or_response_unverifiable` | Não assumir expiração |
| Contagem alterada entre preflight, página e checkpoint | `snapshot_drift` | Bloqueio, auditoria e reconciliação |
| Data `expires` sem fuso, inválida ou supostamente vencida no relógio local | `local_expiry_unverified` | Continua sendo uma inferência do cliente |
| Quebra de checksum, escopo, ordem ou IDs | `integrity_failure` | Bloqueio; não reiniciar |
| Resposta/erro desconhecido | `unknown_rejection` | Código público redigido, não expor entrada |

Cada `FailureAssessment` contém `token_expiration_confirmed=false`, `restart_authorized=false`, `promotion_authorized=false` e `media_downloaded=false`. `manual_retry_candidate=true` indica apenas que uma categoria merece avaliação de um operador; **nenhum retry de API é realizado por esse classificador**.

## Integração sem regressão de contrato

- A integração em `FinnaMetadataSource._json` preserva os códigos públicos já usados para HTTP (`finna_http_status_NNN`) e JSON `finna_api_status_invalid`; agora passam pelo classificador, com taxonomia auditável.
- A CLI `run_kavi_finna_metadata_staging.py` inclui campos públicos da classificação para rejeições, nunca envia `str(exception)` diretamente se o código não for reconhecido.
- O `stage_metadata` continua aplicando segurança de escopo, robots, replay, bloqueio cooperativo e checks de total.
- O PR #66 já integrou o armazenamento por epochs; **este classificador não chama** `restart_after_confirmed_expiry`, nem cria diretórios ou altera seus marcadores.
- O PR #65 segue Draft/HOLD até evidência oficial do timezone e uma política explícita para continuação (não deduzir UTC nem `Europe/Helsinki` como fuso autoritativo).

- Respostas sem status HTTP e com erro de transporte do Guard são classificadas **antes** de HTTP desconhecido; o texto da exceção é redigido para evitar vazamento de token. Com um status HTTP numérico, a classe HTTP permanece explícita.
- Os códigos estáveis existentes de corrupção de checkpoint (`checkpoint_scope_payload_tampered`, `checkpoint_ids_hash_mismatch`, `checkpoint_page_sequence_invalid`, `checkpoint_record_count_mismatch`, `checkpoint_total_records_mismatch` etc.) mantêm seus códigos próprios, para não perder diagnóstico na CLI.

## Gates antes de reconhecer expiração de token

1. Obter assinatura de erro de expiração comprovada pelo mantenedor ou pela implementação oficial relevante ao **mesmo endpoint/versão**; registrar documentação, versão, esquema HTTP/status/código estável e SHA-256 do contrato.
2. Demonstrar que a assinatura é exclusiva de expiração, distinguindo token ausente/malformado, permissão, rate limiting, erro de backend, desligamento e deriva de resultados. Mensagens textuais isoladas não bastam.
3. Criar novo PR para pinagem exata da assinatura e testes negativos, inclusive falsos positivos e formatos ambíguos. Manter status conservador em respostas não reconhecidas.
4. Executar CI completo + Codex e somente então avaliar uma sonda real limitada que exercite a continuação **uma única vez por token**, sem gerar erros deliberadamente na API pública.
5. Um restart de epoch só pode ocorrer após confirmação da assinatura, validação independente, autorização do operador e respeito ao orçamento de **uma** tentativa; nunca por 400, 429, 500 ou relógio do cliente.
6. Não iniciar #83, coleta integral ou promoção ao corpus antes de validação metodológica da análise #82.

## Comandos para validação (sem acesso à rede)

```bash
python -m unittest discover -s tests -p 'test_finna_response_classifier.py' -v
python -m unittest discover -s tests -p 'test_kavi_finna_adapter.py' -v
python -m unittest discover -s tests -p 'test_kavi_finna_epoch_recovery.py' -v
```

**Conclusão:** há classificação estruturada e verificável de erros conhecidos, mas **nenhum sinal de token expirado está oficialmente reconhecido ainda**. Estado recomendado: HOLD do reinício automático.
