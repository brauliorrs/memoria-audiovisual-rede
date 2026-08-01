# Política de comparação longitudinal

## Objetivo

Definir como a plataforma calcula, classifica e publica diferenças entre dois snapshots sem confundir mudança empírica, correção curatorial, alteração de cobertura ou migração metodológica.

## Unidade de comparação

A comparação opera por:

- entidade estável (`entity_id`);
- variável ou relação definida;
- versão do schema;
- período de validade;
- evidência associada;
- estado de revisão.

## Tipos de resultado

- `added`: entidade, relação ou valor surge no período posterior;
- `removed`: deixa de estar presente após validação suficiente;
- `changed`: valor comparável foi alterado;
- `unchanged`: valor permanece equivalente;
- `became_assessable`: antes não avaliável, agora observável;
- `became_unassessable`: perda de capacidade de observação;
- `reclassified`: mudança curatorial ou taxonômica, sem evidência de mudança empírica;
- `schema_migrated`: diferença produzida por migração de modelo;
- `coverage_changed`: diferença decorrente de alteração do universo observado;
- `inconclusive`: evidência insuficiente para declarar mudança.

## Regra de precedência

Antes de classificar uma diferença como empírica, o comparador deve verificar, nesta ordem:

1. identidade da entidade;
2. compatibilidade de schema;
3. equivalência semântica da variável;
4. mudança de cobertura;
5. correção curatorial registrada;
6. qualidade e validade temporal da evidência;
7. diferença de valor.

## Mudanças por dimensão

### Tecnologias e fornecedores

Mudanças possíveis:

- tecnologia adicionada ou retirada;
- troca de fornecedor;
- alteração de função do fornecedor;
- mudança de camada do stack;
- passagem de solução própria para terceirizada ou vice-versa.

Detecção técnica isolada não basta para declarar troca de fornecedor.

### Contratos

Eventos possíveis:

- contrato anunciado;
- adjudicado;
- iniciado;
- prorrogado;
- alterado;
- encerrado;
- cancelado;
- substituído.

Mudança de valor contratual deve preservar moeda, data de referência e natureza da alteração.

### APIs e interoperabilidade

Estados possíveis:

- disponível;
- degradada;
- restrita;
- descontinuada;
- substituída;
- não avaliável.

Falha pontual de acesso não implica descontinuação.

### IA e automação

Transições possíveis:

- announced → pilot;
- pilot → operational;
- operational → suspended;
- operational → discontinued;
- unknown → confirmed.

Menções promocionais não sustentam adoção operacional.

### Riscos

Mudança de risco só pode ser calculada quando:

- a regra de avaliação é a mesma ou compatível;
- os fatores de risco estão documentados;
- a evidência foi revisada;
- a alteração não resulta apenas de nova taxonomia.

## Cálculo de deltas

Para valores quantitativos:

- diferença absoluta;
- diferença relativa, quando o denominador for válido;
- alteração de faixa ou classe;
- intervalo entre observações;
- nível de confiança.

Para valores categóricos:

- valor anterior;
- valor posterior;
- tipo de transição;
- origem da mudança;
- evidências anterior e posterior.

## Comparações proibidas

Não publicar comparação direta quando:

- os identificadores não foram resolvidos;
- a variável mudou de definição sem tabela de correspondência;
- um dos snapshots não documenta cobertura;
- a diferença pode resultar de falha de coleta;
- a evidência anterior foi retirada sem preservação;
- estados pendentes são tratados como confirmados.

## Produto futuro

```text
data/output/longitudinal_comparisons/{comparison_id}.json
data/output/longitudinal_changes/{comparison_id}.csv
```

Cada comparação deve indicar snapshots de origem, schemas, regras utilizadas, cobertura, exclusões e limitações.
