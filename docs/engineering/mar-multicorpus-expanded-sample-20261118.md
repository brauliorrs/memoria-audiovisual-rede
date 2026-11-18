# MAR — Amostragem externa ampliada: Eye e Czech Television (18/11/2026)

**Natureza:** auditoria documental manual de páginas oficiais de origem. Não é validação de licença de republicação de metadados, não é teste de reprodução audiovisual, não é revisão completa do corpus e não incorpora fichas ao site público.

## Recuperação da URL anteriormente pendente (Eye)
- URL original do CSV: https://filmdatabase.eyefilm.nl/en/collection/film-history/film/als-het-verleden-spreekt
- Evidência: navegação pela filmografia da própria Nationale Filmfabriek Bloemendaal, na página https://filmdatabase.eyefilm.nl/en/collection/film-history/company/nationale-filmfabriek-bloemendaal ; o link oficial chega à ficha exata (rota inglesa), confirmando título original **... Als het verleden spreekt**, **1921**, gênero publicidade e produtora. Também acessível na variante neerlandesa https://filmdatabase.eyefilm.nl/collectie/filmgeschiedenis/film/als-het-verleden-spreekt
- Conclusão: **URL documentada e resolvida**. A falha anterior foi de acesso pela ferramenta, não comprova uma ruptura institucional do link. **Não substituir o URL do CSV original nem alterar identidade hash do registro.**

## Eye — 7 fichas oficiais conferidas

| Título no CSV | URL | Observação |
|---|---|---|
| ... Als het verleden spreekt | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/als-het-verleden-spreekt | Confirmado por link interno da filmografia; ano de produção 1921 |
| ...And a Table | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/and-a-table | Confirmado; ano de produção 1971 |
| 1 April viering in een grote stad | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/1-april-viering-in-een-grote-stad | Ficha identificada |
| 1 Mei viering van de SDAP, De | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/de-1-mei-viering-van-de-sdap | Ficha identificada sob título em ordem natural |
| 25-Jarig regeringsjubileum van koningin Wilhelmina | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/25-jarig-regeringsjubileum-van-koningin-wilhelmina | Ficha identificada |
| 5e Episode | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/5e-episode | Ficha identificada |
| Aankomst Circus Carré | https://filmdatabase.eyefilm.nl/en/collection/film-history/film/aankomst-circus-carr%C3%A9 | Ficha identificada; URL com caractere percent-encoded |

**Limites:** o CSV Eye omite ano de produção nas linhas amostradas; a ausência não é zero ou negativa. Não transpor datas das fichas sem revisão específica e trilha de proveniência. O texto da plataforma sobre cookies para reprodução não comprova direito de republicação de metadados nem acesso real de mídia.

## Czech Television — 7 fichas oficiais conferidas

| Título | URL | Tipo |
|---|---|---|
| 5/8 Festivalové vteřiny | https://www.ceskatelevize.cz/porady/15109272875-ct-na-mff-karlovy-vary/226544160080005/ | festival |
| 7. července | https://www.ceskatelevize.cz/porady/1097206490-udalosti-v-kulture/226411000120707/ | atualidades culturais |
| Zahájení 60. ročníku MFF Karlovy Vary | https://www.ceskatelevize.cz/porady/15109272875-ct-na-mff-karlovy-vary/226411033400703/ | abertura do festival |
| 6. července | https://www.ceskatelevize.cz/porady/1097206490-udalosti-v-kulture/226411000120706/ | atualidades culturais |
| Večer lidí dobré vůle – Velehrad 2026 | https://www.ceskatelevize.cz/porady/14728574567-vecer-lidi-dobre-vule-velehrad/32629838006/ | concerto |
| 10/10 Zákupy | https://www.ceskatelevize.cz/porady/13826669737-skryte-skvosty/425235100031010/ | documentário |
| Malá hvězda nezapadá | https://www.ceskatelevize.cz/porady/10123383458-pribehy-slavnych/413235100211002/ | documentário biográfico |

**Distinção crítica:** campos `video_date_display` e `video_published_at` do CSV não demonstram, por si, o **ano de produção** da obra. O importador técnico atual chama seu campo derivado `year`; esse mapeamento necessita correção de nomenclatura ou campo de data específico antes de qualquer projeção pública.

## Avaliação e limites da amostra
- Eye: 7/7 páginas documentais localizadas; inclui a URL anteriormente pendente.
- Czech: 7/7 páginas documentais localizadas; títulos correspondem aos registros selecionados.
- Amostra: intencional e não probabilística, composta dos primeiros registros e casos documentais adicionais; **não prova qualidade, cobertura, acessibilidade ou direitos do dataset completo**.
- Não houve coleta sistemática de redirecionamentos HTTP/códigos de resposta, checagem multimodal, auditoria de direitos/licenças ou amostragem estatística do conjunto completo.
- Não houve alteração de CSVs científicos, autorização de publicação ou validação das 630 fichas Eye históricas.

## Decisão
A pendência da **URL Eye foi sanada**, mas **Eye e Czech permanecem em HOLD para publicação**. A autorização exige revisão integral de duplicatas e links, amostragem estratificada e reprodutível por período/tipo, confirmação de permissões de publicação de metadados e documento de aprovação por corpus. O Streamlit segue mantido e o catálogo Next.js continua exclusivo às 200 fichas KAVI previamente aprovadas.
