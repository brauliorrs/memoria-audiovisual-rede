# Project Backlog

Este backlog separa consolidação operacional, expansão científica e melhorias de apresentação. A auditoria que fundamenta as prioridades atuais está em:

`docs/audit/platform_integration_expansion_audit_2026-08-05.md`

A interpretação científica da expansão, do limiar de prontidão e da sequência continental está documentada em:

`docs/research/05a_scientific_expansion_policy.md`

## P0 — consistência do corpus, das filas e dos denominadores

**Estado:** concluído nesta rodada; monitoramento automático permanente.

### Estado validado

- corpus científico de referência: **58 entidades**;
- corpus operacional ativo global: **55 entidades**;
- corpus operacional ativo europeu: **54 entidades**;
- corpus ativo extraeuropeu: **1 entidade**, o American Archive of Public Broadcasting — AAPB;
- entidades inativas: **3**;
- composição do corpus de referência: **7 agregadores** e **51 arquivos ou instituições**;
- fila europeia vigente: `observatorio_fila_pesquisa_europa.csv`, com **118 registros e 24 campos**;
- fila de fechamento v1: 6 registros, mantida apenas como histórico.

O total de 54 no resumo europeu é correto. Ele representa o recorte geográfico europeu dos 55 corpora ativos globais e exclui o AAPB, incorporado como primeiro corpus norte-americano.

### Concluído

1. os três produtos europeus foram regenerados pelo gerador canônico:
   - `observatorio_pesquisa_europa.csv`;
   - `observatorio_fila_pesquisa_europa.csv`;
   - `observatorio_resumo_pesquisa_europa.csv`;
2. a regeneração não produziu diferença nos CSVs, confirmando que o estado materializado já correspondia ao código canônico;
3. foi criado `scripts/sync_europe_research_outputs.py`, com modo de escrita e modo `--check`;
4. o sincronizador compara semanticamente os três CSVs com os DataFrames reconstruídos pelo código atual;
5. a validação confere separadamente o total global e o total europeu;
6. corpora extraeuropeus são impedidos de entrar silenciosamente no denominador europeu;
7. códigos duplicados, versões de regra misturadas e ranking descontínuo passam a bloquear o CI;
8. os testes simulam uma alteração indevida no denominador e confirmam que ela é rejeitada;
9. o workflow `Quality Checks` executa a validação em cada mudança;
10. `observatorio_fila_fechamento_europa.csv` permanece classificado como artefato histórico, não operacional.

### Critério de conclusão

Registro, fila, resumo e corpus canônico apresentam denominadores coerentes com seus respectivos recortes geográficos, e o CI bloqueia alterações não regeneradas ou cientificamente inconsistentes.

## P1 — primeiro ciclo operacional completo

**Estado:** próxima prioridade executiva.

O último ciclo registrado, concluído em **21 de julho de 2026**, foi parcial e processou apenas `home-movies-memoryscapes`. A linha do tempo não contém um ciclo completo dos 55 corpora ativos globais.

A linha do tempo demonstra alguma execução para 36 códigos únicos; 19 corpora ativos não aparecem nesse histórico de ciclos.

### Ações

1. executar ciclo integral dos 55 corpora ativos;
2. manter falhas, ausências e estados não avaliáveis explicitamente registrados;
3. gerar manifesto do ciclo completo;
4. atualizar linha do tempo e resultados por corpus;
5. verificar se todos os corpora ativos possuem snapshot e observation key;
6. produzir relatório formal de validação operacional;
7. congelar o primeiro baseline operacional completo.

### Critério de conclusão

Todos os 55 corpora ativos aparecem em um ciclo completo, com resultado, falha ou estado não avaliável auditável.

## P2 — materialização da infraestrutura já implementada

**Estado:** código existente; produtos operacionais incompletos.

### Produtos científicos

Implementado:

- registros de indicadores e metodologia;
- snapshot de referência de 58 corpora;
- cobertura de referência;
- nove resultados científicos materializados;
- interface Infraestrutura Científica nos três idiomas.

Ainda não materializado operacionalmente:

