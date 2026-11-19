# MAR — Textos institucionais e SEO multilíngue (18/11/2026)

## Escopo entregue
- Tradução editorial PT/EN/ES para homepage, apresentação institucional, KAVI/Finna, nuvem agregada de títulos, rodapé e notas de integridade. O dicionário é revisável e separado dos metadados de fontes.
- Links e rotas de pesquisa, comparação, catálogo, metodologia e fontes preservados, assim como os 200 registros KAVI autorizados e os bloqueios para as demais fontes.
- Origem oficial única: https://mar-public-site.vercel.app/ (projeto Vercel existente mar-public-site). Nenhum projeto ou domínio Vercel adicional.
- Fonte científica preservada: títulos originais, nomes institucionais, identificadores, categorias de origem, datas, URLs, direitos e hashes SHA-256 permanecem inalterados.

## SEO realista em exportação estática
- A entrada PT permanece em /; adicionam-se duas entradas de apresentação documental com HTML localizado, /en/ e /es/. Não substituem nem redirecionam as rotas existentes.
- Canonical, título, descrição e Open Graph configurados nas páginas de pesquisa, catálogo, metodologia, instituições e perfis. URLs específicas por fonte e ficha KAVI ganham canonical individual.
- hreflang pt-BR, en e es, e x-default são publicados somente nas três entradas equivalentes /, /en/, /es/, que possuem HTML realmente indexável.
- As páginas analíticas e fichas existentes alternam idioma no cliente. NÃO são falsamente apresentadas como rotas de idiomas distintas para indexação; o SEO de cada subpágina por idioma continua etapa separada.
- sitemap.xml publica páginas de pesquisa e somente 200 URLs individuais do lote KAVI admitido; perfis de outras instituições não são inseridos como fichas de obras. robots.txt aponta para esse sitemap do mesmo domínio.
- A indexação por mecanismos externos, manutenção em cache ou uso de metadados por terceiros não demonstra autorização de reprodução audiovisual.

## Critérios de aceite
- Rodar npm run test:editorial-seo, npm run test:scientific-i18n, npm run test:kavi-detail, npm run typecheck, npm run build, mais gates Python da CI.
- Inspecionar no build estático out/index.html, out/en/index.html, out/es/index.html, out/sitemap.xml, out/robots.txt e as 200 rotas originais KAVI.
- A revisão visual em desktop/celular e a verificação de produção devem ocorrer no único projeto mar-public-site, após CI verde e merge.

## Pendências reconhecidas
- Revisão humana de textos históricos/documentais originais sem adulterar a fonte.
- HTML indexável trilíngue de cada ficha e painel, com permalinks próprios, caso justificado editorialmente.
- Validação de publicação efetiva no Vercel, acessibilidade e ferramentas de indexação (nenhuma configuração de serviços pagos nesta etapa).
- O Streamlit permanece operacional; esta entrega não declara migração funcional completa.
