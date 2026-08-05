# Backlog priorizado de implementação

## Foco atual — prioridade alta: apresentação científica

A plataforma já foi apresentada externamente e precisa consolidar seu pacote científico, jurídico e editorial antes de ampliar a divulgação institucional ou iniciar nova expansão ampla do corpus.

### A1 — Licença do repositório

**Objetivo:** definir formalmente as condições de uso, reprodução, modificação e redistribuição do código, da documentação e dos dados publicados.

**Entregáveis:**

1. decisão documentada sobre a licença do código;
2. avaliação separada da licença aplicável aos dados e à documentação, quando necessário;
3. arquivo `LICENSE` na raiz do repositório;
4. referência clara à licença no `README.md` principal e na documentação em português;
5. verificação de compatibilidade com dependências, dados de terceiros e fontes institucionais.

**Critérios de conclusão:**

- licença aprovada e adicionada ao repositório;
- escopo da licença explicitado;
- eventuais exceções ou limitações de reutilização documentadas;
- ausência de afirmações de abertura incompatíveis com as fontes utilizadas.

**Status:** pendente.

### A2 — Arquivo `CITATION.cff`

**Objetivo:** permitir que pesquisadores citem corretamente a plataforma, seu software e futuras versões arquivadas.

**Entregáveis:**

1. arquivo `CITATION.cff` validado;
2. título oficial do projeto;
3. autoria e afiliação institucional;
4. URL do repositório;
5. versão e data da primeira release científica estável;
6. DOI, apenas quando houver arquivamento formal em serviço apropriado;
7. instrução de citação no `README.md` e no Research Handbook.

**Critérios de conclusão:**

- arquivo compatível com o padrão CFF;
- metadados consistentes com a apresentação institucional do projeto;
- nenhuma informação pessoal, institucional ou identificador inventado;
- citação legível pelo GitHub.

**Status:** pendente.

### A3 — Guia de contribuição

**Objetivo:** estabelecer como pesquisadores, desenvolvedores e colaboradores externos podem contribuir sem comprometer a integridade metodológica da plataforma.

**Entregáveis:**

1. arquivo `CONTRIBUTING.md`;
2. fluxo para propostas de novos corpora;
3. critérios mínimos para incorporação de instituições;
4. regras para evidências, proveniência e revisão humana;
5. padrões de código, testes e documentação;
6. fluxo para correção de dados e contestação institucional;
7. separação entre contribuição técnica, científica e curatorial.

**Critérios de conclusão:**

- responsabilidades e etapas de revisão explicitadas;
- contribuições não podem publicar diretamente dados sensíveis ou afirmações institucionais não revisadas;
- novas incorporações devem seguir a fila e os critérios científicos existentes;
- processo de contribuição compatível com a governança do repositório.

**Status:** pendente.

### A4 — Revisão editorial da documentação

**Objetivo:** garantir clareza, consistência, precisão científica e adequação internacional dos textos públicos.

**Escopo mínimo:**

1. `README.md`;
2. `README.pt-BR.md`;
3. `docs/research/`;
4. `docs/analytics/`;
5. `docs/digital-infrastructure-alignment/`;
6. textos públicos da aplicação Streamlit.

**Critérios de revisão:**

- distinguir implementação, validação estrutural e validação empírica;
- evitar afirmar que detectores ou indicadores estão validados quando ainda dependem de teste real;
- padronizar nomes do projeto, dimensões analíticas e estados metodológicos;
- eliminar repetições desnecessárias;
- melhorar legibilidade para públicos internacionais e interdisciplinares;
- preservar a diferença entre ausência de evidência e ausência do fenômeno observado.

**Critérios de conclusão:**

- revisão integral registrada;
- afirmações científicas compatíveis com o estado real da plataforma;
- versão em inglês revisada como porta de entrada internacional;
- versão em português alinhada semanticamente à versão internacional.

**Status:** pendente.

### A5 — Verificação de links

**Objetivo:** impedir que a apresentação pública direcione para páginas inexistentes, rotas antigas ou documentação incompleta.

**Entregáveis:**

1. inventário de links internos e externos da documentação;
2. verificação automatizada de links relativos do repositório;
3. validação do endereço público do Streamlit;
4. verificação dos links entre README, Executive Summary e Research Handbook;
5. identificação de links externos instáveis, redirecionados ou quebrados;
6. rotina repetível para novas verificações.

**Critérios de conclusão:**

- nenhum link interno quebrado;
- links públicos essenciais testados;
- redirecionamentos e URLs antigas corrigidos;
- falhas externas inevitáveis documentadas sem impedir a validação interna.

**Status:** pendente.

### A6 — Harmonização documental

**Objetivo:** alinhar os documentos de pesquisa, analytics e infraestrutura digital para que funcionem como camadas complementares, e não como definições concorrentes.

**Entregáveis:**

1. mapa de finalidade e público de cada conjunto documental;
2. glossário canônico de termos científicos e técnicos;
3. definição única para corpus, unidade elegível, unidade avaliável, evidência, observação, snapshot, indicador e publicação;
4. referência cruzada entre `docs/research/`, `docs/analytics/` e `docs/digital-infrastructure-alignment/`;
5. remoção ou consolidação de trechos contraditórios e duplicados;
6. indicação clara de qual documento é normativo para cada tema.

**Critérios de conclusão:**

- ausência de definições conflitantes;
- cada conceito central possui uma fonte documental canônica;
- documentos especializados remetem à definição principal em vez de reproduzi-la com variações;
- documentação pública e implementação usam a mesma terminologia.