- `data/output/controlled_validation_summary.json`;
- snapshot vivo em `data/output/analytics/<snapshot>`;
- `data/output/analytics/indicator_history.jsonl`;
- `data/digital_infrastructure/ledger.jsonl`;
- `data/digital_infrastructure/ingestion_batches.jsonl`.

### Ações

1. executar a validação controlada sobre `europeana`, `ina` e `bfi`;
2. persistir cobertura, manifesto, run, sensibilidade e nove indicadores;
3. iniciar histórico append-only de indicadores;
4. materializar ledger e lotes de ingestão;
5. fazer a Infraestrutura Científica distinguir claramente snapshot de referência e snapshot operacional;
6. impedir que ausência de artefato operacional seja apresentada como resultado empírico.

### Critério de conclusão

A interface consegue carregar um snapshot operacional reproduzível, com proveniência, hashes, histórico, ledger e lote de ingestão.

## P2A — indicadores experimentais relacionados à inteligência artificial

**Estado:** não implantado; protocolo de evidências de IA existente, metodologia, modelo, validação e integração analítica pendentes.

A plataforma deverá estudar o uso de inteligência artificial como apoio à identificação de sinais que os detectores determinísticos não conseguem classificar com segurança. O protocolo geral de cautela e evidência está documentado em:

`docs/digital-infrastructure-alignment/ai_systems_protocol.md`

### Separação obrigatória dos objetos de IA

A plataforma deverá manter três dimensões científicas independentes:

1. **uso institucional de ferramentas de IA pelo arquivo ou agregador** — verifica se a instituição declara ou documenta uso de IA, quais ferramentas, modelos ou fornecedores utiliza, para quais funções e em qual estágio de implantação;
2. **uso de IA pela própria plataforma para detectar acervo audiovisual e presença pública de vídeo** — mecanismo de apoio à triagem do observatório, sem atribuir esse uso à instituição observada;
3. **detecção de vídeos gerados, sintetizados ou materialmente modificados por IA** — classificação aplicada ao item audiovisual, à versão ou ao segmento, e não à instituição como um todo.

Essas dimensões não podem compartilhar automaticamente o mesmo indicador, denominador ou conclusão. Um arquivo pode utilizar IA em transcrição ou restauração e não custodiar vídeos gerados por IA. Também pode custodiar vídeos sintéticos sem utilizar IA em seus próprios processos. A IA empregada pelo observatório nunca deverá ser atribuída ao arquivo analisado.

### P2A.1 — presença institucional de ferramentas de IA e identificação das ferramentas

A plataforma deverá verificar separadamente:

- se existe evidência pública de uso institucional de IA ou aprendizado de máquina;
- quais ferramentas, sistemas, modelos, fornecedores ou componentes são mencionados;
- quais funções são desempenhadas, como transcrição, OCR, tradução, reconhecimento de imagem, descrição automática, enriquecimento de metadados, extração de entidades, busca, recomendação, detecção de direitos, restauração, colorização, geração de conteúdo ou moderação;
- se o uso está anunciado, em pesquisa, em piloto, operacional ou descontinuado;
- se há supervisão humana, documentação, transparência e mecanismo de contestação.

A presença de uma biblioteca, CDN, componente genérico ou linguagem promocional não constitui prova de uso institucional de IA. Nome, fornecedor, versão, função, estágio, fonte pública e data da evidência deverão ser preservados. Quando a ferramenta não puder ser identificada, o campo permanecerá desconhecido.

Estados mínimos:

- `verified_institutional_ai_use`;
- `detected_pending_review`;
- `declared_without_technical_detail`;
- `ambiguous`;
- `not_identified_on_assessed_surfaces`;
- `not_assessable`;
- `error`;
- `discontinued`;
- `withdrawn_or_corrected`.

`not_identified_on_assessed_surfaces` não significa que a instituição não utiliza IA. Significa apenas que o procedimento declarado não encontrou evidência pública suficiente.

### P2A.2 — IA da plataforma para detectar acervo e presença pública de vídeo

O componente não deverá ser implementado como uma única classificação genérica. Ele deverá produzir duas avaliações independentes e complementares:

