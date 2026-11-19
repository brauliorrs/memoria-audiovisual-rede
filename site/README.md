# MAR — nova aplicação pública

Este diretório inaugura a migração gradual da interface Streamlit para um **site Next.js**.

## Escopo da fase 1

- Catálogo central pesquisável e responsivo, 200 fichas **KAVI/Finna** previamente aprovadas para publicação de metadados;
- Fichas individuais em **200 URLs estáticas** `/acervo/kavi/<id>/`, com proveniência, SHA-256 e estados de revisão, direitos e reprodução;
- Pesquisa com filtro por década, tema/gênero, ordenação por título/ano e paginação incremental;
- Páginas próprias: \`/\`, \`/acervo/\`, \`/instituicoes/\`, \`/instituicoes/kavi/\`, \`/metodologia/\`;
- Rotas institucionais e estados de validação, sem promover conectores técnicos a acervos autorizados;
- Links na origem, sem vídeos, player, cookies de login ou API paga;
- Static export do Next.js, implantável em Vercel (preferencial) ou GitHub Pages (com basePath adaptado).
- **Não consulta Neon nem habilita P0/backup.**

O arquivo \`data/kavi-public.json\` contém uma projeção **reduzida** de fichas aprovadas. Seu manifesto de origem e hash ficam em \`../data/output/\`. Não editar manualmente este JSON. O script \`../scripts/check_mar_site_index.py\` verifica todos os 200 pares identificador/URL contra os originais assinados antes do build.

## Desenvolvimento

Requer Node.js 22+.

\`\`\`sh
cd site
npm install
npm run typecheck
npm run build
# Verifica também 200 rotas HTML de fichas individuais
npm run dev
\`\`\`

A verificação de proveniência na raiz exige apenas Python 3:

\`\`\`sh
python scripts/check_mar_site_index.py
python -m unittest discover -s tests -p 'test_mar_site_public_pages.py' -v
\`\`\`

## Vercel — projeto existente e domínio único

As atualizações deste site são implantadas **somente** no projeto Vercel existente `mar-public-site` (projeto `prj_ynSzKPjTZ4dvgermfa86UcyZN1ou`), usando o domínio canônico `https://mar-public-site.vercel.app/`.

- Não criar projeto ou domínio adicional para novos módulos ou publicações incrementais;
- Origem `brauliorrs/memoria-audiovisual-rede`, branch `main`, diretório `site`, framework Next.js;
- O fluxo de PR e a CI antecedem cada promoção. Quando o deploy Git do projeto existente não estiver vinculado, usar apenas uma implantação explícita no **mesmo projeto**, sem fingir que existe deploy automático;
- O Streamlit permanece ativo até a equivalência funcional e a validação do acesso público;
- Os produtos científicos agregados e os objetos de terceiros possuem critérios de publicação distintos. Os corpora sob HOLD não são liberados pela existência de telas no Vercel;
- A aplicação não necessita de APIs de IA, de APIs pagas ou de banco operacional para consultar os snapshots já publicados.

### Recursos de pesquisa migrados

- `/observatorio/`: panorama de corpora e instituições;
- `/temas/`: temas e cortes de país/plataforma **por fonte**;
- `/series/`: observações longitudinais históricas **por fonte**;
- `/comparar/`: nova bancada comparativa de até três fontes, gráficos temporais não sincronizados e exportação CSV **de agregados**, não de fichas individuais;
- `/instituicoes/pesquisa/`: fichas institucionais de pesquisa;
- `/acervo/`: catálogo de fichas KAVI que passaram pelo gate específico;
- `/casos/`: casos institucionais documentados.

## Sequência de migração

1. Fase 1: portal público estático e catálogo KAVI com auditoria de exportação.
2. Fase 2: exportações oficiais por corpus aprovadas, índice paginado e atualização versionada.
3. Fase 3: API, busca escalável e painel privado com OIDC; Neon apenas depois dos gates de recuperação P0.
4. Fase 4: transição gradual de URL, observabilidade e desativação controlada do Streamlit público.

**Não confundir o cadastro de um conector no motor universal com autorização de publicação.**

## Textos institucionais PT/EN/ES e SEO canônico (18/11/2026)

- Página inicial, apresentação institucional, KAVI, abertura das análises por fonte, legenda da nuvem de palavras e rodapé utilizam `components/institutional-i18n.tsx`. Somente textos editoriais são traduzidos; campos, nomes e links documentais mantêm sua forma original.
- `lib/seo.ts` registra títulos e descrições científicos em PT/EN/ES para **14 rotas institucionais e analíticas existentes**. O HTML estático da rota canônica permanece em **pt-BR** e o seletor cliente traduz a interface para inglês e espanhol.
- **Ainda não há indexação autônoma EN/ES:** não se emitem tags `hreflang` que apontem três línguas para a mesma URL. Essa etapa depende de versões HTML realmente renderizadas e endereçáveis por idioma, sem substituir as rotas legadas.
- Cada rota estática existente usa um `rel=canonical` próprio no domínio único `https://mar-public-site.vercel.app/`; perfis e fichas mantêm os identificadores de origem. O `sitemap.xml` inclui apenas páginas já existentes e, para itens audiovisuais individuais, exclusivamente as **200 fichas KAVI aprovadas**.
- `robots.txt` aponta somente ao mapa de URLs canônico; o mapa de URLs não constitui aprovação científica ou licença de acesso.
- Sem novas fichas, players, mídia, download, APIs pagas, coleta automatizada ou ligação operacional com o Neon. O Streamlit permanece ativo.
- Verificação: `npm run test:institutional-seo`, `npm run typecheck`, `npm run build` e contratos Python de publicação e proveniência.
