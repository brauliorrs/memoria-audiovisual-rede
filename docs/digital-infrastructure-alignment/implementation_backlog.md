# Backlog priorizado de implementação

## P0 — fundação obrigatória

1. pacote `src/digital_infrastructure/domain`;
2. gerador e validador de identificadores;
3. carregamento do registro central de schemas;
4. validador JSON Schema;
5. repositório de proveniência e evidências;
6. verificador de integridade relacional;
7. modelo de versionamento de entidades.

## P1 — operação interna

1. adaptador da auditoria de infraestrutura existente;
2. fila de revisão curatorial;
3. registro de ações e atribuições;
4. avaliação de qualidade e maturidade;
5. decisão de aptidão para uso;
6. avaliações ética e jurídica.

## P2 — memória institucional

1. controlador de ciclos;
2. gerador de snapshots;
3. manifesto e verificação de imutabilidade;
4. comparação entre snapshots;
5. registro de eventos temporais;
6. migração versionada de schemas.

## P3 — produtos científicos

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

1. API somente leitura;
2. painel infraestrutura digital;
3. páginas de instituição, fornecedor e tecnologia;
4. linha do tempo e comparador de períodos;
5. catálogo de downloads e manifestos.

## Fora do primeiro ciclo

- inferência automática de contratos;
- classificação autônoma de riscos por IA;
- publicação de dados pessoais;
- coleta em áreas autenticadas;
- integração automática com fontes juridicamente não avaliadas.
