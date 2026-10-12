# KAVI #82 — gate de retomada entre lotes (pós PR #63)

## Status metodológico

O PR #63 incorporou uma auditoria **offline** dos checkpoints à `main`. Este incremento conecta o runner de staging já existente à auditoria, sem reimplementar o coletor, sem alterar `MetadataPageSource`, sem coletar mídias e sem promover resultados ao corpus MAR. A continuidade com `resumptionToken` foi validada ao vivo em **duas páginas** no PR #62; **não** foi validada integralmente para o índice (~138 mil registros em observação histórica).

A API Finna documenta `resumptionToken=*` como início de uma enumeração por lotes e continuidade com apenas o token retornado, sem `limit`, `page` ou `facet[]` na continuação. Referência: https://www.kiwi.fi/spaces/Finna/pages/51842373/Finnan%2Bavoin%2Brajapinta%2BFinna%2BAPI. A implementação já respeita essa regra no adaptador. O limite temporal real de validade do cursor **não foi garantido pela documentação analisada**; o lote vivo retornou um objeto com `token` e `expires`, que deve agora ser validado localmente.

## Fluxo seguro, obrigatório

1. Nova execução: o executor real exige `--execute`, diretório local persistente, escopo KAVI/Video aprovado e limite explícito de **1 a 25 páginas** (padrão 1). `stage_metadata` executa preflight HTTP/robots, valida o total e preserva checkpoints e raw SHA-256. O CLI imprime apenas resumo público.
2. Após **cada lote**, o runner chama a mesma auditoria offline do PR #63. Ela faz replay de todos os artefatos e verifica scope, hashes, cadeia de cursores, total, IDs originais/normalizados, origem institucional, classificação e flags de direitos/custódia. A aprovação significa apenas integridade local.
3. Em **retomada**, o operador deve informar `--resume --expected-total N` com a contagem daquele preflight preservada **fora** do checkpoint. A auditoria offline ocorre *antes* de qualquer chamada externa. Um checkpoint completo é revalidado sem novas chamadas HTTP.
4. Se parcial, a validade temporal de `source_response.resumptionToken.expires` da última página é comparada ao relógio UTC. Sem data ISO-8601 timezone-aware, com cursor diverso do normalizado ou expirado/na margem de segurança, **HOLD antes de chamadas HTTP**. Por padrão exige no mínimo 30 segundos restantes. Não são fabricados cursores nem feitos resets/retries automáticos.
5. Entre páginas do mesmo lote: mínimo 0,5 s (padrão 1 s). Na retomada, um atraso extra equivalente ocorre antes da primeira busca do novo lote. Nenhum bypass de robots e nenhum aumento do limite de resposta JSON de 8 MiB.
6. Em seguida o executor realiza novo preflight, rejeita deriva do total, só então busca via token autorizado. Após o lote, executa novamente a auditoria offline; qualquer rejeição mantém o corpus inalterado.

**Restrição explícita:** mesmo cursores não expirados podem ser rejeitados pelo servidor; esta verificação temporal é necessária, mas não prova continuidade longa, snapshot consistente ou ausência de paginação instável. A contagem da API é dinâmica e a classificação por prefixo de ID é apenas indicativa, não prova patrimônio sob custódia do KAVI.

## Executar manualmente (não usar na CI)

Novo lote mínimo:

```bash
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049 \
  --directory data/staging/kavi-finna \
  --max-pages 1 --delay-seconds 1 --execute
```

Continuação **somente** enquanto o token não tiver expirado e se houver registro externo da contagem exata do preflight inicial:

```bash
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049 \
  --directory data/staging/kavi-finna \
  --max-pages 1 --delay-seconds 1 \
  --resume --expected-total <TOTAL_ORIGINAL> --execute
```

O total 138.379 mencionado em evidência anterior **não é** uma contagem universal atual. Usar somente a contagem específica do checkpoint local. O comando padrão sem `--execute` é `DRY RUN`. Não compartilhar `data/staging/`, raw IDs nem cursor opaco no Git, artifact CI ou saída do CLI.

## Comprovação, limitações e próximas decisões

- Testes sintéticos (sem rede) verificam sucesso parcial/completo, retomada, atraso interlotes/intralotes, adulterações de cursores, expiração, ausência de prazo, timestamps sem timezone, alterações de total, escopo não autorizado e limite de 25 páginas.
- A CI geral roda toda a suíte `unittest`. **Nenhuma coleta real integral ou nova sonda viva** é disparada neste PR.
- Se o servidor devolver um formato de `expires` diferente de ISO-8601 UTC/offset, classificar como incompatibilidade **HOLD**, sem interpretar por adivinhação. Só adaptar após capturar evidência limitada, sem divulgar o token.
- Não há checkpoint independente em armazenamento de longa duração nem mecanismo provado de snapshot estável. Os limites `max-pages` evitam execução ilimitada, mas não demonstram sustentabilidade de uma enumeração longa.
- A issue #59 e a análise nº 82 permanecem abertas. NÃO promover ao corpus, NÃO baixar mídia e NÃO iniciar a análise nº 83 antes do gate final.

## Testes

```bash
python -m unittest discover -s tests -p 'test_kavi_finna_batch_gate.py' -v
python -m unittest discover -s tests -p 'test_kavi_finna_offline_audit.py' -v
python -m unittest discover -s tests -p 'test_metadata_staging.py' -v
```