1. **detecção de evidência de acervo audiovisual** — identifica sinais de que a instituição preserva, descreve, disponibiliza ou administra coleção audiovisual, mesmo quando o site não utiliza terminologia padronizada;
2. **detecção de presença pública de vídeo** — identifica sinais de vídeo reproduzível ou publicamente exposto nas superfícies observadas, distinguindo página institucional, ficha de catálogo, player incorporado, arquivo de mídia, streaming e simples menção textual.

### Fontes observáveis

A IA poderá analisar, sempre dentro das rotas públicas e autorizadas:

- texto de páginas institucionais e páginas de coleção;
- títulos, descrições, assuntos, gêneros e tipos documentais;
- metadados estruturados e não estruturados;
- resultados de busca interna;
- documentos públicos e trechos extraídos;
- textos alternativos, legendas e transcrições disponíveis;
- elementos de interface associados a player ou reprodução;
- miniaturas e imagens públicas, quando a análise visual for metodologicamente aprovada;
- códigos de incorporação e referências a YouTube, Vimeo, IIIF AV, HLS, DASH, MP4, WebM ou formatos equivalentes;
- evidências já produzidas pelos detectores determinísticos.

A análise de imagens ou miniaturas não autoriza reconhecimento de pessoas, identificação biométrica ou inferência sensível. Reconhecimento facial permanecerá fora deste indicador.

### Estados avaliativos separados

Cada uma das duas tarefas deverá preservar estados como:

- `detected_pending_review`;
- `verified_public_evidence`;
- `ambiguous`;
- `not_identified_on_assessed_surfaces`;
- `not_assessable`;
- `error`;
- `withdrawn_or_corrected`.

`not_identified_on_assessed_surfaces` significa apenas que o procedimento declarado não encontrou evidência nas superfícies examinadas. Não significa ausência de acervo audiovisual nem ausência de vídeo em toda a instituição.

### Campos mínimos de proveniência

Cada resultado deverá registrar:

- `entity_id` e `observation_id`;
- tarefa executada: `audiovisual_collection_detection` ou `public_video_presence_detection`;
- URL e superfície analisada;
- idioma do conteúdo;
- evidência textual, estrutural ou visual que sustentou a classificação;
- detector determinístico relacionado;
- modelo, fornecedor, versão e configuração;
- versão do prompt ou do classificador;
- data e duração da execução;
- classe prevista e nível de confiança;
- justificativa produzida para revisão;
- decisão do revisor humano;
- estado final e referência da correção, quando houver.

A confiança do modelo não poderá ser convertida diretamente em evidência científica positiva ou negativa.

### Validação obrigatória

Antes de integrar os resultados ao catálogo científico, será necessário:

1. construir amostra-ouro multilíngue, estratificada por continente, país, tipo de instituição, agregador e arquivo individual;
2. incluir casos positivos, negativos, ambíguos, bloqueados e sem evidência suficiente;
3. comparar a IA com os detectores determinísticos e com avaliação humana independente;
4. medir precisão, revocação, F1, matriz de confusão e desempenho por idioma e tipo de instituição;
5. estimar falsos positivos e falsos negativos separadamente para acervo e vídeo;
6. testar estabilidade entre versões do modelo e do prompt;
7. definir limiar de encaminhamento para revisão, sem aprovação automática;
8. avaliar custo, tempo, privacidade, reprodutibilidade e dependência de fornecedor;
9. documentar vieses linguísticos, geográficos e tecnológicos;
10. realizar revisão humana de todos os positivos e de amostra controlada dos negativos;
11. versionar metodologia, vocabulário, modelo e cobertura;
12. registrar o indicador em `indicator_registry.json` e `methodology_registry.json` somente após aprovação científica.

### Relação com a fila de expansão

A IA poderá apoiar a triagem da fila ao:

- priorizar páginas que apresentam sinais de acervo audiovisual;
- localizar termos e descrições equivalentes em diferentes idiomas;
- sugerir fichas ou superfícies com possível player;
- identificar casos ambíguos que precisam de revisão humana;
- reduzir trabalho manual repetitivo na descoberta de evidências.

Ela não poderá:

