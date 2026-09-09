# Backlog de arquitetura visual e responsividade

## Objetivo

Reduzir a poluição visual do observatório, melhorar desempenho e tornar a interface utilizável em celular, tablet e desktop sem comprometer a leitura científica.

A revisão envolve arquitetura da informação, hierarquia visual, responsividade, densidade de dados e carregamento progressivo.

## Estado atual

### Concluído

- inventário automatizado das funções de renderização;
- auditoria integrada ao workflow `Quality Checks`;
- redução da navegação principal para quatro áreas;
- remoção das abas individuais de corpora e casos documentados;
- acesso às unidades dentro da categoria correspondente;
- substituição do carregamento simultâneo das abas principais por seleção de seção única;
- carregamento progressivo da Infraestrutura Científica;
- localização multilíngue do rótulo e do conteúdo da Infraestrutura Científica;
- teste e remoção do protótipo vertical separado da Visão Geral.

### Decisão de design revisada

O protótipo de Visão Geral totalmente vertical não apresentou bom resultado e foi removido. Portanto, a estratégia não será transformar toda a plataforma em uma sequência vertical única.

A navegação horizontal curta de quatro áreas será preservada:

1. Visão Geral;
2. Infraestrutura Científica;
3. Categoria: Agregadores;
4. Categoria: Arquivos.

A verticalização continuará sendo usada de forma seletiva dentro de páginas densas, tabelas extensas, listas de unidades e detalhes técnicos.

## Diagnóstico mantido

O inventário registrou:

- 18 funções de renderização analisadas;
- `render_observatory_overview_tab` com 1.295 linhas, 14 chamadas de colunas, até 7 colunas simultâneas, 38 métricas e 37 tabelas;
- `render_panel_tab` com 19 tabelas e 9 gráficos;
- `render_data_tab` com 15 tabelas e nenhum expansor;
- páginas adicionais com excesso de colunas, métricas ou densidade analítica.

A auditoria permanece executável por:

```bash
python scripts/audit_streamlit_visual_layout.py
```

## Princípios vigentes

### 1. Navegação principal curta e estável

- preservar apenas quatro áreas principais;
- não recriar abas individuais para corpora;
- abrir unidades por seleção dentro das categorias;
- executar somente a seção selecionada;
- não usar `st.tabs` quando o conteúdo oculto for pesado.

### 2. Redução de densidade dentro das páginas

- reduzir fileiras excessivas de métricas;
- agrupar indicadores por finalidade científica;
- eliminar repetições entre métrica, texto, tabela e gráfico;
- apresentar primeiro síntese e resultado;
- mover método, evidência e dados completos para detalhamento sob demanda.

### 3. Corpora e tabelas extensas

- aplicar filtros antes da tabela;
- exibir inicialmente apenas colunas essenciais;
- usar detalhes ou expansores para campos secundários;
- manter download do conjunto completo;
- evitar que a tabela larga seja a única forma de consulta;
- carregar o corpus detalhado apenas após a seleção da unidade.

### 4. Gráficos

- evitar vários gráficos densos na mesma linha;
- preferir uma questão analítica por bloco;
- usar barras horizontais quando houver muitas categorias;
- garantir leitura sem depender exclusivamente de hover;
- adiar gráficos secundários até solicitação do usuário.

### 5. Responsividade

A interface deve ser verificada em:

1. celular: 320–480 px;
2. tablet: 768–1024 px;
3. desktop: acima de 1200 px.

Verificar:

- cortes de texto;
- rolagem horizontal obrigatória;
- empilhamento de métricas;
- largura de tabelas;
- controles de toque;
- legibilidade de rótulos;
- manutenção da ordem científica dos componentes.

## Ordem de trabalho revisada

### Ciclo 1 — consolidação da nova navegação

1. validar manualmente as quatro áreas nos três idiomas;
2. medir tempo de abertura de cada área;
3. verificar o seletor de unidades em Agregadores e Arquivos;
4. testar mudança de idioma mantendo a seção selecionada;
5. revisar falhas de rótulo, estado e cache.

### Ciclo 2 — redução de densidade prioritária

6. revisar `render_observatory_overview_tab` sem reconstrução integral;
7. revisar `render_category_tab`, que passou a concentrar síntese e acesso às unidades;
8. escolher `render_panel_tab` ou `render_data_tab` como primeiro redesenho interno controlado;
9. reduzir tabelas e métricas exibidas antes da solicitação do usuário;
10. definir padrões reutilizáveis de resumo, filtro, tabela essencial e detalhe.

### Ciclo 3 — páginas de alta densidade

11. `render_institution_tab`;
12. `render_videos_tab`;
13. `render_research_tab`;
14. páginas de unidade e componentes auxiliares.

### Ciclo 4 — validação responsiva

15. teste manual em celular, tablet e desktop;
16. comparação antes/depois;
17. checklist de aceite visual;
18. registro das limitações remanescentes do Streamlit.

## Próxima ação recomendada

Realizar uma **auditoria manual do percurso principal** nas quatro áreas e nos três idiomas, registrando:

- tempo de abertura;
- falhas de tradução;
- componentes que não respondem;
- tabelas que exigem rolagem horizontal;
- métricas excessivas;
- conteúdo carregado antes da solicitação do usuário.

Após essa auditoria, o primeiro redesenho interno deve ocorrer em `render_category_tab` ou `render_data_tab`, e não em uma nova versão separada da Visão Geral.

## Critérios de conclusão

- as quatro áreas principais abrem de forma confiável;
- apenas a área selecionada é executada;
- unidades não voltam ao nível superior;
- a informação essencial aparece antes do detalhe técnico;
- tabelas extensas possuem visão inicial reduzida ou alternativa de consulta;
- não há rolagem horizontal obrigatória nas rotas principais móveis;
- mudança de idioma atualiza rótulos e conteúdo da seção ativa;
- a interface mantém credibilidade científica e desempenho aceitável.

## Estado

**Navegação e carregamento progressivo implementados; validação multilíngue, redução de densidade e responsividade pendentes.**
