# MAR — Parecer técnico de elegibilidade: Archives Portal Europe (412 registros históricos)

**Data de apuração:** 18/11/2026 · **Decisão:** HOLD — não publicar as 412 entradas como fichas do APE.

## Material efetivamente auditado
- `data/output/ape_catalogo_videos_analitico.csv` · SHA-256 `78de164d22d75e4e1117f06e76cc995f55979e89838f6ff141327bf07fcb9f68`.
- **412/412** linhas analisadas. **396** links exatos distintos de mídia externa; **16** ocorrências adicionais de links repetidos.
- Todas as 412 linhas apontam a plataformas externas, e **não** a uma página individual de item arquivístico APE: YouTube (incl. `youtu.be`, `m.youtube`), Vimeo, Instagram, Facebook ou Internet Archive.
- O `repository_code` e `ape_detail_url` vinculam a linha a uma **busca/página de instituição**, mas **não** identificam um item arquivístico específico.
- As 412 linhas não fornecem identificador de item arquivístico APE independente; **141** títulos ausentes/genéricos na classificação do auditor.
- O mecanismo extraiu identidades de vídeos YouTube/Vimeo quando possível. Detectou 100 linhas em grupos de identidades duplicadas após ignorar parâmetros de incorporação; isso é indicador de revisão, **não** 100 vídeos duplicados adicionais únicos.
- Nenhuma licença de mídia externa foi confirmada; todos os 412 registros foram classificados `third_party_object_rights_unverified`.

## Licença e limite do escopo
- https://www.archivesportaleurope.net/metadata-usage-guidelines/ publica regra geral CC BY-SA 4.0 **para metadados publicados no APE**, salvo indicação em contrário.
- https://www.archivesportaleurope.net/terms-of-use/ esclarece responsabilidades dos provedores e conteúdos digitais.
- As obrigações incluem atribuição aos detentores e agregadores, referência às licenças, mudanças documentadas e compartilhamento nas condições incidentes.
- A presença de um vídeo de terceiros na página de uma instituição mapeada pelo APE **não faz daquele vídeo um registro descritivo APE nem o licencia CC BY-SA**. Aplicar a política aos 412 vídeos seria erro de proveniência e direitos.

## Decisão formal do motor de admissibilidade
`hold_reclassify_external_media_inventory`: preservar as 412 entradas **como inventário histórico de pistas externas** separado das fichas científicas e do índice de metadados republicáveis. Não chamá-las de 412 fichas de vídeo do APE nem exibi-las individualmente como catalogadas/validadas.

## Para futura liberação
1. Pesquisar em APE, como visitante comum, pelo código de instituição e pelos identificadores arquivísticos reais; documentar a associação **item a item**, e não apenas institucional.
2. Distinguir item arquivístico APE de mídia externa que por acaso integra a página da instituição.
3. Para cada metadado publicado no APE, documentar a licença específica ou exceção, atribuições e transformação efetuada.
4. Revalidar os links de mídia externa **somente como caminhos de acesso**, sem download, incorporação ou inferência de direitos.
5. Concluir revisão científica independente e manifesto de autorização segregado antes da promoção.

**Assinatura científica:** não emitida. **Aprovação jurídica individual:** não emitida. **Publicação:** proibida nesta etapa.
