# Backlog de arquitetura visual e responsividade

## Objetivo

Reduzir a poluição visual do observatório e reorganizar a interface para favorecer leitura progressiva, navegação vertical e uso confortável em celulares, tablets e telas de diferentes larguras.

A revisão não deve ser tratada apenas como mudança estética. Ela envolve arquitetura da informação, hierarquia visual, responsividade, densidade de dados e escolha adequada do componente de apresentação.

## Diagnóstico atual

- excesso de informações simultâneas na mesma tela;
- muitos blocos, métricas e tabelas distribuídos horizontalmente;
- percurso excessivamente lateral e pouco orientado à rolagem vertical;
- tabelas extensas com grande número de colunas;
- leitura prejudicada em celulares e tablets;
- pouca diferenciação entre informação principal, informação contextual e detalhe técnico;
- seções densas apresentadas integralmente antes de o usuário solicitar aprofundamento;
- risco de o volume visual ocultar a narrativa científica da plataforma.

## Princípio central

> Sempre que uma seção apresentar corpus extenso, grande volume de campos ou conteúdo analítico denso, a organização padrão deverá ser vertical.

O usuário deve compreender a informação avançando de cima para baixo. A disposição horizontal deve ser reservada a comparações curtas, métricas sintéticas ou grupos pequenos de elementos que permaneçam legíveis em telas estreitas.

## Regras de layout

### 1. Fluxo vertical como padrão

- organizar seções extensas em sequência vertical;
- limitar o número de colunas simultâneas;
- evitar painéis largos com múltiplas áreas competindo pela atenção;
- priorizar uma questão, gráfico ou tabela principal por bloco;
- usar títulos, subtítulos e resumos para construir progressão de leitura.

### 2. Corpora e tabelas extensas

Para corpora grandes:

- preferir registros, cartões, listas ou blocos empilhados verticalmente;
- exibir primeiro os campos essenciais;
- mover campos secundários para expansores, detalhes ou páginas específicas;
- permitir filtros antes da renderização de tabelas muito extensas;
- limitar a tabela inicial às colunas necessárias para a decisão do usuário;
- evitar rolagem horizontal como mecanismo principal de navegação;
- disponibilizar download do conjunto completo quando a interface não for adequada para exibir todos os campos;
- considerar visão por unidade documental, com um registro abaixo do outro, em telas pequenas.

### 3. Métricas

- usar uma única coluna em celulares;
- usar no máximo duas colunas em tablets quando os rótulos forem longos;
- evitar fileiras extensas de métricas;
- agrupar métricas por tema, não apenas por disponibilidade de espaço;
- apresentar primeiro indicadores centrais e deixar métricas auxiliares em seção posterior.

### 4. Gráficos

- priorizar gráficos que funcionem em largura reduzida;
- para muitas categorias, usar barras horizontais com categorias empilhadas verticalmente;
- evitar legendas extensas ao lado do gráfico;
- não colocar vários gráficos densos na mesma linha;
- permitir leitura do gráfico sem depender de interação por hover, que é limitada em telas móveis.

### 5. Navegação e detalhamento progressivo

- usar expansores apenas para conteúdo secundário e não para esconder informação essencial;
- dividir páginas muito longas por seções claramente identificadas;
- adotar detalhamento progressivo: resumo, resultado, método, evidência e dados completos;
- permitir que o usuário abra o detalhe de uma instituição ou corpus sem carregar toda a base na tela inicial;
- avaliar filtros e navegação por etapas em vez de apresentar todas as opções simultaneamente.

### 6. Hierarquia visual

- reduzir caixas, bordas, cores, mensagens e títulos concorrentes;
- estabelecer níveis claros de título e espaçamento;
- reservar destaque visual para resultados realmente prioritários;
- separar conteúdo científico, controles de navegação e mensagens operacionais;
- evitar repetição da mesma informação em métrica, tabela, texto e gráfico sem função analítica distinta.

## Responsividade mínima

