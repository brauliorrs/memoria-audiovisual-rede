# Plano de implementação técnica por fases

## Objetivo

Converter a arquitetura documental da camada infraestrutura digital em módulos executáveis sem comprometer rastreabilidade, comparabilidade longitudinal ou governança curatorial.

## Princípios

- implementar de baixo para cima: contratos e persistência antes de painéis;
- não publicar resultados antes de validação, qualidade e aptidão para uso;
- preservar compatibilidade com o observatório audiovisual existente;
- separar coleta, transformação, validação, snapshot, indicador e publicação;
- manter cada fase reversível e testável.

## Fase 0 — consolidação estrutural

Entregas:
- revisão final de schemas e identificadores;
- registro central de versões;
- mapa de dependências;
- critérios de aceite por módulo.

Saída: arquitetura pronta para implementação.

## Fase 1 — núcleo de dados e proveniência

Entregas:
- modelos de entidades;
- persistência de versões;
- registro de proveniência;
- armazenamento de evidências e artefatos;
- chaves estrangeiras e integridade relacional.

Saída: registros estruturados e rastreáveis, ainda sem publicação.

## Fase 2 — ingestão e adaptação da auditoria

Entregas:
- adaptadores dos coletores existentes;
- geração de IDs estáveis;
- preenchimento de datas e agentes;
- classificação de evidência;
- fila de revisão curatorial.

Saída: dados brutos e revisáveis no novo contrato.

## Fase 3 — validação, qualidade e aptidão

Entregas:
- motor de regras de integridade;
- avaliação de qualidade;
- níveis de maturidade;
- decisões de aptidão para uso;
- trilha de auditoria.

Saída: registros elegíveis para snapshots e pesquisa.

## Fase 4 — memória e comparação longitudinal

Entregas:
- abertura e fechamento de ciclos;
- snapshots imutáveis;
- detecção de mudanças;
- classificação de diferenças;
- migração entre schemas.

Saída: séries históricas comparáveis.

## Fase 5 — indicadores

Entregas:
- catálogo computável;
- cálculo com denominadores explícitos;
- cobertura, confiança e supressão;
- versionamento de definições e resultados.

Saída: indicadores aptos para revisão e publicação.

## Fase 6 — publicação e acesso

Entregas:
- produtos CSV e JSON;
- API pública somente leitura;
- painel longitudinal;
- manifestos de publicação;
- política de retirada e substituição.

Saída: camada pública versionada.

## Fase 7 — expansão analítica

Entregas:
- fornecedores e contratos;
- fluxos de dados;
- IA e automação;
- riscos e dependências;
- análises comparativas entre países e instituições.

Saída: módulo infraestrutura digital plenamente integrado ao observatório.