- incluir ou excluir automaticamente candidatos;
- definir elegibilidade científica;
- alterar `CORPORA` ou `organism_active`;
- transformar ausência de detecção em negativa metodológica;
- substituir o gate de elegibilidade ou a decisão curatorial;
- publicar resultados institucionais sem revisão.

### P2A.3 — detecção de vídeos gerados ou modificados por IA

Este eixo deverá analisar a origem e o processo de produção do conteúdo audiovisual observado, independentemente do uso institucional de IA.

As classes deverão permanecer separadas:

- `declared_fully_ai_generated_video` — vídeo declarado como integralmente gerado ou sintetizado por IA;
- `declared_partially_ai_generated_video` — partes visuais ou sonoras foram geradas por IA;
- `declared_ai_assisted_production` — IA auxiliou roteiro, edição, composição ou outro estágio sem caracterizar necessariamente geração do vídeo;
- `ai_restored_or_enhanced_video` — restauração, interpolação, redução de ruído, colorização ou aumento de resolução;
- `synthetic_voice_or_audio` — voz, fala, música ou efeitos sonoros sintéticos;
- `synthetic_image_or_avatar` — imagens, personagens, avatares ou cenas sintéticas;
- `suspected_ai_generated_pending_review` — sinal técnico ou visual ainda não confirmado;
- `no_public_evidence_of_ai_generation`;
- `not_assessable`;
- `error`;
- `withdrawn_or_corrected`.

Restauração, colorização, transcrição, recomendação ou enriquecimento de metadados não deverão ser classificados automaticamente como “vídeo feito por IA”. O indicador deverá distinguir geração integral, geração parcial, assistência de produção, modificação material e uso de IA apenas em processos auxiliares.

A classificação deverá priorizar:

1. declaração explícita do produtor, arquivo, catálogo ou detentor responsável;
2. metadados de proveniência, credenciais de conteúdo ou documentação técnica verificável;
3. ficha catalográfica, créditos, notas de produção ou documentação de aquisição;
4. marca d’água, identificador ou informação técnica associada ao conteúdo;
5. análise forense ou detector automatizado validado;
6. avaliação humana especializada.

Nenhum detector probabilístico poderá, isoladamente, produzir a afirmação pública de que um vídeo foi gerado por IA. A confiança do modelo será evidência de triagem, não prova de autoria ou processo de produção.

A unidade de análise poderá ser o item completo, uma versão, um segmento temporal, uma faixa de áudio, um quadro ou um elemento sintético incorporado. A presença de um elemento sintético não autoriza classificar automaticamente todo o vídeo como integralmente gerado por IA.

### Produtos a implementar

1. definir três contratos independentes: uso institucional de IA, IA de triagem do observatório e detecção de vídeo sintético;
2. criar vocabulário controlado de ferramentas, funções e estágios institucionais;
3. criar vocabulário controlado de geração, assistência, restauração e modificação audiovisual;
4. criar conjuntos de treinamento e avaliação independentes, com proveniência e licença compatíveis;
5. implementar baseline determinístico e documental para comparação;
6. testar classificador textual multilíngue;
7. testar detecção estrutural de players, embeds e formatos de vídeo;
8. avaliar detectores de conteúdo sintético e, em etapa separada, se análise visual agrega valor mensurável;
9. criar fila de revisão humana e interface de confirmação;
10. persistir evidências, confiança, versão do modelo e decisão final;
11. produzir relatórios separados por tarefa, idioma, continente e tipo de instituição;
12. executar estudo de sensibilidade de limiares;
13. integrar os resultados validados aos snapshots sem sobrescrever observações históricas;
14. criar visualizações que não misturem adoção institucional, triagem automatizada e vídeo sintético;
15. documentar as três metodologias no livro científico antes da ativação pública;
16. manter os indicadores desativados no catálogo analítico até o cumprimento dos critérios específicos de validação.

### Critério de conclusão

A implantação somente será considerada concluída quando a plataforma conseguir responder separadamente:

