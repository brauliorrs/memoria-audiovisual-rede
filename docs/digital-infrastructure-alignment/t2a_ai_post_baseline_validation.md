# T2A — validação pós-baseline dos componentes de IA

## 1. Objetivo e separação do baseline

O T2A avalia os componentes experimentais de inteligência artificial depois do congelamento do baseline operacional oficial. Nenhum resultado desta etapa modifica o T2, seus denominadores, os nove indicadores oficiais ou a elegibilidade dos corpora.

A validação não pergunta genericamente se “a IA acertou”. Cada unidade corresponde a uma afirmação observável, respondida pelo revisor sem depender da previsão experimental.

## 2. Fila inicial de revisão

A fila canônica está em:

`data/digital_infrastructure/ai_experiments/t2a_human_review_queue_v1.json`

Ela foi derivada do artefato do ciclo integral T1 (`full-observatory-cycle-31038017955`) e contém 18 unidades:

- seis entidades da amostra inicial;
- três tarefas com registros no T1;
- 15 previsões experimentais reais;
- três lacunas explícitas do APE, cujo coletor falhou antes da geração dos sinais experimentais.

As lacunas não recebem previsão presumida.

## 3. Respostas humanas padronizadas

As respostas exibidas ao revisor são:

- **Sim**;
- **Não**;
- **Não foi possível avaliar**.

Os valores armazenados são, respectivamente:

- `yes`;
- `no`;
- `not_assessable`.

`not_assessable` é uma exceção metodológica. Deve ser usado somente quando a evidência necessária estiver indisponível, inacessível, removida, bloqueada por autenticação ou tecnicamente insuficiente. Não representa dúvida subjetiva.

Cada unidade deverá registrar:

- `review_status`;
- `human_label`;
- `human_decision`;
- `reviewer_id`;
- `reviewed_at`;
- `evidence_url` ou identificador do artefato;
- descrição ou trecho da evidência;
- condição de acesso;
- motivo da impossibilidade, quando aplicável;
- observações adicionais.

## 4. Perguntas e regras operacionais

### 4.1 Uso institucional de inteligência artificial

**Pergunta:** A instituição declara publicamente utilizar inteligência artificial em alguma atividade relacionada ao seu acervo audiovisual?

Marcar **Sim** quando existir evidência institucional explícita de uso de IA em pelo menos uma das seguintes atividades:

- catalogação ou descrição;
- indexação ou geração de metadados;
- transcrição, tradução ou legendagem;
- reconhecimento de imagem, fala, rosto ou objetos;
- restauração, preservação ou melhoria técnica;
- busca, recomendação ou acesso ao acervo;
- identificação ou classificação de conteúdos;
- geração ou modificação de materiais audiovisuais.

Marcar **Não** quando as superfícies previstas tiverem sido examinadas e nenhuma declaração explícita tiver sido encontrada.

Não constituem evidência suficiente:

- referências genéricas a tecnologia, algoritmo, automação ou digitalização;
- cookies ou ferramentas de analytics;
- simples presença de chatbot;
- disponibilidade de API;
- inferência baseada no funcionamento do site;
- notícia externa sem vínculo documental com a instituição.

Para uma resposta **Sim**, é obrigatória uma URL institucional, documento oficial, relatório, página de projeto ou notícia publicada pela própria instituição.

### 4.2 Presença pública de registros de acervo audiovisual

**Pergunta:** A superfície pública analisada apresenta registros identificáveis de obras ou documentos audiovisuais pertencentes ao acervo da instituição?

Marcar **Sim** quando existir pelo menos um registro identificável contendo elementos como título, descrição, data, duração, autoria, identificador, miniatura, ficha catalográfica ou indicação inequívoca de filme, vídeo, programa televisivo, cinejornal ou gravação audiovisual.

Não é necessário que o vídeo esteja disponível para reprodução.

Marcar **Não** quando a superfície apresentar somente:

