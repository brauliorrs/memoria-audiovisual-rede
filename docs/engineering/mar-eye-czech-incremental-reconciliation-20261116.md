# MAR — Reconciliação incremental Eye e validação documental Czech Television (16/11/2026)

## Auditoria de impacto anterior ao código
Base: main `42a2cd70f401eb33d48a5340952f37979235b09c`. O PR #95 implementa a porta de admissão; o PR #94 implementa navegação KAVI; o PR #93 continua com gates P0 em HOLD. Este incremento não depende de merge desses PRs.

### Estado comprovado
- Eye: `data/output/eye_catalogo_videos_analitico.csv`, 630 registros no snapshot histórico de 15/07/2026. URLs são fichas institucionais `filmdatabase.eyefilm.nl`, não mídia armazenada.
- Czech Television: adaptador `parse_czech_television_catalog_page` / `parse_czech_television_show_page` / `parse_czech_television_episode_page`; testes offline, sem snapshot publicado em `main`.
- Não existe evidência de novas páginas capturadas nesta alteração. Este incremento é **reconciliação e inspeção de evidências OFFLINE**, não uma coleta autorizada.

### Impacto e limites
- Novo módulo puro de reconciliação de fichas Eye: comparação por URL/identidade institucional, nunca título; distingue `new`, `changed`, `unchanged`; faltantes são `not_observed` e não exclusão.
- Nova triagem de um episódio Czech parseado offline, usando `parse_czech_television_episode_page` como adaptador existente; nunca presume reprodução atual nem gera URL a partir de IDs.
- Novo script local somente-leitura que recebe evidência JSON exportada manualmente do probe e lê o CSV Eye histórico existente; escreve relatório JSON exclusivamente em stdout, sem gravar no catálogo, DB ou cache.
- Dados candidatos não podem trazer URL direta de stream, domínio externo, credenciais ou query/fragment. Referências e tamanho da amostra são declarados, não se inferem.
- `CORPORA`, app Streamlit, `data/output` históricos, jobs e segredos não são alterados.

### Plano de testes (antes do código)
R1 — Eye: ID/url já existente, descrição idêntica -> unchanged; descritor alterado -> changed; nova URL no domínio permitido -> new.
R2 — Títulos iguais com URLs diferentes preservam identidade; URL duplicada ou ID duplicado no candidato é rejeitada.
R3 — Conjunto incompleto jamais declara remoção: baseline não vista -> not_observed, mesmo quando candidato declara total remoto.
R4 — Query/fragment, stream mp4/m3u8/mpd, host alheio e esquemas inseguros -> reject.
R5 — Czech: um episódio com URL oficial e campos de `mediaMeta`, comprovante offline `isPlayable` obtido na resposta -> candidate_for_review somente; sem player, publicação nem direitos presumidos; episódio sem resultado -> HOLD.
R6 — Fonte Eye existente não é escrita; novos relatórios jamais geram manifestos de publicação `mar_admitted` e não entram no catálogo público.
R7 — SHA de evidência JSON e código de corpus identificados; divergência bloqueia saída.
R8 — CI, testes históricos Eye e Czech e qualidade geral passam. Sem network.
Rollback: remover módulo, script, testes e este documento. Sem efeitos sobre bancos, acervo publicado ou outras branches.