1. se há evidência pública de que o arquivo utiliza ferramentas de IA, quais são e para quais funções;
2. se a IA do observatório identificou evidência de acervo audiovisual ou presença pública de vídeo, com revisão humana;
3. se um item, versão ou segmento audiovisual possui evidência verificável de geração ou modificação por IA, distinguindo geração integral, geração parcial, assistência e restauração.

As três tarefas deverão possuir amostras de validação, métricas, metodologias e versões próprias. Até esse ponto, os resultados permanecerão experimentais e não poderão fundamentar afirmações públicas conclusivas sobre uma instituição ou um vídeo.

## P3 — operacionalização segura da fila europeia

**Estado:** fila disponível; sondagem e gate ainda não operacionalizados.

### Estrutura existente

- 118 registros na fila europeia;
- 5 fontes de descoberta nas primeiras posições;
- 73 candidatos na fila definitiva um a um;
- 30 agregadores nacionais ou regionais em radar;
- 8 agregadores temáticos em radar contextual;
- código de sondagem técnica;
- gate de elegibilidade científica;
- testes estruturais;
- proibição de promoção automática para `CORPORA`.

### Produtos ausentes

- `observatorio_sondagem_tecnica_fila_europa.json`;
- `observatorio_elegibilidade_fila_europa.json`;
- `observatorio_elegibilidade_fila_europa.csv`;
- workflow operacional e reiniciável da fila;
- fila de revisão curatorial;
- apresentação dos estados do gate na interface.

### Ações

1. criar workflow manual para sondagem com `limit`, `resume` e timeout;
2. sondar candidatos individuais, sem executar fontes de diretório como corpora;
3. materializar evidências técnicas e erros;
4. executar o gate de elegibilidade;
5. criar relatório por estado: aprovado, rejeitado e revisão humana;
6. apresentar contagens e critérios na plataforma;
7. criar lote de revisão curatorial;
8. incorporar somente candidatos aprovados, em commit e decisão separados;
9. nunca alterar `CORPORA` automaticamente.

### Critério de conclusão

Cada candidato possui evidência, estado do gate e decisão humana rastreável antes de qualquer incorporação.

## P4 — política dos 20 corpora e prontidão regional

**Estado:** regra documentada no livro científico; simulação e automação pendentes.

Uma rodada continental deve ser aberta quando houver **20 novos corpora elegíveis, aprovados e validados do mesmo continente** desde a última rodada concluída.

Não contam:

- fontes de descoberta;
- registros em radar;
- duplicados;
- candidatos não avaliáveis;
- negativos metodológicos;
- candidatos sem evidência suficiente;
- revisões curatoriais pendentes.

A regra é uma hipótese operacional de governança, não uma constante científica. Ela deve ser validada antes de se tornar estável e não pode excluir indefinidamente regiões com menor disponibilidade de instituições avaliáveis.

### Ações

1. simular a regra com a fila europeia real;
2. criar contador por continente baseado em candidatos aprovados;
3. definir prazo máximo sem atingir 20;
4. definir regra proporcional para regiões com baixa disponibilidade;
5. definir tratamento de agregadores mundiais e instituições transcontinentais;
6. decidir se cada rodada reobserva todo o corpus continental;
7. versionar denominadores continentais e globais;
8. integrar o gatilho a snapshots, analytics e publicação;
9. publicar relatório de prontidão por região.

### Critério de conclusão

A plataforma informa quantos corpora aprovados faltam para a próxima rodada, qual versão do denominador será alterada e qual regra ou exceção metodológica foi aplicada.

## P5 — sequência continental

**Estado:** sequência provisória documentada no livro científico; validação comparativa pendente.

A descoberta pode ocorrer em paralelo, mas a ativação de novas ondas segue:

0. consolidação do baseline atual, sem novas incorporações;
1. Europa;
2. América do Norte;
3. América Latina e Caribe;
4. África;
5. Ásia;
6. Oceania.

Fontes mundiais, supranacionais ou transcontinentais permanecem em fila transversal e não contam automaticamente para um continente.

### Regras

