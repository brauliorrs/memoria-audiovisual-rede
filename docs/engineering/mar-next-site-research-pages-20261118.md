# MAR Web — fichas individuais e pesquisa facetada (18/11/2026)

## Contexto
A primeira versão Next.js `site/` está integrada na main, com 200 registros KAVI/Finna aprovados para publicação de metadados sob manifesto SHA-256, mas pesquisa reduzida e sem URLs individuais. O Vercel tem deployment inicial estável num commit anterior ao merge; o Streamlit permanece disponível. Este incremento é frontend/índice público **sem alterar CSV, manifesto, Neon, OIDC, backups nem política P0**.

## Decisão de produto e arquitetura
1. Oferecer **uma página por ficha KAVI**, com URL estática `/acervo/kavi/<id>/` gerada em build com `generateStaticParams`, título, ID original, ano, gêneros, assuntos, língua exatamente como metadados existentes, fonte institucional, status documental e links à origem. Nenhum player, download ou conteúdo audiovisual.
2. Pesquisa central e a página institucional compartilham o **mesmo componente/índice**, com busca textual accent-insensitive por título, assunto, gêneros, ID, instituição, país e ano; filtros por década e tema/gênero extraídos somente dos dados aprovados; ordenação por título/ano (sem alterar origem dos dados), retorno de total filtrado e paginação incremental.
3. Explicitamente indicar **escopo atual**: uma instituição com fichas indexadas, 200 registros, cobertura parcial, direitos e reprodução **não verificados**. Não sugerir que os outros conectores já possuam fichas aprovadas ou que há mais de um corpus publicado.
4. No índice de origem KAVI, não duplicar IDs/URLs nem inventar direitos; reaproveitar `scripts/check_mar_site_index.py` como gate. Não criar políticas de importação genérica sem manifesto aprovado.
5. Criar testes contratuais de rotas, links institucionais e campos documentais que impeçam alterações inadvertidas; no CI, gerar as 200 páginas de ficha e checar ao menos uma rota de exemplo; compilar Next.js.
6. **Sem implantação na URL principal do MAR**, migração Neon, alterações em P0, agendamento de coleta, domínio ou custo novo. Homologar no projeto Vercel separado depois de CI verde.

## Critérios mínimos
- [ ] 200 rotas de registro a partir de 200 IDs verificados, sem conflitos e com links https de origem.
- [ ] Pesquisa filtrável por termo, década e gênero e ordenável; estado vazio amigável.
- [ ] Ficha preserva os estados de origem/documental/reprodução sem falsas garantias.
- [ ] CI `MAR Next.js Site` e `Quality Checks` verde no HEAD e pós-merge.
- [ ] Deploy e teste HTTP/visual em URL separada; Streamlit mantido.
