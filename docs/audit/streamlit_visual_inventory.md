# Inventário visual do Streamlit

## Escopo

Este inventário foi produzido por análise estática de `app/streamlit_app.py` por meio de `scripts/audit_streamlit_visual_layout.py` e complementado por interpretação editorial.

A auditoria contabiliza chamadas de colunas, métricas, tabelas, gráficos, abas e expansores por função de renderização. Os números indicam pressão estrutural e devem ser confirmados em inspeção visual em celular, tablet e desktop.

## Resultado geral

A aplicação apresenta concentração excessiva de conteúdo em poucas funções grandes. A principal origem da poluição visual não é apenas a escolha de cores ou estilos, mas a combinação de:

- muitas métricas na mesma página;
- tabelas numerosas e potencialmente largas;
- grupos de até sete colunas;
- gráficos e tabelas renderizados simultaneamente;
- páginas extensas sem decomposição suficiente;
- conteúdo secundário carregado antes de o usuário solicitar aprofundamento.

## Prioridades

| Prioridade | Função | Linhas | Chamadas de colunas | Máximo de colunas | Métricas | Tabelas | Gráficos | Abas | Expansores | Pressão horizontal |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crítica | `render_observatory_overview_tab` | 1295 | 14 | 7 | 38 | 37 | 3 | 7 | 8 | 161 |
| crítica | `render_panel_tab` | 292 | 4 | 2 | 2 | 19 | 9 | 1 | 2 | 69 |
| crítica | `render_institution_tab` | 249 | 7 | 4 | 15 | 4 | 1 | 1 | 1 | 45 |
| crítica | `render_videos_tab` | 154 | 4 | 5 | 5 | 5 | 0 | 0 | 2 | 35 |
| crítica | `render_data_tab` | 196 | 1 | 2 | 0 | 15 | 0 | 0 | 0 | 33 |
| crítica | `render_category_tab` | 192 | 3 | 5 | 5 | 3 | 0 | 1 | 0 | 29 |
| crítica | `render_research_tab` | 162 | 3 | 5 | 10 | 2 | 0 | 0 | 1 | 28 |
| crítica | `render_corpus_tab` | 233 | 3 | 5 | 9 | 0 | 1 | 1 | 1 | 27 |
| alta | `render_base_tab` | 171 | 3 | 4 | 4 | 2 | 0 | 0 | 1 | 22 |
| crítica | `render_protocolled_excluded_unit_tab` | 129 | 1 | 5 | 5 | 3 | 0 | 0 | 0 | 22 |
| alta | `render_scientific_parameters_section` | 30 | 1 | 4 | 4 | 3 | 0 | 1 | 0 | 19 |
| média | `render_geo_tab` | 68 | 1 | 2 | 0 | 1 | 3 | 0 | 0 | 11 |
| baixa | `render_sites_tab` | 75 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 4 |
| baixa | `render_project_tab` | 97 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 2 |

## Diagnóstico por página

### 1. Visão Geral — prioridade máxima

`render_observatory_overview_tab` concentra 1.295 linhas, 38 métricas, 37 tabelas, sete abas internas e grupos de até sete colunas.

Esta função deve ser dividida em componentes menores. A página inicial não deve tentar mostrar simultaneamente estado do corpus, ciclos, cobertura, acesso público, indicadores, atualizações e tabelas detalhadas.

Recomendação:

1. resumo científico inicial;
2. quatro métricas essenciais, em no máximo duas colunas;
3. estado do corpus em bloco vertical;
4. atualização e cobertura em seções separadas;
5. indicadores secundários carregados por escolha do usuário;
6. tabelas completas dentro de expansores ou páginas específicas;
7. nenhuma fileira com mais de duas métricas em tablet e uma em celular.

### 2. Painel analítico

`render_panel_tab` contém 19 tabelas e nove gráficos. Mesmo com apenas duas colunas, a densidade simultânea é elevada.

Recomendação:

- escolher um gráfico principal por etapa;
- usar seletor para alternar análise, em vez de renderizar todas;
- manter tabela de suporte abaixo do gráfico correspondente;
- carregar comparações secundárias apenas após seleção;
- evitar que abas ocultas executem previamente todas as transformações e gráficos.

