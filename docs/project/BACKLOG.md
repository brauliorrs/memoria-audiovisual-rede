# Project Backlog

Este backlog separa as ações necessárias para consolidar a apresentação científica das melhorias que podem ser realizadas em ciclos posteriores.

## Prioridade atual — consolidação da interface pública

### 1. Validação multilíngue do percurso principal

**Estado:** em andamento, com arquitetura funcional já implantada.

Concluído:

- navegação principal disponível em português, inglês e espanhol;
- rótulos principais localizados, incluindo Infraestrutura Científica;
- Infraestrutura Científica com conteúdo próprio nos três idiomas;
- idioma ativo passado diretamente aos módulos especializados;
- carregamento progressivo das seções principais;
- remoção do carregamento simultâneo de todas as abas ocultas.

Pendências:

1. realizar validação manual completa do percurso principal nos três idiomas;
2. verificar frases híbridas e traduções parciais nas categorias e páginas de unidade;
3. revisar controles, mensagens, tabelas e expansores após a seleção de cada idioma;
4. registrar problemas por página e prioridade;
5. confirmar que nenhuma mudança de idioma mantém rótulos ou estado visual do idioma anterior;
6. concluir o critério de prontidão para apresentação científica internacional.

### 2. Navegação principal e desempenho

**Estado:** primeira etapa concluída.

Implementado:

- apenas quatro áreas de primeiro nível:
  1. Visão Geral;
  2. Infraestrutura Científica;
  3. Categoria: Agregadores;
  4. Categoria: Arquivos;
- corpora e unidades removidos do nível superior;
- unidades acessadas por seletor dentro da categoria correspondente;
- somente a seção principal selecionada é executada;
- Infraestrutura Científica carrega apenas a subseção escolhida;
- protótipo vertical separado da Visão Geral removido após avaliação negativa.

Pendências:

1. medir tempo de abertura de cada uma das quatro áreas;
2. identificar leituras de arquivos ainda repetidas após a seleção;
3. avaliar cache e pré-computação nas categorias e unidades;
4. verificar comportamento após suspensão e reinicialização no Streamlit Cloud;
5. testar a navegação em celular, tablet e conexão mais lenta;
6. documentar um orçamento mínimo de desempenho.

## Alta prioridade — arquitetura visual e responsividade

**Estado:** inventário concluído; estratégia revisada.

O fluxo vertical integral proposto para a Visão Geral foi testado e rejeitado. A revisão visual continuará de forma incremental sobre a interface existente, preservando a navegação horizontal curta de quatro áreas.

Diretrizes atuais:

- reduzir densidade e horizontalidade dentro das páginas, sem transformar toda a aplicação em uma sequência vertical única;
- limitar fileiras excessivas de métricas;
- priorizar filtros antes de tabelas extensas;
- mover detalhes secundários para expansores ou para a unidade selecionada;
- evitar carregar tabelas, gráficos e evidências que o usuário ainda não solicitou;
- preservar as quatro áreas principais como estrutura estável de navegação;
- validar responsividade sem sacrificar a leitura científica em desktop.

Próximas ações:

1. revisar a Visão Geral atual e eliminar redundâncias sem reconstruí-la integralmente;
2. revisar `render_category_tab`, agora responsável pela síntese e pelo acesso às unidades;
3. reduzir métricas simultâneas e tabelas largas nas páginas de unidade;
4. escolher entre `render_panel_tab` e `render_data_tab` para o próximo redesenho controlado;
5. criar padrões reutilizáveis para tabela essencial, detalhe sob demanda e métricas compactas;
6. executar teste manual em celular, tablet e desktop;
7. comparar desempenho e legibilidade antes/depois.

Detalhamento em:

`docs/project/VISUAL_ARCHITECTURE_BACKLOG.md`

## Alta prioridade — política de alimentação dos corpora e atualização dos índices

**Estado:** regra proposta; decisões metodológicas e automação pendentes.

### Gatilho operacional proposto

Uma nova rodada de atualização dos índices deve ser aberta quando forem incorporados **20 novos corpora elegíveis e validados do mesmo continente** desde a última rodada concluída para esse continente.

A contagem é separada por continente e não pode combinar corpora de continentes diferentes apenas para atingir o limite.

### Elegibilidade para a contagem

Um corpus somente entra na contagem quando possuir:

1. identidade institucional estável e continente definido;
2. metadados mínimos completos;
3. evidência e proveniência registradas;
4. validação estrutural concluída;
5. estado de avaliabilidade definido;
6. decisão de inclusão aprovada;
7. ausência de pendência crítica de integridade.

Duplicados, pendentes, experimentais, excluídos, não avaliáveis ou sem evidência suficiente não contam.

### Ações ao atingir o limite

1. congelar a composição elegível da rodada;
2. abrir novo ciclo continental de observação;
3. executar coleta e validação;
4. recalcular indicadores continentais;
5. recalcular indicadores globais afetados pelo novo denominador;
6. atualizar cobertura, elegibilidade e não avaliabilidade;
7. comparar com o snapshot anterior;
8. revisar mudanças materiais e distorções metodológicas;
9. passar pelos portões editoriais e de governança;
10. preservar os resultados anteriores como versão histórica imutável.

### Rodadas antecipadas

Uma rodada pode ocorrer antes de 20 corpora quando houver:

- correção de erro material;
- mudança metodológica relevante;
- alteração importante de avaliabilidade;
- incorporação de bloco nacional ou regional estratégico;
- evento relevante de acesso, infraestrutura ou preservação;
- publicação científica, relatório ou marco formal da pesquisa.

Toda antecipação deve possuir justificativa registrada.

### Decisões pendentes

1. simular o limite de 20 com o tamanho atual dos continentes;
2. definir o tratamento de instituições transcontinentais e agregadores internacionais;
3. avaliar limite proporcional ou prazo máximo para continentes com menor expansão;
4. definir exatamente quais indicadores são recalculados;
5. decidir se a rodada reobserva todo o corpus continental ou apenas as novas unidades;
6. definir prazo máximo de espera sem atingir o limite;
7. criar contador automatizado e relatório de prontidão;
8. integrar o gatilho aos workflows de snapshot, analytics e publicação.

### Critérios de aceite

- a plataforma informa quantos corpora faltam para a próxima rodada em cada continente;
- apenas corpora elegíveis incrementam a contagem;
- composição e metodologia são congeladas antes do cálculo;
- denominadores continentais e globais são versionados;
- índices anteriores permanecem recuperáveis;
- rodadas antecipadas possuem justificativa pública ou auditável;
- todo índice exibe data de referência, tamanho do corpus e versão metodológica.

## Após a consolidação da apresentação científica

### Scientific Internationalization Audit — SIA

**Estado:** backlog posterior.

Escopo potencial:

- métricas de cobertura multilíngue por página, módulo e componente;
- validação terminológica semântica;
- inspeção de constantes e estruturas aninhadas;
- proveniência e estado de revisão das traduções;
- verificação automática de consistência terminológica;
- indicador de qualidade da tradução;
- portão completo de internacionalização;
- migração integral de textos públicos para chaves semânticas.

### Vitrine pública independente

**Estado:** decisão arquitetural pendente.

O Streamlit permanece como observatório analítico. Após a consolidação da interface atual, deve ser avaliada uma vitrine pública leve, rápida e indexável, separada do ambiente analítico.

## Regra do backlog

Uma ideia permanece no backlog quando melhora a plataforma, mas não impede uma apresentação clara, credível, funcional e linguisticamente consistente da infraestrutura científica atual.
