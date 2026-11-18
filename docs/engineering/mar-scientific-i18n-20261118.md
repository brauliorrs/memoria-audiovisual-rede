# MAR — Migração PT/EN/ES do núcleo editorial científico

**Etapa:** 18/11/2026. **Superfície:** projeto Vercel preexistente `mar-public-site` (domínio `https://mar-public-site.vercel.app/`). O Streamlit, corpora científicos congelados, coletores, Neon e direitos de publicação permanecem inalterados.

## Cobertura implementada

- `/observatorio/`: introdução, explicação de amostragem, filtros, indicadores, tabela de 63 fontes, grupos territoriais e nota de direitos em português, inglês e espanhol. Contagens usam o formato numérico do idioma; nomes e categorias institucionais de origem são conservados.
- `/analises/`: introdução, filtros, ordenação, cabeçalhos e cautelas científicas dos **62 relatórios** traduzidos; dados numéricos e códigos não se alteram.
- `/observatorio/[code]/`: rótulos e avisos dos **63 perfis documentais** traduzidos, com percentuais por idioma. Observações sobre o acesso, revisão de direitos e outras evidências específicas de cada instituição mantêm-se **literalmente no idioma do inventário original** e são identificadas como tal.
- `site/components/corpus-historical-analytics.tsx`: painéis de integridade, websites, plataformas e indicadores por corpus traduzidos; rótulos próprios de fontes preservados.
- `/metodologia/`: quatro princípios de proveniência, revisão científica, ausência de hospedagem de mídias e expansão controlada traduzidos.
- `/casos/`: introdução, busca, botões e textos metodológicos dos **17 estudos de caso** traduzidos; descrições de evidências e passos de investigação são mantidas no idioma documental de origem para não reinterpretar seus fatos automaticamente.
- `/instituicoes/pesquisa/[source]/[entry]/`: rótulos das fichas individuais institucionais traduzidos, sem tradução artificial de nomes, códigos ou tipos de origem.
- `/acervo/`: introdução do catálogo autorizado traduzida; a interface de busca e as fichas documentais ainda exigem trabalho adicional.

A tradução está concentrada no componente cliente `site/components/scientific-i18n.tsx` e utiliza o seletor já existente `useSiteLocale()`, sem instalar provedores, APIs pagas, pacotes extras nem criar projetos Vercel paralelos. A página original é renderizada em PT, e o idioma selecionado é aplicado na experiência do navegador; metadata SEO estática ainda possui rótulos portugueses em parte das rotas.

## Integridade

A camada de tradução transforma **texto editorial e formatação numérica**, nunca os valores numéricos científicos, nomes próprios, contagens congeladas ou autorização de publicação. O snapshot histórico possui 194.057 registros classificados em 63 corpora; **somente as mesmas 200 fichas KAVI** continuam publicadas individualmente. Não há disponibilização de mídia, players, download de filmes ou nova ficha de fontes sob HOLD.

Cada idioma tem o mesmo conjunto de chaves; os testes validam paridade de vocabulário, notas de direitos, números regionalizados e ausência de alterações nos limites de publicação. CI:
```sh
cd site
npm run test:scientific-i18n
npm run typecheck
npm run build
cd ..
python3 -m unittest discover -s tests -p test_mar_scientific_i18n.py -v
```

## Lacunas deliberadamente pendentes

1. Internacionalizar filtros detalhados do catálogo KAVI, fichas de itens, tabela do índice de acesso, recursos de pesquisa e navegação institucional que ainda possuem strings fixas.
2. Decidir revisão humana/tradução atestada para evidências documentais de fontes, evitando atribuir traduções geradas como se fossem documentos originais.
3. Adicionar URLs indexáveis por idioma e metadados SEO traduzidos, sem perder rotas existentes; avaliar acessibilidade e interface móvel por idioma.
4. Completar matriz funcional do Streamlit antes de considerar encerrá-lo.

Não declarar internacionalização completa até esses itens serem verificados.
