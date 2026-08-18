# Diagnóstico de perda de acesso público

## Objetivo

A MAR não interpreta toda indisponibilidade como retração digital. O diagnóstico longitudinal deve distinguir **perda real de acesso público**, **mudança de endereço**, **barreira de acesso**, **falha técnica transitória** e **causa não determinável**.

## Regra conceitual

Um evento só pode ser denominado `digital_retraction` quando uma superfície ou item que possuía evidência anterior de acesso público deixa de estar publicamente acessível em observação posterior, sem substituição pública equivalente identificada.

Se o item nunca teve acesso público comprovado, o estado é `public_access_limitation`, não retração.

Se a URL anterior deixa de funcionar, mas o mesmo item é encontrado em uma nova superfície pública equivalente, o evento é `relocated_or_migrated`, não retração.

Falha pontual de coleta, indisponibilidade temporária ou bloqueio apenas ao robô não constitui retração.

## O que pode ser conhecido

A MAR deve registrar duas camadas diferentes:

1. **mecanismo observável de inacessibilidade** — inferido de resposta HTTP, cadeia de redirecionamento, conteúdo da página, presença de login/barreira, mensagem institucional e comparação com snapshots anteriores;
2. **causa institucional declarada** — somente quando existe declaração pública verificável da instituição ou documentação equivalente.

A ausência de declaração institucional impede afirmar intenção ou motivação. Nesse caso a MAR pode informar o mecanismo técnico observado, mas a causa institucional permanece `unknown`.

## Taxonomia de mecanismo observável

- `removed_404_410` — URL anteriormente pública passa a responder como não encontrada/removida;
- `redirected_to_home_or_generic` — URL específica redireciona para homepage, índice ou página genérica sem superfície equivalente do item;
- `relocated_or_migrated` — item reaparece em nova URL pública equivalente;
- `authentication_required` — login, cadastro ou autenticação passam a ser exigidos;
- `formal_request_required` — acesso passa a depender de formulário, e-mail ou solicitação institucional;
- `payment_or_subscription_required` — acesso passa a exigir pagamento ou assinatura;
- `geographic_restriction` — mensagem pública ou evidência técnica verificável indica limitação territorial;
- `rights_or_legal_restriction` — página ou resposta pública declara restrição de direitos, copyright, licenciamento ou fundamento jurídico;
- `temporarily_unavailable` — indisponibilidade explicitamente temporária ou falha de servidor compatível com condição transitória;
- `technical_failure` — timeout, erro de servidor, DNS ou falha técnica sem evidência de mudança de política de acesso;
- `crawler_restriction_only` — bloqueio à coleta automatizada sem evidência de indisponibilidade ao usuário público; não conta como retração;
- `indexed_but_public_surface_unavailable` — registro continua descobrível/indexado, mas não há superfície pública específica acessível;
- `unknown` — mecanismo não pôde ser determinado com evidência suficiente.

## Evidências mínimas

Cada diagnóstico deve preservar, quando disponível:

- URL anterior e URL final após redirecionamentos;
- status HTTP e cadeia de redirecionamento;
- timestamp;
- hash/snapshot anterior em que o acesso público estava comprovado;
- mensagem pública apresentada ao usuário;
- evidência de indexação/descoberta atual;
- URL substituta, quando encontrada;
- barreira observada (login, pagamento, solicitação, georrestrição etc.);
- declaração institucional sobre o motivo, quando existir;
- nível de confiança e estado de revisão humana.

## Confiança causal

- `observed` — descreve apenas o mecanismo diretamente observado, sem afirmar causa institucional;
- `declared` — a instituição declara publicamente o motivo;
- `corroborated` — declaração e evidência técnica/documental convergem;
- `unknown` — não há base suficiente para explicar a inacessibilidade.

A MAR não deve transformar correlação temporal em causalidade institucional.

## Relevância científica

A estatística agregada de retração deve ser acompanhada, sempre que houver volume suficiente, da distribuição dos mecanismos observados. Assim, em vez de publicar apenas “X superfícies deixaram de estar acessíveis”, a plataforma poderá distinguir, por exemplo, migrações, remoções, novas barreiras de login, restrições territoriais e casos sem causa determinável.

Casos `unknown` permanecem explicitamente separados. A ausência de explicação não invalida a observação de perda de acesso, mas limita sua interpretação.

## Relação com IA no acervo

Uma perda de acesso público pode tornar um item `not_assessable` para a validação de IA, mas não produz rótulo negativo de IA. O evento de acesso e a classificação semântica de IA permanecem dimensões independentes.
