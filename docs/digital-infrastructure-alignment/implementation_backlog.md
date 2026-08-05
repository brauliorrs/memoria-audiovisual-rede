# Backlog priorizado de implementação

## Foco atual — prioridade alta: apresentação científica

A plataforma já foi apresentada externamente. O ciclo atual consolida o pacote científico, jurídico, editorial e público antes de ampliar a divulgação institucional ou iniciar uma nova expansão ampla do corpus.

### Estado consolidado da prioridade alta

| Frente | Estado | Implementação realizada | Pendência residual |
|---|---|---|---|
| A1 — Licença | implementada | `LICENSE` com MIT para código e CC BY 4.0 para documentação e dados originais publicados | revisão jurídica futura e confirmação de exceções específicas |
| A2 — Citação | implementada | `CITATION.cff` com autoria, título, URLs, versão inicial e descrição | validar no workflow e atualizar versão/DOI após release arquivada |
| A3 — Contribuição | implementada | `CONTRIBUTING.md` com regras técnicas, científicas e curatoriais | amadurecer fluxo de contestação institucional e templates de issues |
| A4 — Revisão editorial | primeira etapa concluída | revisão dos READMEs, Research Handbook e distinção entre implementação e validação empírica | revisão integral dos documentos especializados e textos da aplicação |
| A5 — Verificação de links | automatização implementada | `scripts/check_markdown_links.py` e workflow `Documentation Quality` | executar e corrigir falhas encontradas; validar links externos essenciais |
| A6 — Harmonização documental | primeira etapa concluída | `docs/DOCUMENTATION_GOVERNANCE.md`, hierarquia canônica e glossário comum | auditoria cruzada completa de `docs/analytics/` e `docs/digital-infrastructure-alignment/` |
| A7 — Vitrine pública do projeto | definição pendente | observatório público disponível no Streamlit Cloud | definir arquitetura, identidade visual, domínio, desempenho e relação entre vitrine e ambiente analítico |

## A1 — Licença do repositório

**Objetivo:** definir as condições de uso, reprodução, modificação e redistribuição do código, da documentação e dos dados publicados.

**Implementado:**

- arquivo `LICENSE` na raiz;
- licença MIT para código, scripts, testes e componentes de software;
- licença CC BY 4.0 para documentação original e dados produzidos e publicados pelo projeto;
- ressalva sobre direitos e restrições de materiais e fontes de terceiros;
- referência nos READMEs.

**Estado:** implementado, sujeito a revisão jurídica futura.

## A2 — Arquivo `CITATION.cff`

**Objetivo:** permitir a citação adequada da infraestrutura, do software e das futuras versões arquivadas.

**Implementado:**

- `CITATION.cff` compatível com CFF 1.2.0;
- autoria sem identificadores inventados;
- título oficial, repositório, plataforma pública, resumo e palavras-chave;
- versão inicial `0.1.0`;
- workflow de validação do arquivo.

**Pendências:**

- substituir a versão inicial pela primeira release científica estável;
- adicionar DOI somente após arquivamento formal;
- confirmar afiliação em metadados futuros quando o enquadramento institucional estiver formalmente definido.

**Estado:** implementado para a fase atual.

## A3 — Guia de contribuição

**Objetivo:** permitir contribuições externas sem comprometer integridade metodológica, proveniência e revisão humana.

**Implementado:**

- `CONTRIBUTING.md`;
- regras para propostas de novos corpora;
- critérios para indicadores e métodos;
- exigência de fontes, datas, métodos e limitações;
- proibição de contornar autenticação, paywalls e `robots.txt`;
- separação entre evidência detectada e fato institucional verificado;
- comandos de compilação, testes, implantação e verificação de links.

**Estado:** implementado; templates operacionais podem ser adicionados em ciclo posterior.

## A4 — Revisão editorial da documentação

**Objetivo:** garantir clareza, consistência, precisão científica e adequação internacional.

**Concluído nesta etapa:**

- revisão do `README.md` internacional;
- revisão do `README.pt-BR.md`;
- revisão do índice e da terminologia do Research Handbook;
- inclusão de licença, citação, contribuição e governança documental;
- explicitação de que testes estruturais não equivalem à validação empírica;
- distinção entre `não identificado`, `não avaliável` e ausência institucional.

**Próxima etapa:**

- revisar integralmente `docs/research/`;
- revisar `docs/analytics/` contra as definições canônicas;
- revisar `docs/digital-infrastructure-alignment/` e remover duplicações;
- revisar textos públicos da aplicação nos três idiomas.

**Estado:** primeira etapa concluída; auditoria editorial integral pendente.