- agregadores continentais, supranacionais ou nacionais entram antes de instituições individuais;
- arquivos individuais devem preencher lacunas ou oferecer contraste metodológico;
- facilidade técnica não pode ser o único critério de prioridade;
- a ordem só pode mudar após inventário comparável de fontes, justificativa científica, avaliação de consequências de cobertura e registro da decisão;
- nenhum novo continente entra em ativação antes da conclusão de P0–P4;
- toda onda altera o corpus por lote versionado e deve preservar o baseline anterior.

### Próxima onda

Após o fechamento europeu:

1. consolidar a América do Norte, iniciada pelo AAPB;
2. criar inventário e fila da América Latina e Caribe, usando Iberarchivos apenas como fonte de descoberta e curadoria;
3. manter pesquisa preparatória de África, Ásia e Oceania sem incorporação prematura.

## P5A — corpus geral, corpora continentais e recortes geográficos

**Estado:** política incluída no backlog; modelagem, materialização e interface pendentes.

A plataforma deve preservar **um único corpus geral canônico**, reunindo todas as entidades elegíveis e ativas, e produzir a partir dele **corpora continentais, regionais e nacionais derivados e versionados**.

Esses corpora derivados não serão cópias independentes dos dados. Serão visões analíticas construídas por uma matriz de pertencimento geográfico, de modo que cada entidade mantenha identidade única, proveniência única e histórico único no corpus geral.

### Níveis de análise previstos

A infraestrutura deverá permitir estudos em cinco níveis:

1. **país individual** — comparação entre instituições situadas ou atuantes em um mesmo país;
2. **conjunto de países** — grupos definidos e versionados, como recortes linguísticos, políticos, culturais, econômicos ou de pesquisa;
3. **região ou subcontinente** — por exemplo, América Latina e Caribe, Europa do Sul ou países nórdicos, desde que a composição seja declarada;
4. **continente** — corpora continentais derivados do corpus geral;
5. **comparação entre continentes** — resultados harmonizados entre dois ou mais recortes continentais.

### Estrutura canônica

A implementação deverá distinguir:

- `global_corpus_id`: versão do corpus geral;
- `entity_id`: identidade única da instituição ou agregador;
- `institution_country_code`: país de localização institucional principal;
- `coverage_country_codes`: países efetivamente cobertos pelo corpus ou agregador;
- `region_codes`: regiões analíticas aplicáveis;
- `continent_codes`: continentes aplicáveis;
- `geographic_role`: localização institucional, cobertura, agregação ou atuação transcontinental;
- `membership_version`: versão da classificação geográfica;
- `valid_from` e `valid_to`: validade temporal do pertencimento;
- `decision_reference`: fonte e decisão que justificam a classificação.

### Regras de pertencimento e contagem

- cada entidade aparece uma única vez no corpus geral;
- uma entidade pode participar de mais de um recorte derivado quando sua cobertura for multinacional ou transcontinental;
- participação múltipla não pode gerar dupla contagem no indicador global;
- análises nacionais devem declarar se usam localização institucional, cobertura territorial ou ambos;
- agregadores devem separar o país de sede dos países cobertos;
- grupos de países devem possuir identificador, nome, lista de membros, justificativa científica e versão;
- fontes supranacionais e mundiais devem usar regra explícita de atribuição e não ser forçadas artificialmente a um único continente;
- alterações de fronteira, país, sede ou cobertura devem preservar o pertencimento histórico válido em cada snapshot.

### Comparabilidade científica

Comparações entre países, grupos ou continentes só serão publicáveis quando compartilharem:

- mesma versão metodológica do indicador;
- snapshot ou janela temporal comparável;
- regras de elegibilidade e assessabilidade compatíveis;
- distinção entre agregadores e instituições individuais;
- denominadores explícitos;
- cobertura e dados ausentes declarados;
- tratamento documentado de instituições multinacionais e transcontinentais.

Diferenças de tamanho entre os corpora não devem ser ocultadas. A plataforma deverá apresentar valores absolutos, proporções, denominadores, intervalos ou medidas de sensibilidade adequadas ao indicador.

### Produtos a implementar

