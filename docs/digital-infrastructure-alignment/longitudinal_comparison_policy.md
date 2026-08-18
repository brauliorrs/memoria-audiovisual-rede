# Política de comparação longitudinal

## Objetivo

Definir como a infraestrutura calcula, classifica, revisa e publica diferenças entre snapshots sem confundir mudança empírica, correção curatorial, alteração de cobertura, falha de coleta ou migração metodológica.

## Unidade de comparação

A comparação opera por entidade estável, variável ou relação definida, snapshots de origem e destino, versões de schema e metodologia, cobertura, evidências e estado de revisão.

## Tipos de resultado

- `added`: entidade, relação ou valor surge no período posterior;
- `removed_candidate`: valor anteriormente observado deixa de ser detectado e requer confirmação;
- `removed_confirmed`: desaparecimento sustentado por evidência e revisão aplicável;
- `changed`: valor comparável foi alterado;
- `unchanged`: valor permanece equivalente;
- `became_assessable`: antes não avaliável, agora observável;
- `became_unassessable`: perda de capacidade de observação;
- `reclassified`: mudança curatorial ou taxonômica;
- `schema_migrated`: diferença produzida por migração de modelo;
- `coverage_changed`: diferença decorrente de alteração do universo observado;
- `collection_failure`: comparação bloqueada por falha técnica;
- `inconclusive`: evidência insuficiente para declarar mudança.

O estado `removed` não deve ser produzido diretamente por mera ausência em uma coleta posterior.

## Regra de precedência

Antes de classificar uma diferença como empírica, o comparador deve verificar:

1. identidade da entidade;
2. compatibilidade de schema e método;
3. equivalência semântica da variável;
4. mudança de cobertura;
5. estado de coleta e avaliabilidade;
6. correção curatorial registrada;
7. qualidade e validade temporal da evidência;
8. diferença de valor.

Qualquer bloqueio nos itens anteriores impede uma conclusão empírica automática.

## Perda de acesso público e retração digital

Para superfícies e itens públicos, a comparação deve preservar explicitamente o estado de acesso anterior e posterior.

Uma `digital_retraction` exige simultaneamente:

1. evidência de que a superfície/item era publicamente acessível no snapshot anterior;
2. evidência de que deixou de estar publicamente acessível no snapshot posterior;
3. ausência de uma superfície pública equivalente substituta identificada;
4. exclusão de falha pontual de coleta, bloqueio apenas ao robô ou indisponibilidade transitória como explicação suficiente.

Se o item nunca teve acesso público comprovado, a comparação deve produzir limitação de acesso, não retração.

Se o item migrou para outra URL pública equivalente, deve produzir `relocated_or_migrated`, não retração.

O mecanismo técnico observado e a causa institucional devem permanecer separados. HTTP 404/410, redirecionamento para homepage, login obrigatório, georrestrição, barreira de direitos ou erro de servidor descrevem estados observáveis; somente uma declaração verificável permite atribuir motivo institucional. A política detalhada está em `access_loss_diagnostics.md`.

## Tecnologias, fornecedores e contratos

Detecção técnica isolada não basta para declarar troca de fornecedor, encerramento contratual ou retirada definitiva de tecnologia. Mudanças contratuais exigem fonte documental compatível. Valores devem preservar moeda, data de referência e natureza da alteração.

## APIs e interoperabilidade

Estados possíveis incluem disponível, degradada, restrita, possivelmente descontinuada, descontinuação confirmada, substituída e não avaliável. Falha pontual, bloqueio automatizado ou indisponibilidade temporária não implica descontinuação.

## IA e automação

Transições entre anúncio, pesquisa, piloto, operação, suspensão e descontinuação exigem evidência compatível. Menções promocionais não sustentam adoção operacional. Não detecção posterior não prova abandono da aplicação.

## Cálculo de deltas

Para valores quantitativos, registrar diferença absoluta, diferença relativa quando válida, alteração de faixa, intervalo entre observações, cobertura e confiança.

Para valores categóricos, registrar valor anterior, valor posterior, tipo de transição, origem da mudança, evidências e decisão curatorial aplicável.

## Comparações proibidas

Não publicar comparação direta quando:

- os identificadores não foram resolvidos;
- a variável mudou de definição sem correspondência documentada;
- um dos snapshots não documenta cobertura;
- a diferença pode resultar de falha de coleta;
- estados pendentes são tratados como confirmados;
- o denominador mudou sem explicitação;
- a única diferença é tradução, normalização ou correção editorial.

## Produtos implementados

A infraestrutura possui componentes executáveis para comparação, triagem e revisão de eventos. Os produtos devem preservar identificadores, snapshots de origem e destino, versões de schema e método, cobertura, exclusões, resultados por classe, evidências, estados de revisão e limitações.

A existência desses componentes não significa que toda transição já foi validada em corpora reais.

## Relação com triagem e publicação

O comparador produz candidatos a mudança. A triagem define materialidade e necessidade de revisão. A revisão humana determina o suporte do evento. A publicação é uma decisão editorial posterior.

Nenhuma dessas camadas deve ser reduzida a um único campo `confirmed`.
