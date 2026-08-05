# Protocolo de evidências públicas de IA e automação

## Escopo

Este protocolo orienta o registro de evidências públicas sobre aplicações de IA ou automação ligadas à preservação, descrição, busca, acesso, recomendação, direitos ou circulação audiovisual.

O objeto observado é a **evidência pública disponível na superfície examinada**, não a totalidade dos sistemas internos da instituição. Nenhum resultado negativo autoriza afirmar que a instituição não utiliza IA.

## Separação obrigatória dos objetos de IA

O projeto distingue três objetos que não podem compartilhar automaticamente o mesmo indicador ou denominador:

1. **IA utilizada pela instituição** — sistemas e ferramentas empregados pelo arquivo ou agregador e suas funções;
2. **IA utilizada pelo observatório** — modelos empregados para apoiar triagem, detecção de acervo e localização de vídeo público;
3. **conteúdo audiovisual gerado ou modificado por IA** — propriedade observada em um item, versão, segmento, faixa de áudio ou elemento visual.

Uso institucional de IA não prova que a instituição custodie vídeos gerados por IA. Presença de vídeos sintéticos não prova que o arquivo utilize IA em seus processos. IA usada pelo observatório para detectar evidências não deve ser atribuída à instituição observada.

Restauração, colorização, transcrição, recomendação e enriquecimento de metadados devem permanecer separados da geração sintética do conteúdo. Detectores probabilísticos de vídeo sintético servem para triagem e não podem, isoladamente, sustentar afirmação pública conclusiva.

## Unidade de observação

Cada registro deve vincular:

1. instituição, projeto, sistema ou processo observado;
2. função concreta atribuída à IA ou automação;
3. URL ou documento de evidência;
4. trecho ou elemento técnico que sustenta a classificação;
5. data e método da observação;
6. idioma da evidência;
7. estágio declarado ou inferível com segurança;
8. status de validação e responsável pela revisão.

Menções genéricas a inovação, transformação digital, inteligência artificial ou automação não contam como evidência de uso concreto.

## Estados avaliativos

Os estados devem permanecer distintos:

- `detected_pending_review`: sinal encontrado, ainda não validado;
- `verified_public_evidence`: evidência pública revisada e compatível com a classificação;
- `ambiguous`: evidência insuficiente ou sujeita a mais de uma interpretação;
- `not_identified`: nenhuma evidência foi encontrada nas superfícies e pelo procedimento declarados;
- `not_assessable`: bloqueio, rota inadequada, idioma, formato ou cobertura impedem classificação válida;
- `error`: falha técnica da observação;
- `withdrawn_or_corrected`: classificação anterior retirada ou corrigida com preservação do histórico.

`not_identified`, `not_assessable` e `error` nunca devem ser publicados como ausência institucional de IA.

## Funções controladas

`automatic_transcription`, `speech_to_text`, `ocr`, `image_recognition`, `face_recognition`, `object_detection`, `automatic_translation`, `metadata_enrichment`, `entity_extraction`, `recommendation`, `search_ranking`, `content_moderation`, `rights_detection`, `restoration`, `classification`, `other`.

## Estágio declarado ou documentado

`announced`, `research`, `pilot`, `operational`, `discontinued`, `unknown`.

A classificação do estágio deve refletir a fonte. Projeto de pesquisa, anúncio institucional e serviço operacional são categorias diferentes.

## Campos essenciais

- `ai_system_id`;
- `institution_id`;
- `ai_system_name`;
- `ai_provider`;
- `ai_function`;
- `ai_model_type`;
- `deployment_stage`;
- `human_oversight`;
- `training_data_disclosure`;
- `automated_output_public`;
- `algorithmic_transparency`;
- `impact_area`;
- `evidence_id`;
- `validation_status`.

Campos desconhecidos permanecem desconhecidos. Não devem ser preenchidos por inferência a partir de linguagem promocional ou bibliotecas técnicas genéricas.

## Regras de cautela

- não inferir fornecedor a partir de biblioteca JavaScript, CDN ou componente genérico;
- distinguir automação baseada em regras de aprendizado de máquina apenas quando a fonte permitir;
- registrar reconhecimento facial e biometria em categoria própria e sob revisão sensível;
- não presumir que o acervo institucional foi usado para treinamento;
- separar ferramenta experimental, projeto de pesquisa, piloto e sistema operacional;
- não interpretar ausência de transparência documental como prova de ausência de supervisão ou governança;
- preservar URL, trecho, data, método e versão do vocabulário;
- revisar positivos e amostras negativas para estimar falsos positivos e falsos negativos;
- exigir revisão humana antes de qualquer indicador público.

## Relação com indicadores

Este protocolo, isoladamente, não cria um indicador científico. Uma medida pública sobre IA somente poderá ser ativada quando houver:

1. população elegível e denominador avaliável definidos;
2. metodologia versionada;
3. vocabulário e procedimento de busca documentados;
4. cobertura publicada;
5. revisão de positivos e amostra de negativos;
6. limites interpretativos explícitos;
7. registro no `indicator_registry.json` e no `methodology_registry.json`.

Até essa ativação, os registros de IA permanecem evidências e objetos curatoriais, não resultados consolidados sobre adoção institucional.
