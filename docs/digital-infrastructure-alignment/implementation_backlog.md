# Backlog priorizado de implementação

## Foco atual — prioridade alta: apresentação científica

A plataforma já foi apresentada externamente. O ciclo atual consolida o pacote científico, jurídico e editorial antes de ampliar a divulgação institucional ou iniciar uma nova expansão ampla do corpus.

### Estado consolidado da prioridade alta

| Frente | Estado | Implementação realizada | Pendência residual |
|---|---|---|---|
| A1 — Licença | implementada | `LICENSE` com MIT para código e CC BY 4.0 para documentação e dados originais publicados | revisão jurídica futura e confirmação de exceções específicas |
| A2 — Citação | implementada | `CITATION.cff` com autoria, título, URLs, versão inicial e descrição | validar no workflow e atualizar versão/DOI após release arquivada |
| A3 — Contribuição | implementada | `CONTRIBUTING.md` com regras técnicas, científicas e curatoriais | amadurecer fluxo de contestação institucional e templates de issues |
| A4 — Revisão editorial | primeira etapa concluída | revisão dos READMEs, Research Handbook e distinção entre implementação e validação empírica | revisão integral dos documentos especializados e textos da aplicação |
| A5 — Verificação de links | automatização implementada | `scripts/check_markdown_links.py` e workflow `Documentation Quality` | executar e corrigir falhas encontradas; validar links externos essenciais |
| A6 — Harmonização documental | primeira etapa concluída | `docs/DOCUMENTATION_GOVERNANCE.md`, hierarquia canônica e glossário comum | auditoria cruzada completa de `docs/analytics/` e `docs/digital-infrastructure-alignment/` |

## A1 — Licença do repositório

**Objetivo:** definir as condições de uso, reprodução, modificação e redistribuição do código, da documentação e dos dados publicados.

**Implementado:**

- arquivo `LICENSE` na raiz;
- licença MIT para código, scripts, testes e componentes de software;
- licença CC BY 4.0 para documentação original e dados produzidos e publicados pelo projeto;
- ressalva explícita sobre direitos, licenças e restrições de materiais e fontes de terceiros;
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
- revisão do índice e terminologia do Research Handbook;
- inclusão de licença, citação, contribuição e governança documental;
- explicitação de que testes estruturais não equivalem à validação empírica;
- distinção entre `não identificado`, `não avaliável` e ausência institucional.

**Próxima etapa:**

- revisar integralmente `docs/research/`;
- revisar `docs/analytics/` contra as definições canônicas;
- revisar `docs/digital-infrastructure-alignment/` e remover duplicações;
- revisar textos públicos da aplicação Streamlit nos três idiomas.

**Estado:** primeira etapa concluída; auditoria editorial integral pendente.

## A5 — Verificação de links

**Objetivo:** impedir referências internas quebradas e reduzir rotas públicas obsoletas.

**Implementado:**

- `scripts/check_markdown_links.py` para validação de links relativos em arquivos Markdown;
- workflow `.github/workflows/documentation-quality.yml` acionado em pushes e pull requests documentais;
- validação automática do `CITATION.cff` no mesmo workflow;
- atualização do endereço público do Streamlit nos READMEs.

**Próxima etapa:**

- observar a primeira execução do workflow e corrigir links internos detectados;
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

## Relação com a fila de incorporação europeia

A gestão de novas unidades permanece separada em:

`data/output/observatorio_fila_fechamento_europa.csv`

A fila europeia continua registrando incorporações potenciais, negativas metodológicas e monitoramento. Durante a consolidação científica, novas incorporações amplas não devem substituir a validação documental, analítica e operacional.

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

> Estado atual: parcialmente implementado.

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
