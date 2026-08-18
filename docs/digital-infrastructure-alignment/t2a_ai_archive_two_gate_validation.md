# T2A — dupla validação de IA no acervo

## Regra científica central

O MAR adota uma validação sequencial em duas portas. **Uma ocorrência só é considerada uso de IA no acervo quando passa pelas duas portas.**

### Porta 1 — identificação terminológica/contextual

Objetivo: identificar evidência textual, estruturada ou técnica de que IA participou da produção ou modificação de um conteúdo audiovisual.

A Porta 1 responde:

> Há evidência verificável, na documentação analisada, de participação de IA na produção ou modificação de um item audiovisual?

A Porta 1 pode usar controles externos e documentação institucional para calibrar o reconhecimento de expressões como IA generativa, deepfake, clonagem de voz, conteúdo gerado por IA e produção assistida por IA.

Passar pela Porta 1 **não significa** que o MAR encontrou IA no acervo observado. Significa apenas que o mecanismo reconheceu corretamente uma evidência terminológica/contextual de IA.

### Porta 2 — validação no acervo observado

Objetivo: comprovar simultaneamente que:

1. a unidade observada é realmente um **item, versão ou segmento audiovisual**, e não uma página geral, notícia, índice ou superfície institucional;
2. o item audiovisual integra o corpus/acervo efetivamente observado e materializado pelo MAR; e
3. a evidência de IA está inequivocamente vinculada à produção ou modificação daquele item.

A fonte que comprova o uso de IA pode estar fora da ficha do item — por exemplo, uma declaração do produtor ou uma publicação institucional —, mas ela só pode sustentar o indicador do MAR se o item tiver pertencimento comprovado ao corpus observado.

## Regra de decisão

Formalmente:

`IA_NO_ACERVO = PORTA_1_POSITIVA AND UNIDADE_ITEM AND ITEM_NO_CORPUS AND EVIDENCIA_VINCULADA_AO_ITEM`

Se qualquer componente falhar, o item não é contado como ocorrência positiva de IA no acervo.

Estados operacionais da Porta 2:

- `confirmed_ai_use_in_observed_archive` — as duas portas foram satisfeitas;
- `gate1_terminology_not_positive` — não houve evidência terminológica/contextual suficiente;
- `not_item_level_observation` — o registro é uma página geral, notícia, índice ou superfície institucional, não uma unidade audiovisual elegível;
- `item_outside_observed_corpus` — existe evidência de IA, mas o item não integra o corpus observado;
- `evidence_not_linked_to_item` — a instituição fala de IA, mas a evidência não está vinculada ao item do corpus;
- `not_assessable` — natureza da unidade, pertencimento ou vínculo não puderam ser avaliados.

## Consequência para artigos e páginas institucionais sobre IA

Uma matéria institucional que discuta filmes produzidos com IA é válida para calibrar a **Porta 1**. Entretanto, ela não demonstra por si só presença de IA no acervo.

Exemplo: uma publicação do BFI pode documentar que determinado filme utilizou clonagem de voz por IA. Esse caso é um controle terminológico positivo. Para gerar uma ocorrência de IA no acervo BFI observado pelo MAR, o mesmo filme precisa ser recuperado como item do corpus/materialização do BFI e a declaração precisa ser vinculada a esse item.

Assim, o MAR evita transformar "a instituição fala sobre IA" em "o acervo contém IA".

## Sequência de validação

1. calibrar e concluir a identificação terminológica/contextual;
2. aplicar a Porta 1 automaticamente sobre registros materializados dos corpora ativos;
3. gerar uma fila de candidatos exclusivamente a partir dos produtos reais do corpus;
4. confirmar que cada candidato corresponde a item/versão/segmento audiovisual elegível;
5. validar pertencimento e vínculo item-evidência na Porta 2;
6. comparar decisão automática e revisão humana em amostra cega;
7. somente então habilitar quantificação de IA no acervo.

## Situação das amostras já executadas

O benchmark controlado 3×3, a amostra cega de 12 negativos reais e os controles positivos externos/institucionais pertencem à calibração da **Porta 1**.

A fila `ai_content_blind_positive_challenge_v1.json` foi interrompida como validação de acervo após refinamento metodológico. Os julgamentos já registrados permanecem preservados como controles terminológicos; não podem ser apresentados como ocorrências de IA no acervo.

A Porta 2 deve começar com itens originados nos arquivos e registros efetivamente materializados pelos coletores do MAR.

## Quantificação

Os indicadores `share_with_ai_evidence`, `share_materially_ai_changed` e `share_synthetic` só poderão usar observações com `confirmed_ai_use_in_observed_archive`.

Controles terminológicos externos, notícias, artigos institucionais, páginas gerais e itens fora do corpus não entram no numerador nem no denominador de prevalência do acervo.

## Relação com T2

A dupla validação permanece experimental em T2A e não modifica o baseline T2, os nove indicadores oficiais existentes nem os denominadores históricos.
