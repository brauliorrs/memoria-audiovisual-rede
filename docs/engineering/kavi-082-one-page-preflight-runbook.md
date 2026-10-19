# KAVI/Kuvi nº 82 — pré-validação de acesso e ensaio de **uma página** (G3)

## Marco verificado posteriormente — execução única de 19/10/2026

**Este resultado substitui o estado operacional "não executado" que constava no pré-registro de 15/10/2026; as instruções abaixo são o protocolo histórico prévio, não uma autorização para repetir o ensaio.**

- **Prova viva:** [GitHub Actions run #39290009804](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39290009804), ramo instrumental `analysis/kavi-082-one-shot-g3-20261019`, HEAD `20eb6f2f25fdbd09fa7e9c657817aa577c28097a`. Run e job `kavi-082-one-shot`: **success**.
- **Robots do próprio host API:** `https://api.finna.fi/robots.txt`, HTTP **200**, `mode=evaluated`, SHA-256 do conteúdo `c16fa7433f3c2395b6435c835f4085346aa4c5c98bbfaad347eefad3bac67294`. O Guard do MAR devolveu `true` para cada rota necessária: `building_facet`, `format_facet`, `scope_count`, `one_page_start`. Resultado do gate: `ALLOW_ONE_PAGE` naquele runner e naquela data.
- **Ensaio real:** `run_kavi_finna_metadata_staging.py --max-pages 1 --execute`, SHA da evidência institucional `466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049`; o preflight teve os 3 GETs previstos e o lote inicial mais 1 GET. Resumo de CI, validado pelo próprio job: `expected_total=138393`, `page_count=1`, `record_count=200`, `status=partial`, `media_downloaded=false`, `promotion_authorized=false`.
- **Artefato público (redigido):** `kavi-082-g3-20261019-public-gate`, ID **12203723866**, ZIP SHA-256 `958ae76f19208a3df169125761c5cf5435daac64b3f4dfecd3349fa20f2e5178`. Não se publicaram registros brutos, imagens, vídeos, cookies nem `resumptionToken`. Diretório privado de staging removido ao final do job.
- **Interpretação:** o endpoint de metadados estava acessível mediante `robots` naquele instante e houve acesso e auditoria técnica de **uma página**. **138.393** é total anunciado de **registros de vídeo no índice sob o filtro institucional**, não total de filmes reproduzíveis, custodiados ou já capturados. A diferença em relação aos totais históricos não é prova de crescimento sem controlar os snapshots.
- **Estado posterior:** `LIVE_ROBOTS=VERIFIED_FOR_ROUTES_AT_2026-10-19`; `LIVE_ONE_PAGE=VERIFIED_PARTIAL`; `MACHINE_COLLECTION=PARTIALLY_VERIFIED`; `CORPUS_ADMISSION=HOLD_PROVISIONAL`; `INVESTIGATION_COMPLETE=false`.
- **Não repetir por rotina:** o teste concluiu o gate solicitado. A próxima ação é análise de admissibilidade/escopo, custódia, cobertura e direitos por registro, não refazer sondas ou tentar enumeração massiva. O PR instrumental da execução não deve ser incorporado à `main`.

Evidência e decisão arquivadas na [issue #59](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59#issuecomment-6272633816).


**Data:** 2026-10-15  
**Status da autorização:** **documentação/licença confirmada; acesso técnico atual ainda não validado** (robôs do host `api.finna.fi` não puderam ser consultados por este ambiente).  
**Autorização operacional deste documento:** **NÃO EXECUTAR ENQUANTO O GATE DE ROBOTS NÃO PASSAR**. Não há agendamento e nenhum request de metadados é autorizado por este documento isoladamente.  
**Relação com o PR #80:** delimita o teste técnico sobre o coletor staged *já existente*, sem modificar o pipeline, reproduzir audiovisual ou burlar desafio humano.

## 1. Evidências e o que foi efetivamente testado

1. [Termos oficiais da API Finna](https://www.kiwi.fi/spaces/Finna/pages/53839699/Finna%2BAPI%2BTerms%2Bof%2BUse): acesso aberto sem cadastro (sujeito a restrições para proteger o serviço), metadados **efetivamente publicados na API** sob CC0 1.0. **Não estende CC0 a vídeos, imagens, `onlineUrls`, `urls` ou `images`**, nem a descrições externas à API.
2. [Documentação oficial](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish): método `/v1/search`, facetas, limite de paginação ordinária 100 mil e `resumptionToken` com `*` no primeiro lote; lotes seguintes usam token devolvido pelo servidor. O mecanismo é público mas não prova viabilidade operacional para colher >100 mil resultados.
3. [Termos de uso de Finna](https://www.finna.fi/Content/terms?lng=en-gb): vedam robôs em **funcionalidades que exigem login**; o desafio anti-bot do catálogo Elonet **não será contornado**. O ensaio usa **exclusivamente** o host oficial de API e o código existente.
4. **Estado atual da verificação de robots:** em 2026-10-15, a ferramenta pública não abriu `https://api.finna.fi/robots.txt`. Consulta separada a **somente essa URL** a partir do ambiente desta análise falhou com `NameResolutionError: Temporary failure in name resolution`. **Nenhum endpoint `/v1/search` foi requisitado nessa tentativa.** Isso representa `environment_limited`, **não** `source_blocked` e não permite iniciar o teste vivo deste ambiente.
5. Evidência histórica do próprio projeto: [prova de 2 páginas](kavi-082-resumption-integrity.md), 400 metadados retornados e auditados no escopo `building:"0/KAVI/" AND format:"0/Video/"`, sem evidência de enumeração integral, custódia ou direitos de mídia.

## 2. Execução delimitada no ambiente apropriado

**Pré-condições para o operador**, todas obrigatórias:
- Usar ambiente de rede com DNS confiável e um cliente identificado, sem túnel, proxy ou bypass criado para evitar a barreira do site. Acessar **uma vez** o `https://api.finna.fi/robots.txt` pelo mesmo ambiente e User-Agent do executor. Registrar a data, HTTP status, digest do corpo e decisão do parser para as rotas de API solicitadas. Se não for possível verificar ou se a rota for negada, **STOP**, sem tentar `/v1/search`.
- Confirmar a versão vigente dos termos e ausência de instrução do mantenedor proibindo a execução; respeitar `Retry-After` quando aplicável **interrompendo** a tentativa, sem retry automático.
- Usar o SHA-256 de **evidência de descoberta do escopo já identificada e auditada** (artefato histórico validado), não uma string de exemplo, hash aleatório ou digest fabricado. A correspondência entre artefato, código `0/KAVI/`, formato `0/Video/`, data e commit deve estar no protocolo de execução.
- Direcionar `--directory` a um diretório **novo, restrito, temporário e fora do Git**; em CI, não publicar o diretório bruto nem seu checkpoint com `resumptionToken`.
- Executar **uma única tentativa**, apenas se aprovado; no máximo uma página de resposta. Nenhuma continuação, `--resume`, reinício após erro, cron ou workflow agendado.

**Prévia totalmente offline (não dispara rede):**

```bash
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 "$EVIDENCE_SHA256" --max-pages 1
```

**Comando a executar somente após todos os gates positivos:**

```bash
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 "$EVIDENCE_SHA256" \
  --directory "$PRIVATE_STAGING_DIR" \
  --max-pages 1 --delay-seconds 1.0 \
  --execute
```

`EVIDENCE_SHA256` precisa ser SHA-256 auditado com 64 caracteres hexadecimais. `PRIVATE_STAGING_DIR` é um diretório efêmero único com permissão privada. O script rejeita página >25 por comando, mas **este protocolo restringe ainda mais a 1**.

## 3. Quantidade real de chamadas e barreiras

O comando **não** executa somente uma requisição HTTP: antes da única página ele realiza preflight (faceta institucional, faceta de formato e contagem filtrada; **até três GETs de metadados**) e valida `robots.txt` para o host conforme `Guard`; depois faz **um GET do primeiro lote** via `resumptionToken=*`. O teto é **1 lote retornado**, não “um único request”. Cada GET passa pelas restrições de origem/redirects, MIME, JSON, tamanho máximo 8 MiB e avaliação de `robots`. A resposta histórica de um lote teve **200 registros**, mas isso **não é garantia de tamanho atual**.

Ao retornar qualquer desafio/HTML inesperado, 401/403/429, timeout, DNS, mudança ou ambiguidade de faceta, formato inesperado, IDs inválidos/duplicados, token defeituoso, divergência de contagem ou direitos ambiguamente promovidos, a implementação deve **abortar** e manter o estado de evidência `rejected/partial`, sem retry e sem tentativa pela interface Elonet.

### Check de aceitação do teste

| Evidência | Condição necessária | Se faltar |
|---|---|---|
| Permissão técnica de caminho | Robots do host de API verificados no próprio executor; termos atuais registrados | **NO_EXECUTE** |
| Escopo institucional | Faceta única `0/KAVI/`, formato `0/Video/` reconfirmado e total reportado | **REJECT** |
| Lote | No máximo **uma** página retornada, itens com ID/título e classificação de vídeo verificável; nenhum ID repetido | **REJECT** |
| Integridade | Hash de escopo e de sequência, cadeia de checkpoint verificável, contagem compatível, resumo redigido sem token | **REJECT** |
| Direitos e público | `media_downloaded=false`, `promotion_authorized=false`, status de direitos e custódia = desconhecidos/não demonstrados | **REJECT** |
| Resultado aceito | **Somente** valida `one_page_metadata_access_verified`, `status=partial`; não declara enumeração total ou permissão de reprodução | **HOLD** |

**Saída permitida para a issue #59:** data, commit, versão do script, hash da evidência de escopo, condições de robots (sem conteúdo sensível), contagem da faceta, `page_count`, `record_count`, classes agregadas, hashes dos IDs, flag `promotion_authorized=false`, ausência de mídia. **Não publicar:** payload bruto, token de retomada, URL com token, sessão/cookie, filmes/imagens, diretório staging, evidência de autenticação.

**Resultado atual nesta data:** `TERMS_VERIFIED`, `BATCH_MECHANISM_DOCUMENTED`, `HISTORICAL_2PAGE_PROBE_VERIFIED`, `LIVE_ROBOTS=ENVIRONMENT_LIMITED`, `LIVE_ONE_PAGE=NOT_EXECUTED`, `CORPUS_ADMISSION=HOLD_PROVISIONAL`.

## 4. Decisão seguinte

Um sucesso de **uma página** prova somente a acessibilidade delimitada do endpoint e a compatibilidade mínima do staging. **Não** comprova cobertura total, autorização de uso de mídia, posse das obras ou capacidade para capturar os ~138 mil vídeos históricos. Um possível plano de enumeração integral fica para revisão separada com análise de custo, atualizações do provedor, timeout de token, reconciliação/remoções e direitos por item. Não transferir audiência: os links de reprodução devem continuar na instituição de origem.
