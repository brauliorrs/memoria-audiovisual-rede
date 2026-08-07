# Política de triagem dos eventos longitudinais

A comparação entre snapshots não é publicada diretamente. Cada resultado é tratado primeiro como candidato a evento e passa por classificação operacional que separa estabilidade, mudanças materiais, possíveis desaparecimentos, sinais sensíveis e problemas de qualidade.

## Classes

| Classe | Exemplos | Estado inicial |
|---|---|---|
| `routine` | linha de base e ausência de mudança material | `eligible_for_projection` |
| `material_change` | tecnologia, API, formato ou relação mudou | `pending_review` |
| `disappearance_alert` | parâmetro anteriormente detectado deixou de aparecer | `pending_review` |
| `sensitive` | alteração de acesso, IA, fornecedor, contrato ou classificação de risco | `pending_review` |
| `data_quality` | erro, não avaliável, falha de coleta ou lacuna persistente | `blocked` |
| `methodological_change` | schema, taxonomia, regra ou cobertura mudou | `blocked_for_empirical_claim` |
| `unclassified` | estado não previsto | `blocked` |

`eligible_for_projection` significa apenas que o registro pode integrar uma projeção técnica após os demais controles. Não equivale a publicação externa, validação científica ou afirmação institucional.

## Regras conservadoras

- desaparecimento nunca é publicado como fato definitivo sem revisão e evidência suficiente;
- mudança em acesso, IA, fornecedor, contrato ou risco exige revisão humana;
- erro, bloqueio e superfície não avaliável não são convertidos em desaparecimento;
- alteração metodológica não é publicada como mudança institucional;
- primeira linha de base e eventos sem mudança podem ser classificados como rotineiros, mas devem preservar cobertura e data;
- cada evento recebe identificador determinístico e código de justificativa;
- eventos duplicados na mesma rodada são bloqueados;
- o estado de triagem não substitui a decisão curatorial nem a decisão editorial.

## Dados mínimos do evento

- `event_id`;
- `comparison_id`;
- snapshots anterior e posterior;
- entidade, variável ou relação afetada;
- classe de triagem;
- valor anterior e posterior;
- origem provável da diferença;
- evidências associadas;
- estado de avaliabilidade;
- cobertura aplicável;
- código de justificativa;
- estado de revisão;
- elegibilidade de publicação.

## Produto operacional

Cada rodada pode produzir um arquivo versionado em:

```text
data/digital_infrastructure/triage/<snapshot_id>.json
```

O produto registra contagens por classe, eventos bloqueados, eventos que exigem revisão e o estado de cada candidato. A preservação durável pode usar a branch histórica dedicada, mas essa decisão operacional não integra o significado científico do evento.

## Estado atual

A triagem está implementada estruturalmente e possui testes controlados. Permanecem pendentes a validação com eventos reais heterogêneos, a calibração dos limiares e a confirmação de que todas as classes conservam corretamente falhas, estados não avaliáveis e mudanças metodológicas.