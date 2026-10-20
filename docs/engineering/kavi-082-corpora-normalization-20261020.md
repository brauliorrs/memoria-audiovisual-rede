# MAR / KAVI–Kuvi — normalização no cadastro de corpora (análise nº 82)

**Revisão:** 2026-10-20 · **Estado deste incremento:** cadastro institucional e visualização de fichas implementados; inclusão no ciclo automático de organismos **ainda não autorizada**.

## Marco verificado

A análise nº 82 mantinha 200 fichas reais no índice de pesquisa, mas KAVI/Kuvi ainda não estava em `CORPORA` e sua aba institucional não existia. O fluxo regular esperava saídas analíticas de instituições, resumos e vídeos; simplesmente apontar o CSV de fichas Finna para essas saídas resultaria em métricas falsas ou numa aba vazia.

Este incremento normaliza o cadastro em `src/memoria_audiovisual/corpora.py` com o código exclusivo **`kavi_kuvi`** e ID de proveniência **`fiaf-kavi`**, diferente de **`fina`**, que é a instituição polonesa FINA/Ninateka. Situa a unidade na categoria **instituição**; **Finna** é a fonte agregadora de metadados, não custodiante presumido de cada filme.

## Integração sem duplicar coleta nem alegar direitos não demonstrados

- `KAVI_KUVI_OUTPUT_FILES` reserva os nomes convencionais para **futuros relatórios padronizados**; não substitui o índice público já validado `data/output/kavi_mar_metadata_links.csv` e seu manifesto. Um relatório inexistente não pode ser apresentado como disponível.
- `kavi_finna_registry.py` chama o leitor auditado `kavi_finna_public_catalog.py`, que valida integridade, origem dos URLs, conteúdo mínimo e não ativação. Calcula contagem de **fichas documentais** separada do indicador de **vídeos publicamente reproduzíveis** (zero confirmados nesta rodada, não ausência de acesso).
- Uma aba **KAVI / Kuvi** apresenta contagem de fichas, total de referência da API, situação de cobertura, filtros simples e botão/link da ficha de origem. Não há player, espelho ou mídia. A busca global continua usando as 200 fichas, agora com o rótulo proveniente do cadastro.
- O overview institucional assinala **índice documental parcial** em vez de somar `recordPage` como `video_links_total`, `videos_in_curatorial_catalog` ou evidência de streaming. A fase científica G4 para declarar universo completo ou custódia continua em HOLD.
- `scripts/check_kavi_kuvi_index.py` fornece verificação local apenas, sem requisição de rede, consumo de token ou alteração dos 200 registros.
- **`published_index_active=true`** significa que os metadados aprovados podem ser consultados; **`organism_active=false`** e **`monthly_refresh_enabled=false`** mantêm KAVI fora do executor periódico enquanto faltam saídas analíticas e rotina incremental de atualização totalmente validada. Isso não apaga fichas nem representa decisão de não estudar o corpus.

## Base factual do snapshot

- [PR #85](https://github.com/brauliorrs/memoria-audiovisual-rede/pull/85) integrado à main no commit `80f099195da4cdafa644293ede6f8ce010cdce84`.
- [GitHub Actions #39346643735](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39346643735) documenta coleta de uma página por API Finna com `robots.txt` validado, sem download de mídia.
- `data/output/kavi_mar_metadata_links_manifest.json`: 200 registros e 200 links de ficha; total de referência no índice API KAVI × vídeo 138.399 em 19/10/2026; `coverage_status=partial`; `media_downloaded=false`; `corpus_activation=false`.
- O acesso funcional no Streamlit hospedado precisa de teste próprio e **não** deve ser declarado verificado com base apenas em CI e GitHub.

## Próximo incremento preciso

1. Construir e auditar **saídas analíticas padronizadas de metadados**, usando os registros já publicados, sem converter fichas em vídeos com reprodução pública. Integrar com os mesmos indicadores comparáveis onde a semântica permitir e criar dimensões explícitas de cobertura do índice.
2. Implementar a **atualização incremental** reaproveitando o coletor staged, com checkpoint persistente, token de retomada, expiração, contagens e reconciliação de modificações/remoções e falhas; sem download de vídeo nem requisições abusivas.
3. Só habilitar `organism_active` e `monthly_refresh_enabled` depois de documentar/validar os dois contratos e a execução programada na rede. O conjunto total de registros da API não é contagem de filmes custodiados e a fração indexada pode variar por snapshot.
4. Abrir e encerrar PR por check verde, revisão de P1/P2, testes de integridade; registrar SHA/decisão na [issue #59](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59) e atualizar a memória do Google Drive após o merge.

**Meta institucional permanente:** incorporar todas as fichas audiovisuais legitimamente acessíveis e os links oficiais às instituições de origem; o MAR nunca baixa, hospeda nem serve o conteúdo audiovisual. Não confundir a camada de catalogação com direitos de reprodução.