**Status:** pendente.

### Ordem recomendada de execução

1. licença do repositório;
2. harmonização documental;
3. revisão editorial;
4. verificação de links;
5. `CITATION.cff`;
6. `CONTRIBUTING.md`.

A licença deve ser decidida primeiro porque condiciona a apresentação pública e a reutilização. A harmonização deve anteceder a revisão editorial, evitando revisar textos que ainda serão reorganizados. O arquivo de citação deve refletir a nomenclatura e o estado consolidados após essa revisão.

## Relação com a fila de incorporação europeia

A gestão de novas unidades permanece separada neste arquivo:

`data/output/observatorio_fila_fechamento_europa.csv`

Durante a execução da prioridade de apresentação científica, a fila europeia deve permanecer como registro de incorporação, negativas metodológicas e monitoramento. Novas incorporações amplas não devem substituir a consolidação documental e científica definida neste backlog.

## P0 — fundação obrigatória

> Estado atual: implementado em grande parte; requer consolidação e validação operacional.

1. pacote de domínio de infraestrutura digital;
2. gerador e validador de identificadores;
3. carregamento do registro central de schemas;
4. validador JSON Schema;
5. repositório de proveniência e evidências;
6. verificador de integridade relacional;
7. modelo de versionamento de entidades.

## P1 — operação interna

> Estado atual: implementado estruturalmente; validação empírica e operacional pendente.

1. adaptador da auditoria de infraestrutura existente;
2. fila de revisão curatorial;
3. registro de ações e atribuições;
4. avaliação de qualidade e maturidade;
5. decisão de aptidão para uso;
6. avaliações ética e jurídica.

## P2 — memória institucional

> Estado atual: implementado estruturalmente; execução longitudinal oficial ainda pendente.

1. controlador de ciclos;
2. gerador de snapshots;
3. manifesto e verificação de imutabilidade;
4. comparação entre snapshots;
5. registro de eventos temporais;
6. migração versionada de schemas.

## P3 — produtos científicos

> Estado atual: parcialmente concluído; indicadores existentes precisam de validação empírica e novos indicadores permanecem em desenvolvimento.

1. motor de indicadores;
2. catálogo computável;
3. regras de cobertura e supressão;
4. datasets curados em CSV e JSON;
5. relatório de metodologia e limitações;
6. indicador de evidências públicas de IA aplicada a acervos audiovisuais.

### P3.6 — Indicador de evidências públicas de IA aplicada a acervos audiovisuais

**Objetivo:** transformar os campos experimentais `ai_cataloguing_status` e `ai_cataloguing_evidence` em um indicador científico versionado, calculado apenas sobre unidades elegíveis e efetivamente avaliáveis.

**Escopo técnico e metodológico:**

1. revisar o detector atual, que examina principalmente o texto da superfície ou rota inicialmente consultada;
2. definir uma estratégia controlada de busca em páginas internas, relatórios, notícias institucionais, documentação técnica e páginas de projetos, sem contornar autenticação, paywalls, `robots.txt` ou outras restrições;
3. ampliar e versionar o vocabulário de detecção para aplicações como catalogação automatizada, enriquecimento de metadados, transcrição, reconhecimento de fala, visão computacional, classificação, indexação, tradução e busca semântica;
4. separar os estados `evidência detectada`, `não identificada`, `não avaliável`, `resultado ambíguo` e `pendente de revisão`;
5. registrar URL, trecho, data, método de coleta, idioma, tipo de aplicação de IA e nível de confiança de cada evidência;
6. submeter resultados positivos e amostras negativas à revisão humana;
7. medir falsos positivos e falsos negativos em corpus de validação controlado;
8. definir denominador, fórmula, cobertura mínima, regras de supressão, interpretação e limitações;
9. registrar o indicador no catálogo científico e no registro metodológico;
10. implementar o cálculo no motor analítico e testes automatizados;
11. inserir o resultado na seção **Infraestrutura Científica**, com visualização da cobertura, unidades avaliáveis e evidências revisadas;
12. preservar a distinção entre ausência de evidência pública e ausência institucional de uso de IA.

**Critérios de aceite:**

- definição científica e metodologia versionadas;
- denominador restrito a unidades elegíveis e avaliáveis;
- proveniência completa para cada evidência;
- validação empírica documentada em amostra real;
- métricas de falsos positivos e falsos negativos registradas;
- revisão humana obrigatória para afirmações institucionais;
- testes de cálculo, cobertura, estados não avaliáveis e preservação histórica;
- indicador publicado sem converter automaticamente ausência de detecção em ausência de IA.

**Dependências:** motor de indicadores, catálogo computável, regras de cobertura, proveniência, revisão curatorial e validação operacional dos detectores.

**Risco principal:** páginas iniciais e superfícies públicas isoladas podem omitir projetos de IA descritos em páginas internas, relatórios ou notícias, produzindo subdetecção e comparações institucionais enviesadas.

## P4 — acesso público

> Estado atual: parcialmente implementado.

1. API somente leitura;
2. painel de infraestrutura digital;
3. páginas de instituição, fornecedor e tecnologia;
4. linha do tempo e comparador de períodos;
5. catálogo de downloads e manifestos.

## Fora do primeiro ciclo

- inferência automática de contratos;
- classificação autônoma de riscos por IA;
- publicação de dados pessoais;
- coleta em áreas autenticadas;
- integração automática com fontes juridicamente não avaliadas.
