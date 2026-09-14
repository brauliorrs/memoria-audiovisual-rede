# Famílias conceituais de indicadores de infraestrutura digital

## Status deste documento

Este documento reúne **famílias conceituais e propostas de indicadores**. Ele não é o registro computável ativo, não contém resultados empíricos e não autoriza afirmar que todos os indicadores listados estejam implementados ou validados.

As fontes ativas de identidade, versão, metodologia e execução são:

```text
data/templates/analytics/indicator_registry.json
data/templates/analytics/methodology_registry.json
src/memoria_audiovisual/analytics/
```

Um indicador desta lista somente se torna ativo após receber identificador estável, metodologia versionada, população elegível, denominador, regras de cobertura e supressão, implementação testada e validação compatível.

## Indicadores ativos na fase atual

O registro computável vigente inclui medidas de:

- acesso público imediato aos arquivos audiovisuais;
- cobertura de APIs;
- cobertura ampla de interoperabilidade;
- IIIF;
- OAI-PMH;
- Dublin Core;
- Schema.org;
- JSON-LD;
- índice composto de interoperabilidade.

A marcação `implemented` no registro ativo significa que existe contrato executável e teste controlado. Não significa validação empírica universal.

## Propostas — infraestrutura técnica

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| INF-OPEN-01 | Tecnologia principal de código aberto | relação | proposta |
| INF-STACK-01 | Cobertura observada por camada do stack | instituição | proposta |

API, IIIF e OAI-PMH já possuem indicadores ativos com identificadores computáveis próprios; os códigos conceituais antigos não devem ser usados em resultados novos.

## Propostas — fornecedores e dependência

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| PRV-COUNT-01 | Número de fornecedores com evidência verificada | instituição | proposta |
| PRV-CONC-01 | Concentração de fornecedores por camada | snapshot | proposta |
| PRV-SINGLE-01 | Dependência documentada de fornecedor único | instituição | proposta sensível |
| PRV-FOREIGN-01 | Relação com fornecedor sediado em outro país | relação | proposta |
| PRV-PLATFORM-01 | Dependência documentada de plataforma externa | instituição | proposta |

A presença de uma tecnologia não comprova fornecedor, vínculo contratual ou dependência institucional.

## Propostas — compras e contratos

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| PRO-CONTRACT-01 | Instrumentos tecnológicos com evidência documental | instituição | proposta |
| PRO-VALUE-01 | Valor contratado por categoria tecnológica | contrato/moeda | proposta controlada |
| PRO-OPEN-01 | Documento contratual publicamente acessível | contrato | proposta |
| PRO-DURATION-01 | Duração contratual documentada | contrato | proposta |
| PRO-SUPPLIER-01 | Concentração contratual por fornecedor | snapshot | proposta |

Contratos não devem ser inferidos a partir de detecção técnica, logotipo, domínio ou material promocional.

## Propostas — fluxos e governança de dados

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| DAT-FLOW-01 | Fluxos de dados documentados | instituição | proposta |
| DAT-XBORDER-01 | Fluxo transfronteiriço documentado | fluxo | proposta controlada |
| DAT-THIRD-01 | Processamento por terceiro documentado | fluxo | proposta |
| DAT-LICENSE-01 | Licença de dados identificada | instituição | proposta |
| DAT-AUDIT-01 | Evidência pública de auditabilidade | instituição | proposta |

## Propostas — IA e automação

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| AI-EVID-01 | Cobertura de evidências públicas verificadas de IA | instituição avaliável | em desenho metodológico |
| AI-FUNC-01 | Distribuição das funções documentadas | sistema/evidência | proposta |
| AI-STAGE-01 | Distribuição por estágio declarado | sistema/evidência | proposta |
| AI-VENDOR-01 | Fornecedor externo documentado | sistema | proposta |
| AI-TRANS-01 | Transparência documental observável | sistema/evidência | proposta |
| AI-HUMAN-01 | Supervisão humana publicamente documentada | sistema/evidência | proposta |

Nenhum desses itens deve ser interpretado como medida de ausência de IA. O protocolo aplicável está em [`ai_systems_protocol.md`](ai_systems_protocol.md).

## Propostas — riscos

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| RSK-LOCKIN-01 | Evidência de dependência e barreiras de saída | instituição | proposta sensível |
| RSK-DISC-01 | Risco documentado de descontinuidade | instituição | proposta sensível |
| RSK-INTEROP-01 | Risco de baixa interoperabilidade | instituição | proposta |
| RSK-ACCOUNT-01 | Lacunas observáveis de responsabilização pública | instituição | proposta sensível |
| RSK-EXTINCT-01 | Risco longitudinal de perda de presença pública | instituição/corpus | proposta sensível |

Classificações de risco exigem critérios, revisão humana, contestabilidade e linguagem proporcional à evidência.

## Propostas — evolução longitudinal

| Código conceitual | Proposta | Unidade potencial | Estado |
|---|---|---|---|
| LNG-ADOPT-01 | Tecnologia ou serviço com nova evidência | evento | proposta |
| LNG-DISC-01 | Sinal previamente observado que deixou de ser identificado | evento | proposta sensível |
| LNG-VENDOR-01 | Mudança documentada de fornecedor | evento | proposta |
| LNG-ACCESS-01 | Mudança observada no regime de acesso | evento | proposta |
| LNG-CONTRACT-01 | Início, renovação ou término documentado | evento | proposta |
| LNG-AI-01 | Mudança no estágio publicamente documentado de IA | evento | proposta |

Desaparecimento de evidência não deve ser descrito automaticamente como descontinuação institucional.

## Regra de ativação

Antes do cálculo ou da publicação, cada proposta deverá possuir:

1. pergunta científica e justificativa;
2. unidade de análise e população elegível;
3. numerador, denominador e exclusões, quando aplicável;
4. estados avaliativos e tratamento de dados ausentes;
5. requisitos de evidência e revisão;
6. versão metodológica;
7. cobertura e regra de supressão;
8. implementação e testes;
9. entrada no registro computável ativo;
10. validação operacional documentada.
