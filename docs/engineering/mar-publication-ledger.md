# MAR — Diário permanente de publicações incrementais

Este diário registra cada liberação no repositório, independentemente da memória do chat. A entrada deve distinguir quatro estados: **integrado no GitHub**, **implantado**, **acessível ao público sem login** e **autorizado cientificamente**. Nenhum estado implica automaticamente os demais.

## 2026-11-18 — Índice de Dados Públicos do Observatório

- PR: https://github.com/brauliorrs/memoria-audiovisual-rede/pull/106
- Merge commit na `main`: `2f3c30c7023ea05a22e7497e5e2ef7ac278a98d6`
- CI no commit do PR: MAR Next.js Site, Quality Checks e auditoria APE/Europeana aprovados.
- Vercel: projeto `mar-public-site`, deployment `dpl_G2FH4HDr5JUjNvdDiiyP5F3XNz5A`, ambiente `production`, status `READY`.
- URL prevista: https://mar-public-site.vercel.app/indice-acesso/
- **Acesso anônimo NÃO confirmado**: a configuração Vercel informa SSO habilitado nos domínios vercel.app. Não confundir READY com acesso livre; não desativar proteção sem revisão da configuração.
- Integrado: inventário de 63 corpora/unidades com motivos de não exibição, evidências humanas disponíveis e levantamento histórico de 194.057 registros classificados. Esses números não são novos registros publicáveis.
- Fichas públicas aprovadas: as mesmas 200 KAVI/Finna.
- Fichas adicionais publicadas: **zero**.
- Europeana: 20 linhas auditadas; pesquisa e classificação de direitos e tipologia em HOLD.
- APE: 412 linhas auditadas; links externos, não IDs de itens arquivísticos do APE; HOLD.
- Eye/Czech: PR #105 permanece segregado, sem liberar metadados.
- Streamlit, dados científicos congelados e Neon: inalterados.

## Requisitos da próxima entrega

Cada incremento deve conter data, corpus, fontes, evidência de acesso pelo navegador, situação de direitos, revisão científica, manifestação de autorização, PR/commit/CI, URL de implantação e estado de acesso anônimo. O registro deve dizer expressamente quando **somente a instituição foi identificada**, quando **uma ficha foi observada na origem** e quando **há permissão de republicar metadados**, sem confundir essas categorias.

Nenhuma ficha sujeita a HOLD pode ser promovida por um merge técnico.
