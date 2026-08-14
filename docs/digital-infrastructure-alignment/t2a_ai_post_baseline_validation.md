# T2A — validação pós-baseline dos componentes de IA

## 1. Objetivo e separação do baseline

O T2A avalia os componentes experimentais de inteligência artificial depois do congelamento do baseline operacional oficial. Nenhum resultado desta etapa modifica o T2, seus denominadores, os nove indicadores oficiais ou a elegibilidade dos corpora.

A validação não pergunta genericamente se “a IA acertou”. Cada unidade corresponde a uma afirmação observável, respondida pelo revisor sem depender da previsão experimental.

A calibração humana valida o **motor da plataforma**, não cada item ou instituição de forma exaustiva. Depois de validado, o motor executa automaticamente sobre o corpus e permanece sujeito a erros residuais. Revisões posteriores são orientadas por amostragem, risco, mudança de versão e casos de baixa confiança.

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

Na fila T2A v1.x, os valores persistidos permanecem compatíveis com o avaliador existente:

- `positive` = Sim;
- `negative` = Não;
- `not_assessable` = Não foi possível avaliar.

`not_assessable` é uma exceção metodológica. Deve ser usado somente quando a evidência necessária estiver indisponível, inacessível, removida, bloqueada ou tecnicamente insuficiente. Não representa dúvida subjetiva.

Cada unidade deverá registrar:

- `review_status`;
- `human_label`;
- `human_decision`;
- `reviewer_id`;
- `reviewed_at`;
- `validation_url` ou identificador do artefato;
- descrição ou trecho da evidência;
- condição de acesso;
- motivo da impossibilidade, quando aplicável;
- observações adicionais.

## 4. Unidade de observação e exploração institucional controlada

### 4.1 A unidade não é apenas a homepage

A unidade observável do T2A passa a ser a **superfície digital institucional pública**, isto é, um conjunto delimitado e reproduzível de páginas e recursos públicos pertencentes à mesma instituição.

A homepage continua sendo uma semente possível, mas não é tratada como representação suficiente de toda a infraestrutura digital. A exploração pode alcançar páginas internas e subdomínios institucionais, por exemplo páginas de pesquisa, acervo, dados, tecnologia, metadados, documentação, projetos e catálogos.

O objetivo é reduzir falsos negativos causados por informação relevante publicada em superfícies especializadas, como ocorreu na revisão do INA.

### 4.2 Limites técnicos padrão

A implementação canônica está em:

`src/memoria_audiovisual/digital_infrastructure/ai_surface_discovery.py`

Valores padrão:

- profundidade máxima: `2` níveis;
- páginas máximas por instituição: `24`;
- timeout por requisição: `12` segundos;
- resposta processada por página: até `1.500.000` bytes;
- texto processado por página: até `120.000` caracteres;
- respeito a `robots.txt`: habilitado;
- somente `http` e `https`;
- domínio institucional e seus subdomínios;
- sem credenciais, login ou autenticação.

Os limites podem ser ajustados no modo experimental por variáveis de ambiente:

- `AI_SURFACE_DISCOVERY_ENABLED`;
- `AI_SURFACE_MAX_DEPTH`;
- `AI_SURFACE_MAX_PAGES`;
- `AI_SURFACE_TIMEOUT_SECONDS`;
- `AI_SURFACE_MAX_RESPONSE_BYTES`;
- `AI_SURFACE_MAX_TEXT_CHARS`;
- `AI_SURFACE_RESPECT_ROBOTS`.

### 4.3 O que é analisado

A plataforma pode analisar somente informação pública entregue ao cliente, incluindo:

- texto visível do HTML;
- título e metadados da página;
- JSON-LD público;
- links internos;
- elementos estruturais de mídia como `video`, `audio`, `source` e `iframe`;
- URLs públicas expostas pela própria página.

A plataforma **não acessa código de servidor**, áreas privadas ou autenticadas e não contorna CAPTCHA, paywall, geoblocking, login ou outras barreiras de acesso.

