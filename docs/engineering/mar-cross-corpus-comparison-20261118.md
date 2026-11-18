# MAR — comparação científica de corpora no Next.js

**Etapa de migração:** 18/11/2026. **Nova interface:** `/comparar/` no mesmo projeto `mar-public-site`. **Fonte de verdade:** as projeções versionadas `site/data/research-slices-0.json` a `-15.json`, construídas anteriormente a partir de `data/output/*_tema_pais.csv`, `*_tema_plataforma.csv` e `*_linha_do_tempo_corpus.csv`. Nenhum crawler, banco ou endpoint de terceiros é chamado pelo navegador.

## Perguntas que a interface permite investigar

1. Quais **temas** aparecem em mais de uma das duas ou três fontes selecionadas? Quais se destacam proporcionalmente *dentro de cada fonte*?
2. Qual a distribuição observada por **país** ou por **plataforma** nas fontes escolhidas? As dimensões são separadas: **não calcular país×plataforma** na ausência desse cruzamento original.
3. Como evoluiu um indicador institucional ou de visibilidade **em cada fonte**, segundo suas próprias datas de coleta? Cada gráfico preserva seu eixo histórico; a simultaneidade de coleta entre fontes não é pressuposta.
4. Como extrair um **recorte reprodutível em CSV** de contagens agregadas e caminhos dos arquivos originais?

## Garantias metodológicas

- Máximo de três corpora selecionados, sem repetição. Todas as fontes presentes no inventário analítico são opções; corpora sem indicador para uma dimensão exibem a ausência.
- Contagens por tema derivam de `tema_plataforma` e, quando vazia, `tema_pais`; contagens por país derivam de `tema_pais`, por plataforma de `tema_plataforma`. **Não somar país e plataforma entre si** nem inferir relações ausentes.
- Cada fonte possui **seu próprio denominador** (total das ocorrências classificadas naquela dimensão). As células da tabela exibem contagem e percentual dentro de cada fonte, não quota representativa da produção audiovisual mundial.
- Rótulos são mantidos no idioma da origem. O mesmo termo pode ser classificado de forma distinta por corpora diferentes; nomes semelhantes não passam por reconciliação semântica automática.
- Na evolução temporal, o eixo representa **observações de coleta**, não o ano de produção das obras. Fontes podem ter séries e calendários distintos. Uma única observação não sustenta inferência de tendência.
- Cada CSV é gerado no navegador somente quando solicitado: fonte, dimensão, rótulo agregado, contagem, percentual local, denominador e arquivo de proveniência; a série contém data, indicador, valor e fonte. O exportador **escapa caracteres especiais e neutraliza fórmulas** para planilhas.
- Nenhum título de obra, autor, identificador de item, imagem, URL de mídia ou metadado individual bloqueado é publicado. Dados históricos sob HOLD permanecem somente como estatística.
- Interfaces PT/EN/ES na bancada; nomenclatura científica original preservada.

## Equivalência e implementação

- Código de cálculo e CSV: `site/lib/corpus-comparison.ts`.
- Interface responsiva: `site/components/corpus-comparison.tsx`.
- Rota: `site/app/comparar/page.tsx`.
- Teste documental e contratos da exportação: `tests/test_mar_cross_corpus_comparison.py`, executado pela CI `MAR Next.js Site`.
- Portas de navegação: homepage, observatório, análises e cabeçalho.
- O fluxo preserva as 200 fichas KAVI aprovadas e não altera `app/streamlit_app.py` nem bancos/coletores.

## Próximos incrementos

Construir um sistema pesquisável de hipóteses/recortes científicos com URLs reproduzíveis, ampliar a tradução das páginas legadas PT/EN/ES, adicionar mapas territoriais só a partir de coordenadas verificadas, melhorar acessibilidade e integração operacional. A substituição definitiva do Streamlit depende da matriz de paridade funcional e dos gates de operação; esta etapa **não** constitui migração total.
