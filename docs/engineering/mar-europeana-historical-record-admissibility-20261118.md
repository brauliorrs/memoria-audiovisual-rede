# MAR — Parecer técnico de elegibilidade: Europeana (20 registros históricos)

**Data de apuração:** 18/11/2026 · **Decisão:** HOLD — nenhuma autorização de publicação científica emitida.

## Material efetivamente auditado
- `data/output/europeana_catalogo_videos_analitico.csv` · SHA-256 `a6aa7ee8a2ce02667932a854a695ff5a26a16754d42c9cc2d9ab6f52a8c8978e`.
- **20/20** linhas inspecionadas por regra determinística, identificadores `/item/<dataset>/<id>` extraídos de 20 links Europeana distintos; nenhuma duplicata exata no snapshot.
- Anomalias não mutuamente exclusivas: **7** registros sem tipo audiovisual comprovado no campo de tipo histórico; **10** títulos ausentes/genéricos; **20** registros exigem revisão independente da declaração dos direitos do objeto.
- Direitos do objeto declarados na descrição histórica: 3 menções CC BY-SA; 1 menção CC restritiva; 3 direitos/copyright restritivos; 1 declaração diversa; **12 sem declaração**. As descrições são históricos não revalidados.
- Item de 566/urn___mint_think_code_io_europeana_cyprus_AMAYN013 contém texto de restrição em grego, e item do INA tem copyright reservado; tais direitos se referem ao **objeto**, não invalidam automaticamente CC0 dos metadados da Europeana.
- Há itens identificados como `Image`, `Text`, `Monograph`, `film stills` etc. Não classificá-los como filmes sem confirmação externa.
- Tentativas de abertura externa de três fichas individuais foram limitadas pela ferramenta web. **Não** afirmar indisponibilidade dos itens ao público.

## Licença e rastreabilidade
- Regra oficial: metadados publicados pela Europeana em CC0: https://www.europeana.eu/en/rights/usage-guidelines-for-metadata
- Termos distinguem metadados de miniaturas e conteúdos: https://www.europeana.eu/en/rights/terms-of-use
- Os metadados da Europeana, inclusive via API, são documentados em CC0: https://europeana.atlassian.net/wiki/spaces/EF/pages/2360508417/API+FAQ
- **Não** inferir licença CC0 sobre o objeto digital. A aplicação a uma ficha exige confirmar se os campos foram de fato publicados como metadados da Europeana, revisar fonte, provedor, mudanças e sensibilidade.
- A página de origem e o provedor constam dos registros históricos, mas o link de cada ficha e as licenças atuais ainda exigem comparação na origem.

## Decisão formal do motor de admissibilidade
`hold_scientific_and_item_source_review` — **nenhuma ficha elegível automaticamente**. A política CC0 torna a reutilização de metadados plausível, mas não resolve tipologia audiovisual, qualidade de títulos, proveniência atual, documentação científica e aprovação independente.

## Para futura liberação
1. Reabrir cada uma das 20 fichas na origem ou via interface oficial/documentada, sem burlar controles; registrar data, resultado e identificador.
2. Conferir campos e provedor; corrigir/segregar itens de imagem, texto ou monografia.
3. Separar direitos de metadados, miniaturas e objeto digital, documentar alterações e creditar fontes.
4. Revisor científico independente aprovar registro e conjunto; registrar manifesto de aprovação assinado, com versão e SHA-256 dos dados autorizados.
5. Somente uma etapa de promoção separada e submetida à CI poderá criar as fichas no catálogo público.

**Assinatura científica:** não emitida. **Aprovação jurídica individual:** não emitida. **Publicação:** proibida nesta etapa.