- informações institucionais;
- notícias, eventos ou conteúdo promocional;
- fotografias ou imagens sem obra audiovisual identificável;
- menção abstrata à existência de um acervo;
- formulário de solicitação sem registros públicos consultáveis.

Esta variável mede presença pública de registros na superfície examinada. Não mede a existência histórica, administrativa ou física de acervo fora dessa superfície.

### 4.3 Presença pública de vídeo reproduzível

**Pergunta:** A superfície analisada permite reproduzir publicamente pelo menos um conteúdo audiovisual do acervo?

Marcar **Sim** quando houver player funcional, link direto de reprodução ou incorporação externa que permita iniciar ao menos parte do conteúdo.

Marcar **Não** quando houver apenas:

- ficha catalográfica;
- imagem ou miniatura;
- botão de reprodução inativo;
- conteúdo disponível somente mediante solicitação formal ou presença física;
- autenticação institucional não pública;
- trailer ou vídeo institucional sem relação com o acervo;
- link quebrado ou conteúdo removido.

Quando a reprodução pública exigir pagamento, registrar:

- `human_label = yes`;
- `access_condition = paid`.

A existência de vídeo reproduzível e sua gratuidade são variáveis diferentes.

### 4.4 Conteúdo audiovisual sintético

A tarefa `synthetic_video_detection` não integra a primeira fila porque o T1 coletou sinais em nível de entidade e não produziu unidades item/versão/segmento.

Quando houver amostra adequada, a pergunta será:

**Existe evidência verificável de que este conteúdo audiovisual foi gerado ou materialmente modificado por inteligência artificial?**

Uma impressão visual isolada não será suficiente para uma resposta positiva. Será necessária evidência documental, metadados, declaração do produtor ou análise técnica validada.

## 5. Comparação entre previsão e revisão humana

A matriz binária será calculada somente quando previsão e resposta humana puderem ser convertidas em `yes` ou `no`.

| Previsão | Humano | Classificação |
|---|---|---|
| Sim | Sim | verdadeiro positivo |
| Sim | Não | falso positivo |
| Não | Sim | falso negativo |
| Não | Não | verdadeiro negativo |

Casos `not_assessable`, erros de execução, previsões ausentes e unidades ainda pendentes são preservados e apresentados separadamente como perda de avaliabilidade ou cobertura. Eles não entram em precisão, revocação ou F1.

## 6. Métricas

O avaliador calcula, por tarefa e no agregado:

- verdadeiros positivos;
- falsos positivos;
- verdadeiros negativos;
- falsos negativos;
- precisão;
- revocação;
- F1;
- proporção de unidades não avaliáveis;
- cobertura efetivamente comparável.

Também produz cortes por:

- idioma;
- geografia;
- tipo de instituição ou estrato analítico.

O relatório permanece em estado `pending_human_review` enquanto houver unidades pendentes. A conclusão da anotação não ativa automaticamente nenhum componente: cada tarefa recebe uma decisão científica posterior e independente.

## 7. Critério para decisão de ativação

A decisão deverá ser tomada separadamente para:

1. presença institucional de IA;
2. detecção de registros de acervo audiovisual;
3. detecção de presença pública de vídeo;
4. detecção de vídeo sintético, quando existir amostra item a item.

Além das métricas globais, deverão ser examinados falsos positivos e negativos por idioma e tipo institucional, estabilidade entre versões, tempo, custo e perda de avaliabilidade. A aprovação de uma tarefa não autoriza as demais.

## 8. Operação futura

A validação integral não será repetida em todas as execuções. Depois da calibração inicial, a revisão será orientada por amostragem e risco, priorizando:

- baixa confiança;
- divergência entre detectores;
- previsões positivas sensíveis;
- nova instituição, língua, região ou tipo de superfície;
- mudança de modelo, prompt ou classificador;
- alteração relevante das páginas ou APIs;
- comportamento diferente do histórico.

As decisões humanas formarão um conjunto de referência versionado e cumulativo. Casos já revisados poderão ser reutilizados para comparar versões sem nova anotação, salvo quando a evidência ou a pergunta operacional mudar.