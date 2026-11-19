# MAR — Internacionalização do catálogo e do Índice de Dados Públicos

**Etapa:** 18/11/2026.  
**Site de destino:** somente `https://mar-public-site.vercel.app/` no projeto Vercel preexistente `mar-public-site`.  
**Streamlit e coletores:** inalterados. Nenhum acesso a banco, API externa ou serviço pago foi incorporado.

## Entregas

### Catálogo aprovado (`/acervo/`)

O módulo `site/components/catalog-search.tsx` usa o seletor de idioma atual (PT/EN/ES), aplicando traduções aos filtros por título, assunto, instituição, ID, década e gênero/tema, às opções de ordenação, resultados, paginação, ações dos cartões e avisos de reprodução não verificada.

**A seleção dos dados permanece inalterada:** filtro e ordenação processam apenas os **200 registros individuais KAVI/Finna presentes em `site/data/kavi-public.json`**, já aprovados para publicação de metadados. Títulos, gêneros, assuntos e IDs originais não são traduzidos artificialmente. Um campo de ano ausente continua ausente. A tradução não concede permissão de disponibilizar filmes ou thumbnails.

### Índice de acesso (`/indice-acesso/`)

A introdução, os números históricos, os filtros e os estados de classificação, as métricas por corpus, as mensagens de ausência de resultados e os avisos jurídicos são traduzidos.

**A separação epistemológica e jurídica permanece intacta:**
- 63 unidades/corpora históricos mapeados;
- 194.057 registros classificados historicamente, incluindo 165.134 rotulados como superfície pública observada e 28.923 como restritos;
- 200 fichas individuais KAVI já admitidas em catálogo separado;
- **0 fichas individuais adicionais publicadas pelo índice**; acesso à origem e classificação pública histórica não são licença de republicação.

`item.humanAccessNote`, `corpus.restrictionEvidence`, nomes, códigos de fontes e categorias científicas preservam o conteúdo original, mesmo ao mudar o idioma. O site explica que esses elementos são documentos históricos no idioma em que foram coletados. *Não* traduzir testemunhos ou afirmações específicas sem revisão documental.

### Estratégia técnica e testes

Reutiliza-se `site/components/scientific-i18n.tsx` sem adicionar novas dependências. Novas chaves PT/EN/ES têm paridade verificada pelo teste Node `site/tests/scientific-i18n.test.cjs`; testes Python estão em `tests/test_mar_catalog_access_i18n.py`, além dos contratos de publicação existentes. A CI valida o build estático do Next.js, `/acervo/` e `/indice-acesso/`.

A ampliação **não altera** o Streamlit, os CSVs de origem, o Neon, a camada de autorização científica ou o padrão de navegação do portal.

## Ainda pendente

- Tradução editorial da ficha individual de filme `/acervo/kavi/[id]/` e de outras páginas institucionais legadas, preservando títulos originais.
- Políticas de direitos, licenças e evidências de origem em outros idiomas somente com revisão humana verificável.
- Metadados SEO e URLs indexáveis multilíngues; auditoria visual de layouts e acessibilidade.
- Outros módulos científicos/operacionais do Streamlit que ainda não possuem paridade no Next.js.

**A tradução do catálogo e do índice não significa migração integral do Streamlit.**
