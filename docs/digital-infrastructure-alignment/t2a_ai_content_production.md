# T2A — IA na produção do conteúdo audiovisual

## 1. Pergunta científica

Esta dimensão responde a uma pergunta diferente do uso institucional de IA:

> **Existe evidência verificável de que a inteligência artificial participou da produção ou modificação deste item audiovisual?**

Uma instituição pode usar IA para pesquisar, catalogar, transcrever ou restaurar o acervo sem que os itens disponibilizados tenham sido produzidos com IA. Da mesma forma, um item pode incorporar IA em sua produção sem que a instituição mantenha um programa institucional de IA para gestão do acervo.

As duas dimensões permanecem separadas em armazenamento, validação e apresentação.

## 2. Unidade analítica

A unidade obrigatória é um **item, versão ou segmento audiovisual**. Classificações em nível de instituição não são suficientes para inferir que seus conteúdos foram produzidos com IA.

Cada unidade deve preservar, quando disponível:

- instituição/corpus;
- identificador estável do item;
- URL pública do item;
- versão ou segmento;
- título e descrição;
- idioma;
- data/período;
- fonte da evidência;
- força da evidência;
- classe atribuída;
- versão do protocolo e do classificador.

## 3. Classes operacionais v1

- `no_verified_ai_evidence` — nenhuma evidência verificável de IA na produção foi identificada nas superfícies avaliadas;
- `ai_assisted_production` — IA participou do fluxo de produção, mas não há evidência de transformação material ou geração sintética suficiente para uma classe mais forte;
- `materially_ai_modified` — IA modificou materialmente imagem, voz, vídeo ou outro componente do item;
- `partially_synthetic` — parte identificável do item foi gerada por IA;
- `fully_synthetic` — o item é declarado como integralmente gerado por IA;
- `not_assessable` — a evidência necessária não pôde ser avaliada.

`synthetic_video_detection` permanece uma tarefa mais estreita. Todo conteúdo sintético implica participação de IA na produção segundo este protocolo, mas nem toda participação de IA produz conteúdo sintético.

## 4. Evidência mínima

Uma classificação positiva para uso científico exige evidência verificável, preferencialmente:

1. declaração do produtor, instituição responsável ou criador;
2. proveniência estruturada;
3. metadados técnicos que documentem a participação de IA;
4. documentação institucional ou fonte independente de alta confiabilidade vinculada ao item.

Sinais visuais, classificadores probabilísticos e detectores de conteúdo sintético podem ser usados como **triagem**, mas não são prova suficiente isoladamente.

Menções ao tema “inteligência artificial” dentro do conteúdo não constituem evidência de que o item tenha sido produzido com IA. Da mesma forma, animação, CGI, programação, automação ou restauração digital não devem ser convertidos automaticamente em uso de IA.

## 5. Benchmark de referência 3×3

A amostra canônica está em:

`data/digital_infrastructure/ai_experiments/ai_content_validation_sample_v1.json`

O relatório está em:

`data/digital_infrastructure/ai_experiments/ai_content_validation_report_v1.json`

O benchmark contém seis controles conhecidos:

- três positivos;
- três negativos;
- inglês e espanhol;
- classes `ai_assisted_production`, `partially_synthetic`, `fully_synthetic` e `no_verified_ai_evidence`.

Casos positivos iniciais incluem:

- **TeledIArio del futuro (RTVE, 2026)** — a RTVE documenta partes realizadas com IA, versão sintética da apresentadora e recriações históricas geradas com IA;
- **Tokinokawa (BFI, 2021)** — o BFI documenta uso de software de IA para analisar imagens e compor uma camada infográfica animada;
- **DreadClub: Vampire's Verdict (2024)** — controle externo descrito pelo BFI como longa de animação integralmente gerado por IA.

Os negativos incluem um Telediario contemporâneo sem declaração de IA na produção e dois filmes históricos do BFI.

O benchmark é um conjunto de **controles de calibração**. Não é uma amostra de prevalência e seus resultados não podem ser apresentados como porcentagem de IA no corpus.

## 6. Amostra cega real do corpus

A fila está em:

`data/digital_infrastructure/ai_experiments/ai_content_blind_review_queue_v1.json`

Ela contém 12 itens reais já materializados pelos coletores:

- 3 BFI;
- 3 INA;
- 3 ARCHIPOP;
- 3 AAPB.

A seleção é uma amostra de desafio, não probabilística. Inclui deliberadamente casos capazes de provocar confusão semântica, por exemplo:

- um programa do INA cujo assunto é “intelligence artificielle”, sem que isso prove participação de IA na produção;
- um filme de animação do ARCHIPOP, evitando a inferência “animação = IA”;
- um vídeo do BFI que usa programação computacional, sem evidência de IA.

### 6.1 Cegueira da revisão

A fila humana não contém:

- previsão do modelo;
- confiança;
- status automático;
- classe prevista.

As previsões são geradas separadamente por:

`scripts/assess_ai_content_blind_queue.py`

Somente depois da anotação humana os dois conjuntos devem ser unidos para calcular desempenho.

## 7. Protocolo de superfície do item

O modo padrão do script faz triagem apenas com metadados já materializados.

O modo `--fetch-surfaces` consulta a página pública do item com:

- profundidade `0`;
- uma página por item;
- respeito a `robots.txt`;
- sem login, credenciais ou contorno de barreiras;
- materialização de URL, timestamp e hash pela infraestrutura de descoberta de superfícies.

A página inteira não é tratada indiscriminadamente como descrição do item. Metadados e JSON-LD são preservados, enquanto o texto visível é recortado em torno do título do item quando possível. Isso reduz falsos positivos produzidos por menus, rodapés e recomendações de conteúdos relacionados.

Como a execução depende de sites externos, ela não bloqueia o CI principal. O workflow manual é:

`.github/workflows/t2a-ai-content-surface-assessment.yml`

## 8. Quantificação

A plataforma pode calcular:

- `share_with_ai_evidence` — itens com qualquer evidência positiva / itens avaliáveis;
- `share_materially_ai_changed` — itens materialmente modificados ou sintéticos / itens avaliáveis;
- `share_synthetic` — itens parcial ou integralmente sintéticos / itens avaliáveis;
- contagem por classe;
- cortes por instituição, idioma e período.

O denominador **não pode incluir automaticamente itens não avaliados**. `not_assessable` permanece fora das proporções e deve ser reportado separadamente.

## 9. Quando a prevalência poderá ser publicada

Nenhum dos dois conjuntos iniciais — benchmark 3×3 ou amostra cega de 12 itens — permite inferir prevalência de IA no corpus.

Uma porcentagem científica de uso de IA na produção só poderá ser publicada após:

1. estabilização do protocolo e da taxonomia;
2. validação humana do motor em controles positivos e negativos;
3. definição explícita do universo de itens elegíveis;
4. amostragem probabilística/estratificada ou cobertura integral definida;
5. registro da fração não avaliável;
6. apresentação de incerteza e erro residual do classificador;
7. versionamento temporal para permitir comparação longitudinal.

## 10. Relação com o T2

Toda esta dimensão permanece pós-baseline e experimental.

- não modifica os 55 corpora ativos;
- não altera os nove indicadores oficiais do T2;
- não muda denominadores históricos;
- não reescreve o T1;
- produz artefatos próprios e versionados.

Quando a tarefa for homologada cientificamente, ela poderá gerar um novo indicador longitudinal claramente identificado como resultado computacional validado por amostragem humana, com ressalva explícita de erro residual.
