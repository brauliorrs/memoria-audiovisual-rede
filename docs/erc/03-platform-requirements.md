# Requisitos Cientificos da Plataforma

Este documento traduz a plataforma Memoria Audiovisual em Rede para requisitos de infraestrutura cientifica ERC.

## Mudanca de Funcao

A plataforma deixa de ser avaliada principalmente por cobertura, interface ou utilidade publica. Ela passa a ser avaliada por sua capacidade de produzir evidencias confiaveis para uma pergunta de pesquisa.

## Unidades de Observacao

A arquitetura de dados deve permitir distinguir:

- instituicao custodial;
- agregador ou plataforma intermediaria;
- colecao ou corpus;
- obra audiovisual;
- registro digital;
- identificador externo;
- URL ou rota de acesso;
- estado de disponibilidade;
- data da observacao.

Essa separacao e crucial para nao confundir existencia fisica do acervo com visibilidade publica online.

## Variaveis Minimas

### Detectabilidade

- presenca em agregadores;
- indexacao em mecanismos de busca internos;
- existencia de identificadores persistentes;
- idioma dos metadados;
- completude de titulo, data, autoria, descricao e assunto;
- disponibilidade de vocabularios controlados.

### Interoperabilidade

- padrao de metadados;
- existencia de API, OAI-PMH, RDF, CSV, JSON ou outro meio estruturado;
- estabilidade dos identificadores;
- licenca de metadados;
- compatibilidade com agregadores publicos.

### Acesso

- acesso publico ao registro;
- acesso publico ao conteudo audiovisual;
- acesso restrito;
- conteudo apenas onsite;
- conteudo indisponivel;
- rota quebrada;
- condicao desconhecida.

### Governanca

- tipo de instituicao;
- pais;
- idioma principal;
- modelo de financiamento;
- politica de licenciamento;
- politica declarada de digitalizacao;
- dependencia de plataformas privadas.

### Temporalidade

- primeira observacao;
- ultima observacao;
- mudanca de estado;
- desaparecimento;
- reaparecimento;
- migracao de plataforma;
- alteracao de metadados.

## Indicadores Provisorios

### Digital Audiovisual Visibility Index

Indice composto a desenvolver. Deve evitar dar uma nota simplista de qualidade institucional. O objetivo e medir condicoes de visibilidade, nao ranquear acervos culturalmente.

Componentes iniciais:

- metadata completeness score;
- interoperability score;
- public access score;
- route stability score;
- multilingual discoverability score;
- aggregation presence score;
- licensing clarity score.

### Digital Extinction Signals

Sinais observaveis:

- URL persistente deixou de resolver;
- registro removido de agregador;
- metadados essenciais desapareceram;
- conteudo passou de publico a indisponivel;
- colecao perdeu interface publica;
- instituicao migrou para plataforma sem preservacao de identificadores;
- registro existe apenas em evidencia historica ou snapshot permitido.

## Reprodutibilidade

Cada coleta deve registrar:

- fonte;
- data e hora;
- metodo de coleta;
- versao do script;
- parametros usados;
- numero de registros encontrados;
- numero de registros incorporados;
- numero de erros;
- limites conhecidos da coleta;
- hash ou identificador do dataset gerado, quando aplicavel.

## Etica e Direito

A plataforma deve priorizar:

- metadados;
- identificadores;
- URLs;
- indicadores de acesso;
- datas de observacao;
- caracteristicas tecnicas;
- evidencias documentais legalmente permitidas.

Evitar armazenar copias integrais de obras audiovisuais protegidas sem autorizacao. Miniaturas, snapshots e paginas arquivadas exigem protocolo juridico especifico, especialmente em contexto europeu.

## Requisitos de Interface Publica

A interface publica deve comunicar incerteza metodologica:

- distinguir amostra de universo;
- exibir limites de completude;
- marcar rotas instaveis;
- diferenciar registro, obra e conteudo disponivel;
- permitir consulta por pais, instituicao, agregador, regime de acesso e periodo;
- evitar afirmar que a plataforma representa a totalidade de um acervo quando a coleta e parcial.

## Evidencia ERC

Para a candidatura, a plataforma deve gerar pelo menos quatro artefatos:

1. dataset preliminar documentado;
2. relatorio metodologico de coleta e limites;
3. visualizacao longitudinal de mudancas de visibilidade;
4. conjunto de casos demonstrativos de invisibilidade, restricao e extincao digital.

