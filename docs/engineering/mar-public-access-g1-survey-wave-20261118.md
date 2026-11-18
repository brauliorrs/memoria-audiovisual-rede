# MAR — Rodada G0/G1: navegação pública de corpora (18/11/2026)

**Escopo:** nova rodada documental limitada a rotas oficiais visíveis em navegador/ferramenta web. Não é autenticação como visitante real com JavaScript garantido, não é auditoria dos registros históricos em massa, nem coleta, incorporação ou validação de direitos de cada ficha. Uma falha HTTP/timeout da ferramenta é `environment_limited`, não prova de que a instituição bloqueie o público.

| Corpus | Página oficial consultada | Estado G1 observado | Evidência e limite |
|---|---|---|---|
| Archives Portal Europe (`ape`) | https://www.archivesportaleurope.net/tools/for-users/ | `portal_search_interface_observed` | Ajuda descreve pesquisa pública por arquivo, pessoas e instituições; não foram visitadas as 412 fichas históricas |
| CICLIC (`ciclic`) | https://memoire.ciclic.fr/les-memoires-filmees-catalogue | `environment_limited` | Catálogo indicado por material oficial; tentativa de abrir outra página CICLIC resultou 403 da ferramenta |
| Bundesarchiv (`barch`) | https://www.bundesarchiv.de/im-archiv-recherchieren/archivgut-recherchieren/recherchesysteme/digitaler-lesesaal/ | `institutional_route_observed` | Página oficial confirma o sistema Digitaler Lesesaal para filmes e sua substituição do Filmothek; tentativa de abrir o aplicativo de pesquisa terminou em timeout |
| ASIM Mallorca (`asim`) | https://www.conselldemallorca.es/es/asim | `institutional_route_observed` | Página oficial confirma consulta presencial aberta e amostras pela internet em plataformas terceiras; não comprova um catálogo integral aberto |
| Bulgarian National Film Archive (`bnfa`) | https://europeanfilmgateway.eu/about_efg/partners_contributors/bulgarian-national-film-archive | `aggregator_profile_observed` | Perfil BNFA encontrado no European Film Gateway, mas a rota de coleção retornou 403 da ferramenta |
| European Film Gateway (`european-film-gateway`) | https://www.europeanfilmgateway.eu/content/Arxiu%20del%20So%20i%20de%20la%20Imatge%20de%20Mallorca%20(Palma) | `aggregator_profile_observed` | Identificada página de contribuinte e referência à coleção ASIM; não houve avaliação de licenças ou enumeração |

## Evidência nova — licença explícita de metadados APE
Página institucional: https://www.archivesportaleurope.net/metadata-usage-guidelines/

A política publicada declara metadados sob **CC BY-SA 4.0 salvo indicação contrária**. Condições incluem atribuição ao provedor/instituição e agregadores, identificação da licença, link às fontes e divulgação de alterações, observando exceções e legislação aplicável. Recomenda uso de links ou API devido à atualização dinâmica de metadados.

**Decisão:** `conditional_open_metadata_policy_review_per_record`. O antigo bloqueio operacional por falta de acesso oficial não se confunde com proibição legal absoluta. A publicação de 412 entradas históricas ainda requer inventário de fontes originais, avaliação de exceções, metadados de atribuição e verificação de consistência. **Nenhuma ficha APE foi liberada**.

## G2/G3/G4 não comprovados nesta rodada
- Acessibilidade efetiva de fichas por navegador humano nos cinco corpora: parcialmente **não testada**; sobretudo APE (interface documentada), CICLIC, Bundesarchiv, BNFA e ASIM.
- Consulta com autenticação, limites territoriais, direitos audiovisuais, regras de crawling, segurança dos registros ou permissão de mídia: **não examinadas**.
- Aderência dos registros de 2026-06 ao estado atual: **não revalidada**.
- Direitos/licenças específicos de cada corpus: **pendentes**, exceto a regra geral identificada para APE, ainda sujeita a exceções.
- Conclusão científica ou publicação: **HOLD**, documentos informativos apenas.

## Não confundir
1. Catálogo **existente** vs ficha **efetivamente aberta**.
2. Ficha pública vs reprodução do filme vs redistribuição de metadados.
3. 403/timeout da ferramenta vs restrição imposta ao cidadão comum.
4. Texto com CC BY-SA no APE vs autorização indiscriminada para exportar registros sem conferir exceções.

Os estados desta rodada foram transcritos para `site/data/public-access-observatory.json`; `recordDisplay` permanece `not_authorized_for_new_site` e o contador KAVI permanece 200. O Streamlit e corpora científicos congelados permanecem inalterados.


## Segunda leva — cinco interfaces e orientações adicionais
| Corpus | Fonte | Resultado | Ponto de licença |
|---|---|---|---|
| Europeana | https://www.europeana.eu/en/rights/europeana-data-sources | Política institucional acessível; pesquisa pública documentada | Metadados publicados pela Europeana sob CC0; imagens, vídeos e outros conteúdos não se tornam CC0 automaticamente. Conferir origem das 20 fichas do CSV antes de projetá-las |
| EUscreen | https://euscreen.eu/collections/ | Coleções e pesquisa públicas documentadas | Direitos de audiovisual permanecem com arquivos parceiros; licença para republicar metadados não verificada |
| American Archive of Public Broadcasting | https://americanarchive.org/search | Busca e filtros de Online Reading Room e All Records documentados | Consulta e acesso a conteúdo não são licenças irrestritas para republicar descrições |
| BFI National Archive | https://www.bfi.org.uk/bfi-national-archive/search-bfi-archive | Busca pública de coleção documentada; parte das mídias livre no BFI Replay, outra parte presencial/restrita | Termos de reutilização de metadados não avaliados |
| Institut national de l'audiovisuel (INA) | https://catalogue.ina.fr/index/WEB-MEDIA/Inatheque | Interface pública especializada de consulta identificada | Acesso às obras e licença de metadados permanecem pendentes; índice histórico aponta 31 registros restritos |

Fontes adicionais: https://www.europeana.eu/en/rights/terms-of-use ; https://euscreen.eu/help/ ; https://americanarchive.org/legal/orr-rules ; https://www.bfi.org.uk/bfi-national-archive/inside-archive/bfi-national-archive-faq .

**Decisão:** nenhum novo registro incorporado; somente estados e evidências G1 do inventário. CC0 da Europeana e CC BY-SA do APE criam caminhos jurídicos **condicionais à proveniência e às exceções**, não dispensam validação científica por registro.

## Totais desta rodada
Foram atualizados **11 registros de corpora/unidades** no inventário (APE, CICLIC, Bundesarchiv, ASIM, BNFA, EFG, Europeana, EUscreen, AAPB, BFI e INA). Os demais permanecem classificados como não revalidados nesta migração.
