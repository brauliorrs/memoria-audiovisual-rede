# KAVI #82 — Validação de continuação e integridade de metadados Finna

## Relação com o sistema existente

Este incremento parte do PR #61, integrado na `main` com CI verde, sem criar um segundo pipeline MAR. Reutiliza `RawArtifactStore`, `FileWriteLock`, o contrato `MetadataPageSource` e o executor `stage_metadata`. A sonda anterior provou **uma página real de 200 registros**, frente ao total de referência **138.377 vídeos indexados** na faceta `building:"0/KAVI/"` × `format:"0/Video/"`; o staging permaneceu parcial, sem mídia e sem promoção.

## Objetivo estritamente delimitado

Comprovar que `resumptionToken` funciona também na **continuação entre páginas**, além da primeira chamada, e que a retomada relê e verifica artefatos imutáveis. O CI executará **uma página inicial + uma página de continuação**, em diretório temporário descartável. A execução começa apenas com `robots.txt` e preflight das facetas, usando filtros originados da API e hash de evidência previamente validada.

Não é um job de ingestão integral de 138 mil resultados. Não existe autoagendamento ou loop de captura de mídia. Os registros brutos, IDs e tokens opacos não são publicados no artefato do CI; o relatório resume apenas contagens, integridade criptográfica e classificação metodológica.

## Diagnóstico da primeira execução viva do PR #62

A sonda de duas páginas foi iniciada, mas **não chegou à segunda página** nas primeiras execuções de CI. O preflight passou e a API respondeu à consulta inicial de metadados; o `Guard.get` rejeitou o conteúdo com `body_size_limit`. Portanto, o problema não era `resumptionToken` nem bloqueio HTTP — o teto de **2 MB**, adequado à descoberta HTML, era pequeno para um lote de 200 fichas filmográficas completas.

Ajuste limitado ao adaptador KAVI/Finna: `Guard(session, max_body_bytes=8 * 1024 * 1024)`, com streaming e interrupção acima de **8 MiB**, mantendo **2 MB** como teto padrão dos probes institucionais. Regressões comprovam o limite e impedem configuração ilimitada. Não foram removidos os controles de MIME, `robots.txt`, escopo, cursor, direitos ou IDs.

A confirmação ocorreu na execução viva descrita abaixo. A incorporação de metadados ao corpus principal permanece **não autorizada**, porque a enumeração integral e o gate humano ainda não foram concluídos.

## Evidência viva — continuação real de duas páginas

- GitHub Actions **Quality Checks #38189112168**, HEAD validado `cff46e3f05def11accc81c6e3c69f027d1a920c9`.
- Artefato público `kavi-finna-two-page-public-probe`, id **11720539255**, ZIP SHA-256 `f25911987133fb50820b0e6072f9d15985892d78ca3535e1082937248d854356`.
- A API retornou contagem de escopo `expected_total=138379` para os filtros KAVI/Kuvi × vídeo; esta contagem é uma fotografia temporal, não uma afirmação de patrimônio sob custódia.
- Primeira página: **200** registros, `status=partial`. Segunda chamada usando o token retornado: **400** registros acumulados, `page_count=2`, `resumption_verified=true`, `status=partial`.
- Auditoria: **399** IDs de `film_candidate`, **1** outro vídeo, **0** registros sem formato `0/Video/` confirmado, **0** registros com custódia estabelecida e **0** com direitos de mídia verificados.
- SHA-256 da sequência das 400 identificações (sem divulgar IDs): `8f96abb10a17c8f78c47a00af9f29016b4316c923cdfad37b38f94cd220107ea`.
- Nenhum token, registro bruto ou URL de mídia está no artefato público. `promotion_authorized=false` e `media_downloaded=false`. O diretório de staging do job foi descartado ao final da execução.

**Gate alcançado:** validação real de continuação e replay de duas páginas, com integridade e proveniência metodológica; **não é** enumeração integral dos 138.379 registros nem verificação de custódia/direitos individuais.

## Gates reforçados

1. Recalcular cada hash de `next_cursor_sha256` presente nas páginas do checkpoint, em vez de verificar apenas hash do token de entrada e token final.
2. Verificar `promotion_authorized=false` e `media_downloaded=false` ao restaurar, rejeitando alterações maliciosas nos indicadores do checkpoint.
3. Manter a proibição de IDs duplicados dentro de uma página e entre páginas, total estável entre preflights e resultado final da API, escopo imutável, sequência e cadeia de tokens verificadas por SHA-256.
4. Auditar após a retomada a correspondência **ordenada** entre IDs de metadados normalizados e IDs da resposta original, o código `provider_index_code` e o estado de direitos e custódia. Não transformar a faceta institucional em comprovação de propriedade física.
5. Apresentar contagens de `film_candidate` versus outros vídeos e de formatos `0/Video/` não confirmados nos registros da amostra. Esses números são diagnósticos; não equivalem à promoção de fichas individuais.
6. Gerar SHA-256 da sequência observada de IDs, sem publicá-los. Não disponibilizar links diretos de mídia, tokens de retomada ou conteúdo integral das páginas de resposta.

O ensaio vivo aplica uma pausa explícita de **1 segundo entre os dois lotes**, inclusive quando `stage_metadata` é chamada duas vezes com `max_pages=1`, pois o throttling interno só funciona dentro da mesma invocação. O intervalo é injetável em testes e não altera a sequência de tokens nem os controles de acesso.

## Condições para continuação da análise nº 82

- Se o segundo lote falhar, preservar o gate de staging parcial e classificar a causa. Nunca contornar `robots.txt`, alterar o cursor arbitrariamente ou pular páginas.
- Se o segundo lote passar, **apenas o protocolo de paginação de duas páginas** está verificado; a enumeração integral, checkpoints persistentes entre ambientes, licença e custódia por ficha continuam pendentes.
- A análise nº 82 continua aberta na issue #59. Não avançar ao nº 83, nem incorporar automaticamente à análise audiovisual do MAR.

## Reproduzir testes

```bash
python -m unittest discover -s tests -p 'test_metadata_staging.py' -v
python -m unittest discover -s tests -p 'test_kavi_finna_two_page_resume.py' -v
python scripts/probe_kavi_finna_two_page_resume.py \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049

# Somente com autorização de consulta pública, executa duas páginas:
python scripts/probe_kavi_finna_two_page_resume.py \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049 \
  --execute
```