## A5 — Verificação de links

**Objetivo:** impedir referências internas quebradas e reduzir rotas públicas obsoletas.

**Implementado:**

- `scripts/check_markdown_links.py` para validação de links relativos em Markdown;
- workflow `.github/workflows/documentation-quality.yml`;
- validação automática do `CITATION.cff`;
- atualização do endereço público do Streamlit nos READMEs.

**Próxima etapa:**

- observar as execuções do workflow e corrigir links internos detectados;
- testar manualmente links externos essenciais;
- documentar exceções decorrentes de bloqueios, redirecionamentos ou mecanismos anti-bot.

**Estado:** automatização implementada; validação externa e correções resultantes pendentes.

## A6 — Harmonização documental

**Objetivo:** fazer com que pesquisa, analytics e infraestrutura digital funcionem como camadas complementares.

**Implementado:**

- `docs/DOCUMENTATION_GOVERNANCE.md`;
- `docs/research/` definido como narrativa científica canônica;
- `docs/analytics/` definido como fonte das especificações computacionais;
- `docs/digital-infrastructure-alignment/` definido como fonte da implementação e governança técnica;
- glossário para projeto, infraestrutura, plataforma, observatório, corpus, evidência, estados avaliativos e validação operacional;
- referências cruzadas no README e no Research Handbook.

**Próxima etapa:**

- localizar definições duplicadas ou divergentes;
- substituir repetições por referências ao documento canônico;
- alinhar nomes de indicadores, estados e populações com o código e a interface.

**Estado:** estrutura de governança implantada; auditoria cruzada integral pendente.

## A7 — Vitrine pública do projeto

**Objetivo:** definir uma porta de entrada institucional, científica e internacional que apresente o projeto com carregamento rápido, identidade visual própria e navegação independente do ambiente analítico.

### Diagnóstico atual

- o Streamlit Cloud funciona como demonstração pública e ambiente analítico;
- o endereço e a implantação ainda não foram tratados como solução definitiva;
- o primeiro carregamento foi percebido como lento;
- uma aplicação Streamlit pode entrar em suspensão e exigir inicialização antes de responder;
- a interface analítica não deve concentrar, sozinha, apresentação institucional, documentação, divulgação e exploração dos dados.

### Princípio arquitetural

A **vitrine pública** e o **observatório analítico** devem ser tratados como camadas distintas:

1. **Vitrine pública:** página leve, rápida, indexável e orientada à apresentação do projeto, seus objetivos, métodos, resultados, equipe, publicações, colaboração e acesso aos produtos.
2. **Observatório analítico:** aplicação interativa para consulta, filtros, indicadores, evidências e exploração dos corpora.
3. **Repositório científico:** código, documentação metodológica, dados versionados, governança e histórico técnico.

O Streamlit pode permanecer como observatório analítico, mas não deve ser adotado automaticamente como vitrine definitiva.

### Decisões pendentes

1. definir se a vitrine será uma página estática ou aplicação web leve;
2. comparar opções de hospedagem, como GitHub Pages, Vercel, Cloudflare Pages ou serviço institucional;
3. definir domínio ou subdomínio próprio;
4. decidir se o Streamlit permanecerá no plano gratuito, será otimizado, receberá hospedagem dedicada ou será substituído em etapa futura;
5. definir selo, logotipo e sistema visual definitivos;
6. definir arquitetura de informação e percurso do visitante;
7. estabelecer versões em português, inglês e espanhol;
8. definir métricas mínimas de desempenho, disponibilidade e acessibilidade.

### Conteúdo mínimo da vitrine

- nome, subtítulo e proposta científica;
- problema e pergunta de pesquisa;
- explicação resumida da infraestrutura longitudinal;
- números principais do corpus e da cobertura;
- indicadores científicos disponíveis;
- limitações e estado de validação;
- demonstração visual do observatório;
- links para observatório, repositório, documentação, datasets e citação;
- autoria, afiliação, contato e formas de colaboração;
- publicações, apresentações e atualizações do projeto.

### Avaliação de desempenho do Streamlit

Antes de decidir pela permanência da implantação atual, devem ser medidos:

- tempo de primeira resposta após período de inatividade;
- tempo até a primeira tela útil;
- consumo de memória na inicialização;
- tamanho e quantidade de arquivos carregados no início;
- operações executadas antes da seleção do usuário;
- uso de cache para dados e recursos;
- impacto das traduções, imagens, gráficos e leitura dos corpora;
- comportamento em dispositivos móveis e conexões mais lentas.

### Ações de otimização candidatas