A interface deverá ser avaliada em pelo menos três faixas:

1. celular: aproximadamente 320–480 px;
2. tablet: aproximadamente 768–1024 px;
3. desktop: acima de 1200 px.

A validação deve verificar:

- ausência de cortes de texto e componentes;
- ausência de rolagem horizontal obrigatória nas páginas principais;
- legibilidade de tabelas e rótulos;
- tamanho adequado de controles de toque;
- ordem lógica dos componentes após o empilhamento;
- carregamento e navegação em orientação vertical e horizontal do dispositivo.

## Inventário visual concluído

O inventário automatizado foi executado sobre `app/streamlit_app.py` e registrado em:

`docs/audit/streamlit_visual_inventory.md`

Principais resultados:

- 18 funções de renderização analisadas;
- `render_observatory_overview_tab` classificada como prioridade máxima, com 1.295 linhas, 14 chamadas de colunas, até 7 colunas simultâneas, 38 métricas e 37 tabelas;
- `render_panel_tab` com 19 tabelas e 9 gráficos;
- `render_data_tab` com 15 tabelas e nenhum expansor;
- sete páginas ou seções adicionais classificadas como críticas por excesso de colunas, métricas ou densidade analítica;
- confirmação objetiva de que a principal interface está excessivamente horizontal e concentrada.

A auditoria permanece executável por:

```bash
python scripts/audit_streamlit_visual_layout.py
```

Ela também passou a integrar o workflow `Quality Checks`.

## Ordem de redesign aprovada

### Ciclo 1 — protótipos prioritários

1. `render_observatory_overview_tab` — Visão Geral;
2. `render_corpus_tab` ou `render_data_tab` — modelo para corpus extenso.

### Ciclo 2 — páginas de alta densidade

3. `render_panel_tab`;
4. `render_institution_tab`;
5. `render_videos_tab`;
6. `render_category_tab`;
7. `render_research_tab`.

### Ciclo 3 — harmonização e validação

8. `render_base_tab`;
9. `render_protocolled_excluded_unit_tab`;
10. `render_scientific_parameters_section`;
11. `render_geo_tab`;
12. páginas de baixa pressão e componentes auxiliares.

## Entregáveis

1. inventário visual por página e aba — **concluído**;
2. mapa da arquitetura de informação atual — **parcialmente concluído pelo inventário**;
3. proposta de nova hierarquia visual — **pendente**;
4. regras de responsividade para componentes Streamlit — **definidas em nível geral; implementação pendente**;
5. protótipo da página Visão Geral — **próxima ação**;
6. protótipo de uma página com corpus extenso — **próxima ação**;
7. padrão para tabelas, cartões, listas, métricas e gráficos — **pendente**;
8. teste manual em celular e tablet — **pendente**;
9. comparação antes/depois com capturas de tela — **pendente**;
10. checklist de aceite visual e responsivo — **pendente**.

## Critérios de conclusão

- a navegação principal ocorre prioritariamente de cima para baixo;
- corpora extensos não dependem de tabelas excessivamente largas;
- a quantidade de elementos simultâneos é reduzida;
- a informação principal aparece antes dos detalhes técnicos;
- páginas principais funcionam sem rolagem horizontal obrigatória em celular;
- métricas e gráficos se reorganizam adequadamente em tablets e celulares;
- o usuário consegue identificar rapidamente objetivo, resultado e próxima ação;
- a estética reforça a credibilidade científica, sem competir com os dados.

## Prioridade

**Alta — experiência pública e apresentação científica.**

Esta frente deve ser articulada com:

- A7 — vitrine pública do projeto;
- diagnóstico de desempenho do Streamlit;
- revisão da terminologia pública;
- arquitetura futura do observatório analítico.

## Estado

**Inventário concluído; redesign pendente.**

A próxima ação é criar a nova hierarquia e o primeiro protótipo vertical da página Visão Geral. Em seguida, deve ser criado o padrão de apresentação vertical para `render_corpus_tab` ou `render_data_tab`.