# MAR — Evidências externas e decisão de homologação (18/11/2026)

> **Atualização posterior (18/11/2026):** a URL Eye anteriormente não verificada foi aberta com sucesso navegando pela filmografia oficial da produtora. Houve ampliação para 7 fichas Eye e 7 Czech, todas localizadas. Consulte `mar-multicorpus-expanded-sample-20261118.md` e a decisão JSON atualizada. O relato abaixo permanece como evidência histórica da primeira tentativa, não como estado atual.


## Escopo
Auditoria de 2 URLs Eye e 2 URLs Czech Television presentes nos CSVs históricos de julho de 2026. Inspeção pública de HTML/metadados documentais; não reproduz mídia, não testa licença e não faz coleta incremental. Os workflows `MAR Multicorpus Staging` (44358253929) e `Quality Checks` (44358254086) concluíram com sucesso no PR #105, executando Eye, depois Czech, e integridade KAVI.

## Eye Filmmuseum — verificação externa
1. `https://filmdatabase.eyefilm.nl/en/collection/film-history/film/als-het-verleden-spreekt`: a tentativa de abrir a ficha específica retornou erro no verificador web (inclusive com barra final). A obra aparece no catálogo e em uma filmografia do Eye, mas a **URL exata não foi confirmada acessível**. Resultado: `hold_url_unverified`.
2. `https://filmdatabase.eyefilm.nl/en/collection/film-history/film/and-a-table`: ficha acessível, título `...And a Table`, ano de produção 1971, registro audiovisual com player condicionado a consentimento de cookies. O CSV histórico não contém esse ano; **não preencher automaticamente esse campo por inferência sem revisão da origem**. Resultado: `documentary_metadata_confirmed_rights_unverified`.

## Czech Television — verificação externa
1. `https://www.ceskatelevize.cz/porady/15109272875-ct-na-mff-karlovy-vary/226544160080005/`: título `5/8 Festivalové vteřiny`, 8 min, produção 2026, categorias de cultura/festival. Resultado: `documentary_metadata_confirmed_rights_unverified`.
2. `https://www.ceskatelevize.cz/porady/1097206490-udalosti-v-kulture/226411000120707/`: título `7. července`, 14 min, produção 2026, programação de cultura; segmentos do episódio listados na origem. Resultado: `documentary_metadata_confirmed_rights_unverified`.

## Links de verificação
- Eye ficha #2: https://filmdatabase.eyefilm.nl/en/collection/film-history/film/and-a-table
- Eye filmografia contextual: https://filmdatabase.eyefilm.nl/en/collection/film-history/company/nationale-filmfabriek-bloemendaal
- Czech #1: https://www.ceskatelevize.cz/porady/15109272875-ct-na-mff-karlovy-vary/226544160080005/
- Czech #2: https://www.ceskatelevize.cz/porady/1097206490-udalosti-v-kulture/226411000120707/

## Decisão de gates
| Corpus | CI técnica | URLs documentais piloto | Publicação de metadados | Decisão |
|---|---|---|---|---|
| Eye | PASS | 1 acessível; 1 não verificada | sem autorização específica | HOLD |
| Czech | PASS | 2 acessíveis | sem autorização específica | HOLD |

**Conferir uma ficha no site institucional não demonstra licença para republicar metadados, completude, direitos de mídia nem estabilidade geral do corpus.** Uma eventual reprodução pública indicada no site de origem não autoriza incorporação de player. Não há autorização científica/humana emitida nesta etapa, nem aprovação de publicação por corpus. As duas fontes permanecem candidatas técnicas apenas.

## Para solicitar liberação posterior
- Eye: resolver a ficha não verificável (revisão manual, atualização de URL, redirecionamento e nova amostragem estratificada).
- Czech: testar amostras adicionais de diferentes programas e datas, estados de acesso/restrição e colisões de ID.
- Ambos: revisar integridade/duplicatas do conjunto completo, documentar permissões sobre metadados, limites de cobertura e registrar autorização formal assinada no gate específico; somente então construir índice e rotas em Preview.

## Invariantes
KAVI continua com 200 fichas aprovadas; `site/data`, `app/streamlit_app.py`, snapshots científicos congelados e PostgreSQL/Neon não foram alterados por esta auditoria.