Scripts e estilos não são usados como declaração institucional de IA apenas por conterem nomes de bibliotecas ou termos técnicos. A presença de tecnologia no código cliente não equivale, por si só, a uso institucional de inteligência artificial.

### 4.4 Priorização multilíngue de links

A exploração usa vocabulário controlado apenas para **priorizar** links. Ele não transforma uma página em evidência positiva por si só.

O vocabulário inclui, entre outros:

- `film`, `filme`, `película`;
- `video`, `vídeo`;
- `moving image`, `audiovisual`;
- `archive`, `archives`, `arquivo`, `acervo`, `collection`, `fonds`;
- `metadata`, `metadados`, `métadonnées`, `metadatos`;
- termos de IA em português, inglês, espanhol e francês;
- termos de transcrição, reconhecimento, restauração, preservação, pesquisa e catalogação.

A inclusão de `filme` decorre da validação manual da Europeana, na qual esse termo recuperou registros audiovisuais relevantes.

### 4.5 Proveniência da exploração

Cada execução materializa dois produtos separados do baseline oficial:

1. `surface_discovery_report.json` — auditoria completa da exploração;
2. `surface_classifier_text.jsonl` — somente o conteúdo público usado pelo classificador.

O relatório registra, quando aplicável:

- URL;
- URL de origem da descoberta;
- profundidade;
- status HTTP;
- tipo de conteúdo;
- data/hora da coleta;
- SHA-256 do conteúdo processado;
- número de links encontrados;
- truncamento por limite;
- bloqueio por `robots.txt`;
- erro de requisição ou redirecionamento para fora do escopo.

Esses artefatos são experimentais e não modificam o T2.

## 5. Perguntas e regras operacionais

### 5.1 Uso institucional de inteligência artificial

**Pergunta:** A instituição declara publicamente utilizar inteligência artificial em alguma atividade relacionada ao seu acervo audiovisual?

Marcar **Sim** quando existir evidência institucional explícita de uso de IA em pelo menos uma das seguintes atividades:

- catalogação ou descrição;
- indexação ou geração de metadados;
- transcrição, tradução ou legendagem;
- reconhecimento de imagem, fala, rosto ou objetos;
- restauração, preservação ou melhoria técnica;
- busca, recomendação ou acesso ao acervo;
- identificação, segmentação ou classificação de conteúdos;
- geração ou modificação de materiais audiovisuais.

O classificador determinístico v1.1 exige proximidade contextual entre três componentes:

1. termo explícito de IA ou tecnologia equivalente;
2. contexto de acervo/audiovisual;
3. atividade operacional sobre o acervo.

Essa regra evita classificar como uso institucional uma notícia genérica sobre IA, uma API, analytics, automação, chatbot ou simples presença de tecnologia.

Marcar **Não** quando a superfície institucional delimitada tiver sido examinada e nenhuma declaração explícita tiver sido localizada. A resposta significa **“não identificado nas superfícies observadas”**, não prova de inexistência absoluta na instituição.

Não constituem evidência suficiente:

- referências genéricas a tecnologia, algoritmo, automação ou digitalização;
- cookies ou ferramentas de analytics;
- simples presença de chatbot;
- disponibilidade de API;
- inferência baseada apenas no funcionamento do site;
- biblioteca ou script cliente com nome relacionado a IA;
- notícia externa sem vínculo documental com a instituição.

Para uma resposta **Sim**, é obrigatória uma URL institucional, documento oficial, relatório, página de projeto ou notícia publicada pela própria instituição.

### 5.2 Presença pública de registros de acervo audiovisual

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

### 5.3 Presença pública de vídeo reproduzível

**Pergunta:** A superfície analisada permite reproduzir publicamente pelo menos um conteúdo audiovisual do acervo?

Marcar **Sim** quando houver player funcional, link direto de reprodução ou incorporação externa que permita iniciar ao menos parte do conteúdo sem autenticação não pública.

