# Política de retenção e preservação

## Objetivo

Definir o que deve ser preservado, por quanto tempo e em qual nível, para sustentar memória institucional, auditoria e análise longitudinal.

## Classes de retenção

### Permanente

- manifestos de snapshots fechados;
- schemas e regras versionadas;
- eventos temporais publicados;
- registros de proveniência;
- relatórios de integridade;
- mapeamentos de migração;
- indicadores publicados e suas bases de cálculo;
- evidências necessárias à reprodução, quando juridicamente permitido.

### Longo prazo

- artefatos brutos não redistribuíveis;
- respostas de APIs;
- HTML e cabeçalhos observados;
- arquivos intermediários de transformação;
- logs técnicos relevantes.

Retenção mínima recomendada: dez anos, sujeita a direitos, custo e capacidade de armazenamento.

### Operacional

- caches;
- arquivos temporários;
- logs de depuração;
- resultados abortados ou incompletos.

Retenção recomendada: 30 a 180 dias, conforme utilidade e custo.

## Princípio de não apagamento histórico

Registros válidos de snapshots fechados não são excluídos por mudança posterior. Quando um recurso não puder continuar armazenado, preservar ao menos:

- identificador;
- metadados técnicos;
- hash;
- origem;
- período de disponibilidade;
- motivo da retirada;
- vínculo com eventos e snapshots.

## Direitos e restrições

A retenção não autoriza redistribuição. Cada artefato deve indicar:

- condição de acesso;
- licença conhecida;
- possibilidade de redistribuição;
- eventual embargo;
- fundamento para preservação interna;
- data de revisão da condição jurídica.

## Integridade

Artefatos permanentes devem possuir hash, tamanho, formato, data de criação e localização lógica. Mudanças de armazenamento não alteram a identidade do artefato.

## Redundância

Para produtos permanentes, adotar futuramente:

- cópia versionada no repositório quando o tamanho permitir;
- armazenamento externo controlado;
- manifesto independente com hashes;
- verificação periódica de integridade.

## Exclusão

Toda exclusão deve gerar evento com:

- artefato afetado;
- motivo;
- agente responsável;
- data;
- política aplicada;
- substituto ou metadados preservados;
- impacto sobre reprodutibilidade.
