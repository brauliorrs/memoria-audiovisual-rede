# Protocolo de IA na produção de conteúdo audiovisual

## 1. Distinção conceitual

A plataforma separa duas perguntas científicas diferentes:

1. **IA institucional aplicada ao acervo** — uso de IA para pesquisa, catalogação, descrição, metadados, transcrição, reconhecimento, restauração, busca, preservação ou outras operações institucionais sobre o acervo;
2. **IA aplicada à produção ou modificação do conteúdo** — uso de IA que participa da criação, edição ou alteração do próprio item audiovisual.

Uma instituição pode usar IA intensivamente para pesquisar ou catalogar acervos sem possuir conteúdo produzido com IA. Da mesma forma, um item pode conter material gerado por IA mesmo quando não existe evidência de IA na infraestrutura institucional de pesquisa do acervo.

As duas dimensões nunca devem ser somadas ou apresentadas como se medissem o mesmo fenômeno.

## 2. Unidade de análise

A tarefa `ai_content_production_detection` opera em nível de:

- `item_id`;
- `item_version_id`; ou
- `segment_id`.

Ela não é executada apenas com contexto de instituição. O objetivo é evitar inferências agregadas como “a instituição usa IA, portanto seus vídeos usam IA”.

A implementação está em:

`src/memoria_audiovisual/digital_infrastructure/ai_content_production.py`

## 3. Classes de uso de IA no conteúdo

O protocolo v1.0 adota classes mutuamente exclusivas para cada unidade observada:

- `no_verified_ai_evidence` — não existe evidência verificável de IA na produção/modificação do item;
- `ai_assisted_production` — IA participou do fluxo de produção, mas não existe evidência de alteração material que torne o conteúdo sintético;
- `materially_ai_modified` — IA alterou materialmente imagem, voz ou vídeo preexistente;
- `partially_synthetic` — parte relevante do conteúdo foi gerada artificialmente;
- `fully_synthetic` — o item é declarado como integralmente gerado por IA;
- `not_assessable` — evidência insuficiente ou inacessível para aplicar o protocolo.

Exemplos de `ai_assisted_production` incluem edição assistida, geração declarada de legendas ou apoio de IA em etapas de produção que não transformem substancialmente o conteúdo audiovisual.

Exemplos de `materially_ai_modified` incluem clonagem de voz, deepfake, face swap, dublagem sintética ou alteração generativa substancial de imagem/vídeo.

## 4. Regra de evidência

Uma classificação positiva para publicação científica exige evidência verificável, preferencialmente:

1. declaração do produtor, instituição ou detentor do conteúdo;
2. proveniência estruturada ou credencial de conteúdo que declare uso de IA;
3. metadados técnicos que documentem a intervenção de IA;
4. documentação oficial associada ao item.

Sinais de detector visual, áudio ou modelo probabilístico podem ser preservados como **evidência auxiliar de triagem**, mas não tornam um item positivo sozinhos.

A aparência visual de um vídeo não é prova suficiente de geração por IA.

## 5. Quantificação

A quantificação usa como denominador principal os **itens avaliáveis**, e não todos os registros brutos encontrados.

Para um conjunto de itens:

- `items_total` = todos os itens observados;
- `items_evaluable` = total menos `not_assessable`;
- `items_with_ai_evidence` = `ai_assisted_production` + `materially_ai_modified` + `partially_synthetic` + `fully_synthetic`;
- `items_materially_ai_changed` = `materially_ai_modified` + `partially_synthetic` + `fully_synthetic`;
- `items_synthetic` = `partially_synthetic` + `fully_synthetic`.

Indicadores derivados:

- **proporção com evidência de IA na produção** = `items_with_ai_evidence / items_evaluable`;
- **proporção materialmente alterada por IA** = `items_materially_ai_changed / items_evaluable`;
- **proporção de conteúdo sintético** = `items_synthetic / items_evaluable`.

A plataforma também pode produzir cortes por:

- instituição/corpus;
- língua;
- período;
- coleção;
- tipo de conteúdo;
- classe de uso de IA;
- força da evidência.

## 6. Relação com `synthetic_video_detection`

`ai_content_production_detection` é a dimensão ampla que identifica o papel da IA na produção do conteúdo.

`synthetic_video_detection` permanece como tarefa mais estreita, destinada a determinar se um item ou segmento é efetivamente sintético. Um conteúdo `ai_assisted_production` não deve ser automaticamente classificado como sintético.

Assim:

- toda evidência de conteúdo sintético implica uso de IA na produção quando a IA for o mecanismo declarado;
- nem todo uso de IA na produção implica conteúdo sintético.

## 7. Validação humana

A pergunta principal é:

**Existe evidência verificável de que inteligência artificial participou da produção ou modificação deste conteúdo audiovisual?**

Quando a resposta for positiva, o revisor classifica o papel da IA em uma das classes do protocolo.

Para `partially_synthetic`, `fully_synthetic` e `materially_ai_modified`, deve ser preservada a evidência que sustenta a intensidade da intervenção.

## 8. Publicação e ressalva

Os indicadores representam detecção computacional calibrada por amostragem humana. Eles não equivalem a perícia forense de autenticidade de cada item.

A interface pública deverá distinguir claramente:

- **IA no funcionamento do acervo**;
- **IA na produção dos conteúdos**;
- **conteúdo sintético**.

Isso permite estudar longitudinalmente não apenas a digitalização e a infraestrutura dos arquivos, mas também a entrada de práticas generativas no próprio patrimônio audiovisual disponibilizado pelas instituições.