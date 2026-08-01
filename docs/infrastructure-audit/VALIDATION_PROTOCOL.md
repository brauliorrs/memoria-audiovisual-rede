# Protocolo de validação da auditoria de infraestrutura

## Objetivo

Padronizar a passagem de sinais automatizados para evidências científicas utilizáveis em tabelas, indicadores, artigos e visualizações públicas.

## Unidade de revisão

A unidade mínima de revisão é uma combinação de:

```text
corpus + rota + detector + valor detectado + evidência
```

A instituição inteira não deve ser validada a partir de um único sinal isolado.

## Etapas

### 1. Verificação da coleta

Confirmar:

- a rota pertence à unidade observada;
- a URL final não redirecionou para página genérica ou de erro;
- o conteúdo corresponde ao momento registrado;
- o status de coleta foi classificado corretamente;
- a evidência não foi produzida por banner, rodapé, notícia ou conteúdo irrelevante.

### 2. Revisão por grupo

#### Tecnologias

Aceitar como `confirmed` quando houver assinatura técnica inequívoca, metatag de gerador, arquivo típico, cabeçalho ou documentação oficial. Logotipos, textos promocionais e links externos isolados não bastam.

#### APIs e serviços

Distinguir:

- endpoint operacional;
- documentação de API;
- simples menção textual;
- API interna usada pela interface, sem compromisso público de acesso.

Uma chamada interna detectável pode ser `probable`; uma documentação oficial ou endpoint identificável pode ser `confirmed`.

#### Formatos de metadados

Confirmar quando o formato estiver presente em metadados embutidos, resposta estruturada, documentação oficial ou endpoint. Não inferir Dublin Core, EAD ou EDM apenas pelo vocabulário descritivo da página.

#### Interoperabilidade

A presença de um protocolo não prova interoperabilidade institucional plena. Registrar apenas o mecanismo detectado, como manifesto IIIF, endpoint OAI-PMH, OpenSearch ou Linked Data.

#### Busca

Distinguir formulário HTML simples, busca por parâmetros, busca facetada e mecanismo técnico identificado. Não atribuir Solr ou Elasticsearch sem evidência específica.

#### Restrições

Registrar a restrição observada na superfície e no momento da coleta. Não generalizar para todo o acervo. Diferenciar autenticação, cadastro, assinatura, direitos condicionados, geobloqueio e bloqueio automatizado.

#### IA

Exigir evidência textual explícita ou documentação institucional. Expressões genéricas como “pesquisa inteligente”, “automatizado” ou “inovador” são insuficientes. Identificar a tarefa declarada: catalogação, indexação, transcrição, reconhecimento de fala, visão computacional, recomendação ou classificação.

### 3. Decisão

- `confirmed`: evidência inequívoca ou triangulada com fonte oficial;
- `probable`: sinais fortes e convergentes, ainda sem confirmação suficiente;
- `inconclusive`: sinal ambíguo ou insuficiente;
- `false_positive`: regra acionada por contexto inadequado;
- `not_assessable`: superfície indisponível, bloqueada ou tecnicamente incapaz de sustentar conclusão.

### 4. Nota de revisão

Toda decisão diferente de `confirmed` deve ter nota curta. Recomenda-se também registrar nota quando a confirmação depender de fonte externa.

Modelo:

```text
Decisão: probable
Justificativa: endpoint JSON usado pela busca pública foi detectado, mas não há documentação que o apresente como API aberta.
Fonte complementar: nenhuma
```

## Amostragem inicial futura

Quando houver execução, a primeira validação deve priorizar diversidade e não apenas volume:

- um agregador europeu;
- uma instituição audiovisual nacional;
- uma instituição regional;
- uma plataforma com API documentada;
- uma unidade com acesso restrito;
- um caso com sinal de IIIF ou OAI-PMH;
- um caso com possível evidência de IA.

## Controle de falsos positivos

Cada detector deve manter contagem de:

- registros revisados;
- confirmações;
- prováveis;
- falsos positivos;
- inconclusivos.

Detectores com taxa elevada de falso positivo devem ser desativados para indicadores até revisão da regra.

## Critério para publicação

Um indicador pode entrar no painel somente quando:

1. usa campos definidos no contrato de dados;
2. exclui `pending_review` e `false_positive`;
3. apresenta denominador explícito;
4. informa o número de unidades `not_assessable`;
5. não transforma ausência de detecção em ausência de tecnologia;
6. mantém link ou referência para evidência auditável;
7. informa a data do snapshot.

## Auditoria da própria validação

A validação deve ser reprodutível. Alterações de decisão preservam histórico com revisor, data, decisão anterior e nova justificativa. Nenhuma correção apaga a observação bruta.