Marcar **Não** quando houver apenas:

- ficha catalográfica;
- imagem ou miniatura;
- botão de reprodução inativo;
- conteúdo disponível somente mediante solicitação formal ou presença física;
- cadastro/login exigido para iniciar a reprodução;
- autenticação institucional não pública;
- trailer ou vídeo institucional sem relação com o acervo;
- link quebrado ou conteúdo removido.

Condições de acesso são registradas separadamente. Vocabulário recomendado:

- `open_online`;
- `geo_restricted`;
- `paid`;
- `registration_required`;
- `restricted_online`;
- `onsite_only`;
- `not_available`.

A restrição geográfica não transforma automaticamente a presença de vídeo em negativa quando a reprodução pública for confirmada em outra região. Nesse caso, registrar `human_label = positive` e `access_condition = geo_restricted`.

Quando a reprodução exigir apenas pagamento público, registrar `human_label = positive` e `access_condition = paid`.

Quando exigir cadastro/login para iniciar a reprodução, registrar `human_label = negative` para a pergunta de reprodução pública e `access_condition = registration_required`.

### 5.4 Conteúdo audiovisual sintético

A tarefa `synthetic_video_detection` não integra a primeira fila porque o T1 coletou sinais em nível de entidade e não produziu unidades item/versão/segmento.

Quando houver amostra adequada, a pergunta será:

**Existe evidência verificável de que este conteúdo audiovisual foi gerado ou materialmente modificado por inteligência artificial?**

Uma impressão visual isolada não será suficiente para uma resposta positiva. Será necessária evidência documental, metadados, declaração do produtor ou análise técnica validada.

## 6. Comparação entre previsão e revisão humana

A matriz binária será calculada somente quando previsão e resposta humana puderem ser convertidas em Sim ou Não.

| Previsão | Humano | Classificação |
|---|---|---|
| Sim | Sim | verdadeiro positivo |
| Sim | Não | falso positivo |
| Não | Sim | falso negativo |
| Não | Não | verdadeiro negativo |

Casos `not_assessable`, erros de execução, previsões ausentes e unidades ainda pendentes são preservados e apresentados separadamente como perda de avaliabilidade ou cobertura. Eles não entram em precisão, revocação ou F1.

## 7. Métricas

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

A conclusão da anotação não ativa automaticamente nenhum componente: cada tarefa recebe uma decisão científica posterior e independente.

## 8. Critério para decisão de ativação

A decisão deverá ser tomada separadamente para:

1. presença institucional de IA;
2. detecção de registros de acervo audiovisual;
3. detecção de presença pública de vídeo;
4. detecção de vídeo sintético, quando existir amostra item a item.

Além das métricas globais, deverão ser examinados falsos positivos e negativos por idioma e tipo institucional, estabilidade entre versões, tempo, custo, cobertura de superfícies e perda de avaliabilidade. A aprovação de uma tarefa não autoriza as demais.

Amostras iniciais muito homogêneas não são suficientes para homologar um detector. É necessário incluir controles positivos e negativos representativos, inclusive casos externos versionados quando o corpus não contiver exemplos adequados.

## 9. Operação futura

A validação integral não será repetida em todas as execuções. Depois da calibração inicial, a revisão será orientada por amostragem e risco, priorizando:

- baixa confiança;
- divergência entre detectores;
- previsões positivas sensíveis;
- nova instituição, língua, região ou tipo de superfície;
- mudança de modelo, prompt ou classificador;
- alteração relevante das páginas ou APIs;
- comportamento diferente do histórico.

As decisões humanas formarão um conjunto de referência versionado e cumulativo. Casos já revisados poderão ser reutilizados para comparar versões sem nova anotação, salvo quando a evidência, a superfície observada ou a pergunta operacional mudar.

A interface pública deve informar que os resultados são produzidos automaticamente por mecanismos computacionais validados por amostragem humana e que **não representam verificação manual exaustiva de cada item ou instituição**. Erros residuais de detecção permanecem possíveis.