# MAR — metodologia científica do observatório

**Versão documental:** 1.0 (proposta de consolidação, sujeita à revisão acadêmica).  
**Objeto:** observação da presença e da circulação **públicas** de acervos audiovisuais em ambientes digitais.  
**Situação:** documento de referência para o desenho do MAR. A aprovação deste texto **não** aprova modelos experimentais, não equivale ao selo de protocolos particulares e não atesta a conclusão do fechamento europeu.

## 1. Problema, questão e finalidade

O Memória Audiovisual em Rede (MAR) é um **observatório científico aberto** destinado a mapear, acompanhar e analisar as condições pelas quais acervos audiovisuais se tornam encontráveis, visíveis, acessíveis, restritos, instáveis ou pouco representados nas redes digitais. A constituição do corpus e o desenvolvimento da plataforma são **meios de observação**, não o objeto científico em si. Seu ponto de partida é a pergunta orientadora registrada no [README](../../README.md):

> Sob quais condições infraestruturais, institucionais, técnicas e culturais os acervos audiovisuais se tornam visíveis, invisíveis, restritos ou instáveis em ambientes digitais?

Hipótese de trabalho: a circulação pública digital do patrimônio audiovisual relaciona-se não apenas à existência material e à localização das coleções, mas também às condições de descrição, indexação, interoperabilidade, idioma, governança institucional, licenciamento, dependência de plataformas, conectividade e regimes técnicos de acesso. Trata-se de **hipótese investigativa**, não de relação causal já demonstrada pelos dados atuais.

Os objetivos metodológicos são: (i) constituir e documentar um corpus observável; (ii) medir manifestações de disponibilidade pública, encontrabilidade, acesso e instabilidade **dentro desse corpus**; (iii) analisar as infraestruturas e relações institucionais associadas; (iv) permitir comparações e observações longitudinais quando os snapshots forem efetivamente comparáveis; e (v) produzir resultados auditáveis e reutilizáveis em estudos acadêmicos.

A identificação de **evidências públicas de adoção e uso de inteligência artificial por instituições** integra o estudo das infraestruturas e práticas de descrição, busca e circulação audiovisual. Ela não redefine o objetivo geral do MAR.

## 2. Delineamento e evolução do instrumento

O MAR combina desenvolvimento de instrumento digital, investigação documental e observação empírica de superfícies públicas. Sua abordagem é **observacional e comparativa**, com possibilidade de séries longitudinais baseadas em snapshots e estudos qualitativos complementares; inferências causais não decorrem automaticamente das associações encontradas.

A plataforma foi inicialmente implementada em versão básica, acompanhada do início da incorporação de acervos ao corpus. O avanço da incorporação foi temporariamente interrompido para desenvolver instrumentos de busca, descoberta, tipagem de superfícies, auditoria técnica e validação. Essa mudança na **ordem de execução** não alterou a pergunta científica central. Concluída a validação exigida de cada instrumento, a constituição e a observação do corpus poderão prosseguir segundo seus protocolos de inclusão.

Os arquivos incorporados antes da criação dos instrumentos de classificação eram **fontes do corpus geral**. A simples presença anterior de uma instituição no MAR **não demonstra**, por si, que seus registros foram usados no desenvolvimento do classificador; essa utilização deve ser verificada em cada estudo de validação. Da mesma forma, corpus institucional anterior não pode ser descrito como inteiramente inédito no projeto.

## 3. Universo, recorte e níveis de análise

O universo de referência compreende instituições, plataformas e agregadores que expõem publicamente, de algum modo, coleções ou informações relativas a patrimônio audiovisual. O recorte em execução prioriza o fechamento metodológico europeu. Agregadores são examinados antes de instituições individuais, conforme critérios explícitos de cobertura, relevância e viabilidade das rotas públicas; amostras comparativas externas podem ser mantidas com identificação separada.

As seguintes entidades **não são intercambiáveis**:

| Nível | Definição operacional | Limite de inferência |
| --- | --- | --- |
| Instituição custodial | Organização responsável ou participante do acervo | Uma rota não representa automaticamente a organização inteira. |
| Agregador/plataforma | Serviço que reúne, indexa ou distribui informações | A ocorrência em agregador não equivale à disponibilidade na fonte custodial. |
| Corpus MAR | Conjunto versionado de dados materializados sob um protocolo de coleta | O total do corpus não é estimativa do acervo físico. |
| Rota/superfície | URL e resposta públicas observadas em condições e data específicas | Ausência de sinal na rota não prova ausência institucional. |
| Registro/item | Unidade audiovisual, metadado, ficha, player ou ligação, segundo o contrato pertinente | Ficha descritiva não equivale necessariamente a vídeo acessível. |
| Evidência/observação | Documento, sinal técnico e snapshot associados à unidade e ao método | Hipóteses e classificações são separadas dos dados brutos. |

A estrutura do corpus preserva explicitamente inclusões, unidades protocoladas ainda não incorporadas e negativas justificadas. Instituições com conteúdo apenas textual, documental ou exclusivamente sonoro não são automaticamente computadas no corpus audiovisual ativo. Unidades restritas ou comerciais sem catálogo público quantificável podem ser documentadas, mas não passam a integrar indicadores cuja base exige registros observáveis.

## 4. Constituição do corpus e coleta

Para cada corpus, documentar: identificação e natureza da instituição, país, rotas iniciais e finais quando observáveis, critérios de inclusão e exclusão, data e configuração de coleta, limite técnico e profundidade, erros e barreiras, unidades efetivamente materializadas, grau de completude e nota metodológica. Respeitar `robots.txt`, autenticação, direitos e restrições de acesso; não contornar barreiras.

**Completude é atributo da coleta, não da instituição.** O número de vídeos ou registros localizados descreve o resultado de uma observação pública delimitada; não deve ser apresentado como dimensão do acervo físico sem fonte independente adequada. Preservar resultados negativos, bloqueios, falhas, redirecionamentos e alterações das rotas quando pertinentes.

Em comparações futuras, declarar a estratégia de seleção e seu alcance — por exemplo, seleção deliberada de agregadores, cobertura de países ou estudo de casos extremos. O corpus atual não constitui amostra probabilística representativa de todas as instituições audiovisuais europeias; generalizações dependem de desenho amostral posterior adequado.

## 5. Instrumentos da plataforma e seus objetos específicos

As funcionalidades técnicas auxiliam o observatório, mas cada uma responde a uma questão própria. A matriz de referência [`instrument-status.json`](instrument-status.json) diferencia a existência de código, o funcionamento verificado por testes e a **validação empírica independente**.

### 5.1 Busca, descoberta e encontrabilidade

O mecanismo de consulta e descoberta identifica rotas, registros e formas públicas de pesquisa nos corpora e serviços observados. Sua avaliação não se confunde com uma afirmação de que todas as peças audiovisuais de uma instituição foram recuperadas. Para testar a qualidade de uma busca, será necessário conjunto de consultas pré-definidas, critérios de relevância por avaliadores e métricas pertinentes à tarefa (por exemplo, precisão em posições de resultado e, somente quando houver universo de referência conhecido, revocação).

A qualidade da **descoberta da superfície** deve ser avaliada separadamente da qualidade da **tipagem** dessa superfície e da **relevância de resultados para uma consulta**.

### 5.2 Auditoria de infraestrutura digital

O detector técnico examina sinais verificáveis em HTML, metadados, cabeçalhos, endpoints e documentação. Suas famílias incluem CMS/repositórios, APIs, protocolos de interoperabilidade, formatos de metadados, formas públicas de busca, restrições e **evidências públicas de IA/automação**. Na camada inicial, o resultado é **heurístico**, não conclusão institucional definitiva.

A unidade mínima de verificação é **corpus + rota + detector + valor + evidência**. A [validação de infraestrutura](../infrastructure-audit/VALIDATION_PROTOCOL.md) exige conferir o contexto da evidência, a rota observada e a diferença entre endpoint funcional, simples referência e anúncio. Estados de revisão: `pending_review`, `confirmed`, `probable`, `inconclusive`, `false_positive`, `not_assessable`. Resultados não avaliáveis ou inconclusivos não são zeros.

### 5.3 Evidências de inteligência artificial