### 3. Instituição

A página usa até quatro colunas e 15 métricas.

Recomendação:

- cabeçalho institucional em uma coluna;
- resumo com duas métricas por linha no desktop e empilhamento móvel;
- separar perfil, evidências, tecnologias e histórico em sequência vertical;
- exibir tabelas detalhadas somente após seleção da instituição e abertura da seção.

### 4. Vídeos

A página usa até cinco colunas e cinco tabelas.

Recomendação:

- filtros em fluxo vertical ou em duas colunas no máximo;
- métricas em cartões empilháveis;
- lista de vídeos orientada verticalmente;
- detalhes de cada vídeo em expansor ou página própria;
- evitar tabela larga como visão principal em celular.

### 5. Dados

A página possui 15 tabelas e nenhum expansor.

Recomendação:

- transformar a página em catálogo vertical de conjuntos;
- apresentar nome, descrição, período, cobertura e ação de download;
- abrir prévia somente quando solicitada;
- limitar a prévia a colunas essenciais;
- não renderizar simultaneamente todas as tabelas.

### 6. Categorias

A página usa até cinco colunas, cinco seletores e três tabelas.

Recomendação:

- filtros em sequência lógica;
- resultado principal abaixo dos filtros;
- métricas em duas colunas no máximo;
- detalhes e tabelas secundárias sob demanda.

### 7. Pesquisa

A página usa até cinco colunas, dez métricas e nove seletores.

Recomendação:

- preservar a narrativa científica em fluxo vertical;
- separar pergunta, método, parâmetros e estado de validação;
- evitar transformar conteúdo científico em painel de métricas horizontais;
- mover controles avançados para seção posterior.

### 8. Corpus

A página usa até cinco colunas e nove métricas.

Recomendação:

- adotar visão vertical por unidade documental;
- permitir busca e filtros antes de carregar detalhes;
- mostrar resumo do corpus, lista de unidades e detalhe da unidade em etapas;
- em celular, usar um registro por bloco, nunca depender de tabela larga.

## Ordem de redesign

### Ciclo 1 — protótipos

1. `render_observatory_overview_tab`;
2. `render_corpus_tab` ou `render_data_tab` como modelo de corpus extenso.

### Ciclo 2 — páginas de alta densidade

3. `render_panel_tab`;
4. `render_institution_tab`;
5. `render_videos_tab`;
6. `render_category_tab`;
7. `render_research_tab`.

### Ciclo 3 — harmonização

8. `render_base_tab`;
9. `render_protocolled_excluded_unit_tab`;
10. `render_scientific_parameters_section`;
11. `render_geo_tab`;
12. validação das páginas de baixa pressão.

## Padrão de carregamento sob demanda

Devem ser candidatas a carregamento somente após ação do usuário:

- tabelas completas;
- análises secundárias;
- comparações entre múltiplos recortes;
- evidências detalhadas;
- históricos e séries extensas;
- downloads gerados dinamicamente;
- gráficos de páginas ou abas não ativas;
- conteúdo de instituição ou corpus ainda não selecionado.

## Critérios de aceite

- nenhuma página principal usa mais de duas colunas de conteúdo denso;
- nenhum grupo de métricas usa mais de duas colunas em tablet;
- corpora extensos possuem alternativa vertical à tabela larga;
- conteúdo secundário não é renderizado antes de ser solicitado;
- Visão Geral deixa de concentrar dezenas de tabelas simultâneas;
- páginas críticas são verificadas em celular, tablet e desktop;
- a navegação principal ocorre de cima para baixo;
- a interface preserva a narrativa científica antes do detalhamento técnico.

## Validação automatizada

A auditoria foi executada no workflow `Quality Checks` e a suíte terminou com:

- auditoria visual concluída;
- 18 funções de renderização analisadas;
- 644 testes e 2 subtestes aprovados;
- verificações científicas e de implantação aprovadas.

A análise estática deve permanecer no workflow para acompanhar regressões de densidade e crescimento horizontal.