1. criar registro geográfico canônico e versionado;
2. criar tabela muitos-para-muitos entre entidades e recortes geográficos;
3. criar catálogo versionado de países, grupos de países, regiões e continentes;
4. materializar manifesto do corpus geral e manifestos derivados por recorte;
5. gerar matrizes de pertencimento e cobertura;
6. criar filtros por país, conjunto de países, região e continente;
7. permitir seleção de dois ou mais recortes para comparação;
8. gerar resultados analíticos com denominadores próprios por recorte;
9. impedir dupla contagem no corpus geral e documentar sobreposição entre recortes;
10. criar testes de consistência geográfica e de soma dos denominadores;
11. integrar os recortes aos snapshots, ao histórico de indicadores e aos downloads;
12. documentar a política no livro científico antes da publicação de comparações internacionais.

### Critério de conclusão

A plataforma consegue reconstruir, a partir do mesmo corpus geral versionado, estudos por país, conjunto declarado de países, região, continente e comparação intercontinental, preservando identidade única das entidades, denominadores explícitos, sobreposições documentadas e reprodutibilidade histórica.

## P6 — publicação derivada e entrega pública

**Estado:** código estrutural existente; implantação pendente.

Implementado em código:

- visão pública derivada;
- revisão de publicação;
- registro da publicação ativa;
- histórico de ativações;
- projeção de entrega pública.

Pendências:

1. definir raiz pública canônica;
2. materializar `active_publications.json` e histórico;
3. criar workflow de ativação com portão editorial;
4. gerar `delivery/events.json` e `delivery/manifest.json`;
5. conectar somente produtos aprovados ao observatório;
6. implementar API pública somente leitura em ciclo posterior;
7. criar catálogo estável de downloads e manifestos.

## P7 — consolidação da interface pública

**Estado:** arquitetura principal implantada; auditoria residual.

Concluído:

- quatro áreas principais;
- unidades acessadas dentro das categorias;
- carregamento somente da área selecionada;
- Infraestrutura Científica progressiva;
- português, inglês e espanhol;
- remoção do protótipo vertical rejeitado;
- seletor de idioma em botões compactos na própria página, sem barra lateral.

Pendências:

1. validar manualmente as quatro áreas nos três idiomas;
2. corrigir frases híbridas remanescentes;
3. medir tempo de abertura de cada área e unidade;
4. testar suspensão e reinicialização do Streamlit Cloud;
5. validar celular, tablet e desktop;
6. reduzir tabelas largas e métricas redundantes de forma incremental.

Detalhamento visual:

`docs/project/VISUAL_ARCHITECTURE_BACKLOG.md`

## P8 — vitrine pública independente

**Estado:** decisão arquitetural pendente.

O Streamlit permanece como observatório analítico. A vitrine futura deve ser leve, indexável, multilíngue e separada do ambiente de exploração científica.

A vitrine só deve consumir produtos publicados ou claramente identificados como provisórios.

## P9 — Scientific Internationalization Audit — SIA

**Estado:** ciclo posterior.

Escopo potencial:

- métricas de cobertura multilíngue por página e componente;
- validação terminológica semântica;
- proveniência e revisão das traduções;
- consistência automática entre catálogos;
- indicador de qualidade da tradução;
- migração integral de textos públicos para chaves semânticas.

## Ordem executiva atual

```text
Concluído: sincronizar e validar corpus, registro, fila e resumo europeus
1. Executar o ciclo completo dos 55 corpora ativos globais
2. Materializar validação controlada, analytics vivo, ledger e lotes
3. Modelar o corpus geral e os recortes geográficos versionados
4. Operacionalizar sondagem e elegibilidade da fila europeia
5. Desenvolver e validar separadamente: uso institucional de IA, IA de triagem do observatório e detecção de vídeos gerados ou modificados por IA
6. Simular e validar a política dos 20 corpora
7. Fechar a onda europeia
8. Consolidar a América do Norte
9. Preparar a fila da América Latina e Caribe
10. Manter descoberta preparatória de África, Ásia e Oceania
11. Ativar publicação derivada e entrega pública versionada
```

## Regra do backlog

Novas funcionalidades não devem anteceder a execução dos módulos científicos e de governança que já existem. A prioridade é transformar código estrutural em um ciclo operacional completo, auditável e publicável.
