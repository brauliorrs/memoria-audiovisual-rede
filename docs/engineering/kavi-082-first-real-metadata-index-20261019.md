# MAR — KAVI/Kuvi nº 82: primeira inserção real de fichas com links

**Data da observação:** 19/10/2026 (horário do Brasil); o runner GitHub registrou a operação em 20/10/2026 UTC.  
**Fonte:** API oficial Finna, `building:"0/KAVI/"` e `format:"0/Video/"`.  
**Objeto efetivamente materializado:** metadados estruturados e **URLs de fichas Finna**, nunca arquivos de vídeo.

## 1. Evidência real do primeiro lote

- [GitHub Actions #39346643735](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39346643735) executou 1 lote via coletor staged existente, depois de `robots.txt` HTTP 200 e quatro rotas aprovadas pelo Guard do MAR. Sem bypass de desafio humano do Elonet.
- **200 registros** recebidos, **200 URLs individuais `recordPage`** efetivamente fornecidas no JSON e transformadas em páginas `https://www.finna.fi/Record/...`, com IDs verificados. **Zero fichas sem destino** neste lote.
- A API anunciou **138.399 registros de vídeo filtrados** nessa observação. A razão 200/138.399 mede **cobertura inicial indexada nesta faceta da API**, não amostragem estatística nem porcentagem de filmes disponíveis em streaming.
- Artefato verificável: `kavi-082-first-link-index-20261019`, ID **12231870011**, [run de origem](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39346643735), digest do ZIP `sha256:ed4a549724db160610e78ecea6e84e8cb5db8b7b7e9476c1fe6d8c086e470e59`.
- CSV preservado sob `data/output/kavi_mar_metadata_links.csv`, SHA-256 `2458484980094c10db9e9f990b6ca2236e8abcfdb09d3cafc886d0e0e9b22a31`. A saída não contém `onlineUrls` brutos, imagens, MP4, M3U8 ou cursores de continuação.
- Manifesto em `data/output/kavi_mar_metadata_links_manifest.json` associa o CSV a hash, faceta, total da API, data, status e evidence run, preservando `corpus_activation=false`, `media_downloaded=false`, `metadata_license=CC0-1.0_API_metadata_only`, e `media_rights_status=not_verified` por item.

## 2. Admissão por lote e consulta na plataforma

A publicação é **somente do índice de metadados**. O módulo `kavi_finna_public_catalog.py` valida que o CSV e manifesto estão presentes, hash e contagens concordam, 200 IDs são únicos, URLs individuais pertencem a fichas Finna/Elonet e os direitos de mídia não foram classificados sem provas. **Não** libera a admissão científica global de 138.399 registros, não afirma posse custodial pela agência e não afirma que todos os vídeos sejam reproduzíveis.

O `build_research_video_catalog_frame` da interface de pesquisa MAR acrescenta as fichas aprovadas à busca unificada, com distinção visível **KAVI/Kuvi — índice parcial de metadados** e destino **Acessar na origem**. A opção **somente vídeos públicos** não pode tratar uma ficha `recordPage` como prova de reprodução livre; registros KAVI com `media_access_status=unverified` são excluídos desse filtro, mas continuam consultáveis na busca geral.

**Aspecto do link:** a API Finna documenta `recordPage` como link relativo a `www.finna.fi`, portanto a origem pública documentada neste lote é a própria ficha Finna. Um link preferencial do serviço Elonet será possível **apenas quando a ficha Elonet correspondente tiver sido evidenciada**, sem construção especulativa de URLs. A reprodução permanece sempre na plataforma externa; o MAR não incorpora player nem hospeda mídia.

## 3. Metodologia e continuidade

- **Cobertura progressiva:** estado `published_partial_metadata`, 200 registros de uma página. Ao ampliar os lotes, preservar IDs e rastreio de snapshot, atualizando a cobertura e evitando duplicação/reutilização de cursors vencidos.
- **Semântica:** os 200 itens deste lote são `film_candidate` por padrão do ID institucional; a avaliação humana e a tipagem curatorial permanecem separadas da mera indexação.
- **Custódia:** `not_established` nos registros; `building=0/KAVI/` mostra o provedor de metadados, não o custodiante do filme.
- **Direitos:** CC0 para os metadados efetivamente disponibilizados na API, não para obras audiovisuais, imagens e URLs de streams. O link para a ficha não promete acesso ao player.
- **Serviços complementares:** Elonet, Elävä muisti, Elokuvapolku e Ritva têm regras próprias e não podem ser somados à contagem da faceta KAVI × Video sem prova de cobertura e reconciliação de IDs.
- **Próxima escala:** planejar paginação/cursor, ritmo permitido, persistência de checkpoints, atualização por lotes, rotas canônicas da agência e direitos/acessibilidade; não iniciar enumeração indiscriminada de 138 mil registros com base no sucesso de uma página.

**Distinção de gates:** o G3 autorizou o acesso por um lote; o G4 ainda mantém em HOLD a **afirmação científica de cobertura total e de custódia/direitos individuais**. A publicação de fichas documentais com links e indicação de cobertura parcial atende à diretriz do MAR sem fingir que o acervo completo já foi observado.

**As duas rotinas transitórias de GitHub Actions criadas para recuperar e importar este lote foram removidas da alteração antes da integração à `main`**, preservando a prova imutável do run e apenas o pipeline regular de qualidade.