O MAR investiga usos de IA **associados à instituição, ao sistema ou ao processo de gestão e circulação do acervo**, como transcrição, reconhecimento de fala, enriquecimento de metadados, reconhecimento visual, recomendação e classificação. Devem ser identificados, quando possível: tarefa concreta, responsável/instituição, evidência vinculada, data e estágio (`announced`, `research`, `pilot`, `operational`, `discontinued` ou `unknown`).

Há três afirmações distintas, com requisitos crescentes:
1. **Sinal encontrado:** menção ou assinatura pública detectada na superfície e rodada.
2. **Aplicação institucional documentada:** função e vinculação institucional sustentadas por evidência validada e revisão humana.
3. **Uso operacional confirmado:** evidência específica, temporalmente adequada, de implantação, não apenas anúncio ou demonstração.

Menção genérica a “inovação”, associação de domínio, biblioteca de terceiros ou ausência de sinal não autoriza afirmar presença operacional, fornecedor responsável ou inexistência de IA. A detecção forense de **vídeos gerados ou alterados por IA** é tarefa distinta e **não faz parte do escopo validado deste instrumento**. O [protocolo de IA](../statetech-alignment/ai_systems_protocol.md) orienta a revisão específica.

### 5.4 Tipagem de superfícies e elegibilidade de itens

O classificador experimental M3 busca distinguir papéis de superfícies digitais para apoiar a coleta e a interpretação dos registros; sua avaliação deve informar classes, suporte, erros e desempenho por instituição. O mecanismo binário M4 examina elegibilidade de superfície de item e não pode ser inferido da simples existência de fichas ou links. **Testes unitários do software não substituem validação dos modelos.**

A VAL-007 registrou falhas nos critérios operacionais históricos do M3 2.2.0 e do M4. O candidato 2.3.0 e os módulos de prontidão VAL-009 permanecem **experimentais**: infraestrutura de integridade e testes sintéticos concluídos não constituem avaliação independente nem autorização para promover M4.

### 5.5 Observação longitudinal e indicadores

Comparações entre observações somente são realizadas quando a identidade, o universo, as condições de coleta, as definições e as versões forem compatíveis ou acompanhadas de ponte metodológica documentada. Indisponibilidade transitória, limitação técnica, mudança de rota e desaparecimento sustentado devem ser categorias distintas. **Extinção digital** é uma hipótese analítica que exige critério longitudinal e verificação complementar; uma única falha HTTP não a demonstra.

Indicadores descritivos, relacionais, longitudinais e de risco têm regras específicas de elegibilidade e revisão. Índices compostos ou medidas amplas de visibilidade são **objetivos futuros**, não resultados automaticamente disponíveis pela existência de um painel. A [política de governança](../statetech-alignment/indicator_governance_policy.md) exige definição versionada, denominadores explícitos, período, confiabilidade, responsável, snapshot e condições de comparabilidade.

## 6. Evidências, decisões e governança

Preservar separadamente: **dados brutos** da observação, registros **curados** com decisão e justificativa, e dados **publicáveis** com elegibilidade e denominação adequadas. Cada observação deve ser rastreável à origem, instante e versão do instrumento. Um detector automático propõe sinais; a confirmação de afirmações institucionais requer evidências apropriadas e revisão humana.

Adotar a [hierarquia e os estados de evidência](../statetech-alignment/evidence_and_validation_protocol.md). Uma relação entre instituição, fornecedor e tecnologia não se deduz apenas de associação de domínio, e uma interpretação de risco não é saída direta do detector. Publicações distinguem confirmado, provável e não avaliável e preservam a data, o universo e a base da afirmação.

A [governança curatorial](../statetech-alignment/curatorial_governance.md) especifica separação entre coleta, auditoria técnica, revisão curatorial, fechamento de snapshot e aprovação de indicadores. Os papéis são **exigências de processo**; sua descrição documental não prova que já estejam designados e operacionais em todas as avaliações.

## 7. Validação dos instrumentos: planos que não devem ser confundidos

