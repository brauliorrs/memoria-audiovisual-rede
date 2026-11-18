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

## Vercel

Criar um **novo projeto**, sem reutilizar \`mar-p0-recovery-lab\`, apontando para o repositório \`brauliorrs/memoria-audiovisual-rede\`, **Root Directory \`site\`**, framework **Next.js**. Usar Preview inicialmente. O app é estático nesta fase e não exige secrets. **Não transferir o domínio do Streamlit antes de um teste funcional no preview**.

O plano Hobby é permitido apenas para uso pessoal não comercial; confirmar enquadramento com os termos antes de uso institucional/comercial. Não é necessário contratar plano para desenvolver ou validar o MVP.

## Sequência de migração

1. Fase 1: portal público estático e catálogo KAVI com auditoria de exportação.
2. Fase 2: exportações oficiais por corpus aprovadas, índice paginado e atualização versionada.
3. Fase 3: API, busca escalável e painel privado com OIDC; Neon apenas depois dos gates de recuperação P0.
4. Fase 4: transição gradual de URL, observabilidade e desativação controlada do Streamlit público.

**Não confundir o cadastro de um conector no motor universal com autorização de publicação.**
