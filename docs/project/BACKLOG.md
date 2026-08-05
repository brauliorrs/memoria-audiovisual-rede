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
5. Simular e validar a política dos 20 corpora
6. Fechar a onda europeia
7. Consolidar a América do Norte
8. Preparar a fila da América Latina e Caribe
9. Manter descoberta preparatória de África, Ásia e Oceania
10. Ativar publicação derivada e entrega pública versionada
```

## Regra do backlog

Novas funcionalidades não devem anteceder a execução dos módulos científicos e de governança que já existem. A prioridade é transformar código estrutural em um ciclo operacional completo, auditável e publicável.
