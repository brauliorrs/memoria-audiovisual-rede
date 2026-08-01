# Política de triagem dos eventos longitudinais

A comparação entre snapshots não é publicada diretamente. Cada evento passa por uma classificação operacional que separa mudanças rotineiras, alterações materiais, desaparecimentos, sinais sensíveis e problemas de qualidade dos dados.

## Classes

| Classe | Exemplos | Publicação |
|---|---|---|
| `routine` | linha de base e ausência de mudança | `publishable` |
| `material_change` | tecnologia, API ou formato apareceu ou mudou | `pending_review` |
| `disappearance_alert` | parâmetro anteriormente detectado deixou de aparecer | `pending_review` |
| `sensitive` | mudança em restrição de acesso ou sinal de IA | `pending_review` |
| `data_quality` | erro, não avaliável ou lacuna persistente | `blocked` |
| `unclassified` | estado não previsto pela política | `blocked` |

`publishable` significa apenas que o evento é elegível para uma camada pública futura. O workflow atual não publica páginas, painéis ou alertas externos automaticamente.

## Regras conservadoras

- desaparecimento nunca é publicado como fato definitivo sem revisão;
- mudança em restrição ou IA exige revisão humana;
- erro e superfície não avaliável não são convertidos em desaparecimento;
- primeira linha de base e eventos sem mudança podem ser expostos como informação rotineira;
- cada evento recebe identificador determinístico e código de justificativa;
- eventos duplicados dentro da mesma rodada são bloqueados.

## Produto

Cada rodada produz:

```text
data/statetech/triage/<snapshot_id>.json
```

O arquivo contém contagens por classe, quantidade de eventos que exigem revisão e o estado de publicação de cada evento. Ele é preservado na branch `statetech-history` e incluído na cópia operacional temporária do workflow.
