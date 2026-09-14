# Política de revisão derivada da publicação

## Objetivo

Permitir que decisões humanas concluídas após o fechamento de uma rodada sejam incorporadas à projeção pública sem modificar a coleta, a triagem, o snapshot ou a primeira versão derivada.

## Regra de imutabilidade

Os produtos iniciais permanecem preservados. Cada regeneração cria uma revisão derivada, sequencial e identificável. Nenhuma revisão pode sobrescrever silenciosamente a anterior.

## Fontes da regeneração

A revisão é reconstruída a partir de:

1. eventos longitudinais originais;
2. ledger append-only atualizado;
3. decisões curatoriais válidas;
4. regras de quórum e elegibilidade vigentes;
5. bloqueios editoriais, jurídicos ou de contestação aplicáveis.

Não é permitido editar diretamente um produto anterior para acrescentar, alterar ou retirar eventos.

## Tipos de revisão

- `curatorial`: incorpora nova decisão humana sobre evento;
- `corrective`: corrige erro técnico ou editorial;
- `methodological`: aplica mudança de regra sem apresentá-la como mudança empírica;
- `contest_response`: responde a contestação documentada;
- `rights_restriction`: altera exposição por licença, privacidade ou redistribuição;
- `withdrawal`: retira produto ou item de circulação preservando o histórico.

## Manifesto

Cada revisão registra:

- `snapshot_id` e `product_id`;
- número e identificador da revisão;
- versão anterior substituída;
- tipo e justificativa;
- solicitante e responsável pela decisão;
- eventos adicionados, removidos, alterados ou suprimidos;
- revisões e evidências utilizadas;
- impacto em indicadores e textos públicos;
- estado de contestação;
- data de geração e, quando aplicável, publicação.

A substituição ocorre apenas no sentido editorial. Versões anteriores continuam preservadas e recuperáveis.

## Restrições

- a versão anterior precisa existir;
- justificativa e responsável são obrigatórios;
- eventos de outro snapshot não podem ser incorporados sem vínculo explícito;
- a numeração é sequencial;
- uma revisão existente não pode ser sobrescrita;
- regeneração não executa nova coleta;
- regeneração não altera o ledger, snapshots ou relatórios de cobertura;
- mudança metodológica deve ser identificada como tal;
- retirada cautelar não equivale automaticamente a admissão de erro.

## Relação com publicação externa

Uma nova projeção derivada não precisa ser automaticamente promovida à versão externa vigente. A ativação pública é uma decisão separada, registrada no catálogo ou registro de publicação ativa.

## Estado atual

A regeneração versionada e a preservação das revisões estão implementadas estruturalmente. Permanecem pendentes a validação operacional com correções e contestações reais e a definição dos responsáveis editoriais do primeiro ciclo oficial.