# Decisão final da análise nº 82 — KAVI/Finna: HOLD de admissibilidade

**Data da adjudicação:** 13/10/2026.  
**Unidade:** `fiaf-kavi`, KAVI / National Audiovisual Institute, Finlândia.  
**Escopo ensaiado:** Finna REST Search, `building:"0/KAVI/"` + `format:"0/Video/"`.  
**Decisão:** **HOLD/protocolo, sem promoção e sem incorporação ao corpus MAR.** Análise nº 82 concluída metodologicamente; trabalho de melhoria do conector poderá ser retomado futuramente em tarefa separada se surgirem evidências adicionais.

## Matriz de acessibilidade — não confundir acesso ao catálogo e elegibilidade

1. **Documentação e acesso a metadados: positivos.** A [documentação oficial Finna API](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish) descreve a busca pública e `resumptionToken=*` para resultados grandes. A análise #82 recuperou, em sonda viva anterior registrada na issue #59 e PR #62, **duas páginas de 200 registros**: **400 metadados**, total de busca **138.379** informado naquele snapshot, 399 *candidatos* `kavi.elonet_elokuva_...` e 1 outro vídeo. A recuperação histórica é evidência de acessibilidade pública **à época**, não prova de que a API continue respondendo na data atual.
2. **Não demonstrada a enumeração completa, estável e reproduzível.** A sonda viva posterior no PR #65 falhou por rejeição **do nosso próprio cliente**, `resume_cursor_expiration_timezone_missing`, porque o campo `expires` veio sem fuso. **Isso não prova queda ou indisponibilidade da Finna**. O PR #69 integrou uma via opt-in conservadora que permite uma página por token validado pelo servidor, mas foi validada **somente offline** após sua implementação; não há prova viva de três retomadas independentes.
3. **Origem custodial e semântica de patrimônio não validadas.** Registros indexados em `building=0/KAVI/` não demonstram, por si só, que sejam fichas patrimoniais sob custódia específica do KAVI; `kavi.elonet_elokuva_` é candidato a filme, não comprovação de titularidade, custódia ou itens disponíveis.
4. **Direitos e disponibilidade de mídia não comprovados.** O acesso a *metadados* não significa download autorizado de vídeos nem seus direitos. Nenhuma mídia foi baixada ou promovida.
5. **Falha de acesso atual não atribuível ao serviço.** Em 13/10/2026, um ambiente de execução local tentou resolver `api.finna.fi`, `www.finna.fi`, `github.com` e `example.com` e todos falharam na resolução DNS. Um mecanismo web também não conseguiu obter a resposta dinâmica da API, embora a documentação oficial tenha sido localizada. Esta situação caracteriza **limitação do ambiente de investigação**, não uma evidência suficiente para classificar a Finna como globalmente indisponível.
6. **Tentativa experimental PR #70 não executou coleta.** Falha de configuração do GitHub Actions ocorreu antes de criar jobs; a PR foi fechada sem merge. Uma segunda branch experimental não chegou a abrir PR por restrição de segurança da conexão. Portanto essa fase recuperou **zero** novas páginas, e não altera a evidência positiva de 400 registros do PR #62.

## Aplicação do gate formal da issue #59

O protocolo da issue nº 82 exige, para admissão staged, **enumeração pública completa/reproduzível de fichas patrimoniais e proveniência**. Os testes atuais não demonstraram enumeração integral do recorte nem custódia/direitos; portanto **HOLD/protocolo** é a decisão consistente com o critério de projeto, independentemente de o endpoint estar online.

**Não rotular como `source_unavailable` ou `Finna fora do ar`.** Usar **`metadata_public_access_previously_confirmed; complete_enumeration_and_custody_unverified; HOLD_no_corpus_admission`**.

### Evidências preservadas

- Issue #59: https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59 (histórico e ensaios).
- PR #62: duas páginas reais de metadados (400 registros) e auditoria, sem mídia; hash agregado da sequência de IDs `8f96abb10a17c8f78c47a00af9f29016b4316c923cdfad37b38f94cd220107ea`.
- PRs #63–#64: replay/auditoria de checkpoint e gate seguro de continuação.
- PR #65: HOLD real `resume_cursor_expiration_timezone_missing`; encerrado como substituído.
- PRs #66–#68: mecanismo **offline** de epochs, taxonomia de falhas e erro combinado inválido/expirado.
- PR #69: opt-in de uma página por token, testado offline, sem retry e sem interpretação de fuso.
- PR #70: tentativa de workflow sem jobs, fechada sem merge. Não representa falha da fonte.
- Documentação oficial Finna API: https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish.

## Continuidade da fila

Após integrar este parecer, encerrar formalmente issue #59 como **HOLD concluído** (não como integração de corpus) e abrir a análise cumulativa **nº 83 — Kinoteka da Macedônia do Norte**, conforme fila pinada na própria issue #59. O próximo site institucional identificado é **https://kinoteka.mk/**, que possui seção oficial de arquivo de filmes: https://kinoteka.mk/en/film-archive-2/ . Isso comprova a existência da instituição e uma descrição do arquivo, **não** sua enumeração pública; aplicar novamente robots/HTTPS/sitemap/navegação/semântica/gate sem pressupor admissibilidade.

**Proibições:** não baixar mídia, não adicionar registros KAVI ao corpus, não apagar a trilha de pesquisa, não promover baseados apenas em 400 registros parciais, não tratar acesso falho do executor como prova de queda do fornecedor. A nº 84 mantém sua posição na fila.