| Plano | Questão | Evidência exigida | Interpretação |
| --- | --- | --- | --- |
| Qualidade de software | Código e contratos funcionam como especificado? | CI, testes de regressão, schema, hashes, integridade | Verifica engenharia, **não** desempenho científico. |
| Qualidade da coleta | As rotas e registros observados foram documentados de modo íntegro e delimitado? | Snapshots, URLs, erros, completude e revisão de casos | Verifica a validade do conjunto coletado no seu escopo. |
| Validade de detector/auditoria | Os sinais técnicos correspondem às evidências e declarações sustentadas? | Amostra revisada, fonte verificável, falsos positivos e casos não avaliáveis | Autoriza somente afirmações compatíveis com o nível de evidência. |
| Validade de classificador | As saídas M3/M4 concordam com referência independente no universo delimitado? | Protocolo prévio, dados disjuntos pertinentes, revisão cega, matrizes e incerteza | Estima desempenho **na população testada**, não validade de toda a plataforma. |
| Validade dos indicadores | As variáveis permitem comparações e inferências declaradas? | Denominador, universo, regra versionada, revisão e cobertura | Controla a publicação e interpretação do observatório. |

Para estudos de classificação, definir antecipadamente população, unidades, tipos de exclusão, versão, parâmetros, métricas e regras de encerramento. Evitar sobreposição de páginas e **contaminação indireta** decorrente de informações dos corpora utilizadas para calibrar regras. Uma instituição anteriormente coletada pelo MAR não é automaticamente uma instituição previamente utilizada pelo M3: as duas exposições devem ser auditadas e nomeadas separadamente.

### Aplicação à VAL-009

A minuta histórica pergunta pela generalização em instituições **ausentes dos conjuntos humanos anteriores de M3**, e **não** declara que tais instituições jamais foram vistas pelo MAR. Documentos posteriores demonstraram que as seis instituições propostas já tinham registros no corpus geral. A pergunta restrita pode permanecer como proposta, **somente após verificação documentada de possíveis influências indiretas** e decisão formal de revisão; seus resultados não provarão generalização para instituições inéditas em todo o projeto. Caso a pesquisa exija esta segunda afirmação, deverá existir **outro desenho prospectivo**, com população e amostra próprias.

A minuta VAL-009 continua **não selada e não executada**. O inventário documenta no mínimo 137 URLs de exposição histórica; 22 strings de testes estão em triagem distinta e não equivalem a 22 visitas comprovadas. Não alterar retrospectivamente a VAL-007, nem usar a incorporação de uma minuta metodológica como autorização para coleta científica, divulgação de previsões ou M4.

## 8. Análise e apresentação dos resultados

Relatórios do MAR devem sempre declarar o objetivo da análise, o recorte geográfico e institucional, a unidade observada, período e protocolo, denominador observado, exclusões, nível de revisão, limitações de coleta e identificadores de snapshot. Uma associação descritiva não é mecanismo causal demonstrado; resultados de instituições e rotas não são observações independentes por definição. Comparações e eventuais intervalos de incerteza devem respeitar agrupamentos institucionais e a composição efetiva da amostra.

Na escrita acadêmica, apresentar **o procedimento final utilizado e eventuais desvios que alterem a validade ou a interpretação dos resultados**. Não é necessário reproduzir cada tentativa técnica, correção de implementação ou PR. Histórico de código, experimentos malsucedidos relevantes, evidências de exposição e mudanças em protocolo são preservados no repositório e citados quando afetarem o argumento científico. Uma metodologia proposta não deve ser narrada como procedimento já executado.

## 9. Estatuto do presente documento

Este texto consolida o **referencial metodológico comum** do observatório e a distinção entre seus instrumentos. O desempenho de cada detector e modelo depende de seu próprio protocolo e dos resultados efetivamente obtidos. As [normas de infraestrutura](../infrastructure-audit/VALIDATION_PROTOCOL.md), [governança de evidências](../statetech-alignment/evidence_and_validation_protocol.md), [protocolo de IA](../statetech-alignment/ai_systems_protocol.md), [governança de indicadores](../statetech-alignment/indicator_governance_policy.md) e [documentação da VAL-009](../engineering/val009-methodology-screening.md) compõem os anexos técnicos, sem fazer da sequência de engenharia o objeto do trabalho acadêmico.

**Antes de declarar a metodologia definitiva para publicação**, confirmar com a coordenação científica: definição final da população e do universo europeu; estado efetivo de validação de cada instrumento; política de estudos longitudinais; limites dos indicadores públicos; responsáveis pelos papéis curatoriais e decisões de cada protocolo particular.
