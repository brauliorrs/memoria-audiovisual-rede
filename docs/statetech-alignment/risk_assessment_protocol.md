# Protocolo de dependências e riscos

## Princípio

Risco não é detecção técnica bruta. É uma classificação analítica baseada em evidências, regras transparentes e revisão humana.

## Dimensões

- dependência de plataforma externa;
- concentração de fornecedores;
- dependência de fornecedor único;
- dependência de formatos proprietários;
- dependência de autenticação externa;
- dependência de nuvem ou CDN;
- risco de baixa interoperabilidade;
- risco de descontinuidade de serviço;
- risco de extinção digital;
- risco de baixa responsabilização pública.

## Escala

- `not_assessed`: sem avaliação;
- `low`: alternativas documentadas e baixa criticidade;
- `moderate`: dependência relevante, mas com mitigação observável;
- `high`: dependência crítica com alternativas limitadas ou governança opaca;
- `critical`: interrupção ou controle externo pode comprometer diretamente acesso, preservação ou função pública.

## Estrutura da avaliação

- `risk_id`;
- `institution_id`;
- `risk_dimension`;
- `risk_level`;
- `affected_technology_ids`;
- `affected_provider_ids`;
- `assessment_rule_version`;
- `evidence_ids`;
- `mitigation_detected`;
- `reviewer_rationale`;
- `validation_status`;
- `assessment_date`.

## Regras

- não atribuir risco alto apenas porque um sistema é proprietário;
- considerar criticidade da função, substituibilidade, portabilidade e transparência;
- diferenciar dependência técnica de parceria institucional;
- registrar mitigadores: exportação aberta, redundância, código aberto, contrato de continuidade, padrões interoperáveis;
- não somar dimensões automaticamente em um índice geral nesta fase;
- manter versão da regra para permitir comparação longitudinal;
- publicar apenas avaliações confirmadas e acompanhadas de nota metodológica.