- adiar carregamentos pesados até a abertura da seção correspondente;
- usar cache para datasets, transformações e recursos estáveis;
- carregar agregados pré-computados na página inicial;
- reduzir leituras repetidas de CSV e JSON;
- evitar criação antecipada de gráficos e tabelas não visíveis;
- separar dados de apresentação dos arquivos científicos completos;
- criar uma tela inicial mínima antes da exploração analítica;
- avaliar hospedagem com processo permanentemente ativo quando o projeto exigir disponibilidade institucional.

### Entregáveis

1. documento de decisão arquitetural da vitrine;
2. comparação técnica e financeira das alternativas de hospedagem;
3. identidade visual e selo definitivos;
4. wireframe ou protótipo da página inicial;
5. orçamento de desempenho do observatório;
6. relatório de diagnóstico do carregamento do Streamlit;
7. plano de domínio e URLs permanentes;
8. integração clara entre vitrine, observatório, GitHub e documentação.

### Critérios de conclusão

- visitante compreende a proposta do projeto sem esperar o observatório carregar;
- vitrine abre rapidamente em computador e dispositivo móvel;
- URLs públicas possuem função clara e não se confundem;
- identidade visual é consistente e adequada à apresentação científica internacional;
- observatório possui desempenho medido e limites documentados;
- decisão sobre permanência, otimização ou substituição do Streamlit é registrada;
- links permanentes são atualizados nos READMEs e metadados de citação.

**Estado:** nova frente prioritária; definição arquitetural, selo definitivo e diagnóstico de desempenho pendentes.

## Relação com a fila de incorporação europeia

A gestão de novas unidades permanece separada em:

`data/output/observatorio_fila_fechamento_europa.csv`

A fila europeia continua registrando incorporações potenciais, negativas metodológicas e monitoramento. Durante a consolidação científica e da vitrine, novas incorporações amplas não devem substituir a validação documental, analítica, operacional e pública.

## P0 — fundação obrigatória

> Estado atual: implementado em grande parte; consolidação e validação operacional pendentes.

1. pacote de domínio de infraestrutura digital;
2. identificadores e validação;
3. registro central de schemas;
4. validação JSON Schema;
5. proveniência e evidências;
6. integridade relacional;
7. versionamento de entidades.

## P1 — operação interna

> Estado atual: implementado estruturalmente; validação empírica e operacional pendente.

1. adaptador da auditoria;
2. revisão curatorial;
3. registro de ações;
4. qualidade e maturidade;
5. aptidão para uso;
6. avaliações ética e jurídica.

## P2 — memória institucional

> Estado atual: implementado estruturalmente; primeiro ciclo longitudinal oficial pendente.

1. controlador de ciclos;
2. snapshots;
3. imutabilidade e manifestos;
4. comparação longitudinal;
5. eventos temporais;
6. migração de schemas.

## P3 — produtos científicos

> Estado atual: parcialmente concluído; validação empírica dos indicadores e novos indicadores permanecem em desenvolvimento.

1. motor de indicadores;
2. catálogo computável;
3. cobertura e supressão;
4. datasets curados;
5. metodologia e limitações;
6. indicador de evidências públicas de IA aplicada a acervos audiovisuais.

### P3.6 — Indicador de evidências públicas de IA aplicada a acervos audiovisuais

**Objetivo:** transformar `ai_cataloguing_status` e `ai_cataloguing_evidence` em indicador científico versionado, restrito a unidades elegíveis e avaliáveis.

**Etapas pendentes:**

1. ampliar o detector para páginas internas, relatórios, notícias e projetos;
2. versionar vocabulário e tipos de aplicação de IA;
3. separar evidência detectada, não identificada, não avaliável, ambígua e pendente de revisão;
4. registrar URL, trecho, data, método, idioma, aplicação e confiança;
5. revisar positivos e amostras negativas;
6. medir falsos positivos e falsos negativos;
7. definir fórmula, cobertura e supressão;
8. registrar no catálogo e motor analítico;
9. publicar na seção Infraestrutura Científica sem interpretar ausência de detecção como ausência de IA.

## P4 — acesso público

> Estado atual: parcialmente implementado. A vitrine pública passa a ser tratada em A7.

1. API somente leitura;
2. painel de infraestrutura digital;
3. páginas de instituição, fornecedor e tecnologia;
4. linha do tempo e comparador;
5. catálogo de downloads e manifestos.

## Fora do primeiro ciclo

- inferência automática de contratos;
- classificação autônoma de riscos por IA;
- publicação de dados pessoais;
- coleta em áreas autenticadas;
- integração automática com fontes juridicamente não avaliadas.
