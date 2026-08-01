# Política de snapshots e ciclos longitudinais

## Objetivo

Definir como a plataforma abre, conduz, fecha, nomeia, preserva e publica ciclos de observação longitudinal sem sobrescrever estados anteriores.

## Princípio

Cada snapshot representa um estado imutável e auditável do organismo em um momento definido. Um snapshot fechado nunca é reescrito; correções posteriores geram nova versão, evento curatorial ou snapshot substituto explicitamente relacionado ao anterior.

## Tipos de snapshot

- `baseline`: linha de base inicial de um conjunto de entidades ou variáveis;
- `scheduled`: ciclo periódico ordinário;
- `event_driven`: ciclo aberto por mudança relevante, como término de contrato, mudança de fornecedor, adoção de IA ou alteração de acesso;
- `methodological`: ciclo destinado a migração de schema, revisão de taxonomia ou recalibração metodológica;
- `corrective`: ciclo que corrige erro identificado sem reclassificar a correção como mudança empírica.

## Periodicidade

A política padrão prevê:

- snapshot anual completo para todas as entidades ativas;
- snapshot trimestral para variáveis voláteis: APIs, disponibilidade, autenticação, fornecedores, contratos, IA operacional e regimes de acesso;
- snapshot extraordinário quando houver evento material documentado;
- snapshot metodológico sempre que mudança de schema afetar comparabilidade.

A periodicidade poderá ser alterada por entidade ou dimensão, mas a exceção deverá ser registrada no manifesto do ciclo.

## Abertura de ciclo

Um ciclo só pode ser aberto quando possuir:

- `cycle_id` único;
- tipo de snapshot;
- escopo geográfico e institucional;
- entidades e variáveis previstas;
- versão dos schemas;
- versão das regras de validação;
- data e agente de abertura;
- justificativa metodológica;
- ciclo anterior de referência, quando existir.

Estados do ciclo:

- `planned`;
- `open`;
- `collecting`;
- `under_review`;
- `ready_to_close`;
- `closed`;
- `published`;
- `superseded`;
- `cancelled`.

## Fechamento de ciclo

Um ciclo poderá ser fechado apenas quando:

1. as entidades previstas estiverem classificadas como observadas, não avaliáveis ou justificadamente ausentes;
2. os registros incluídos passarem pela integridade estrutural;
3. registros publicados possuírem evidência compatível;
4. pendências críticas estiverem resolvidas ou formalmente excluídas do snapshot;
5. o manifesto informar cobertura, lacunas, exceções e limitações;
6. os hashes dos artefatos integrantes estiverem registrados;
7. a versão dos schemas e regras estiver congelada para o snapshot.

Fechamento não significa completude absoluta. Significa que a cobertura e as limitações do ciclo estão explicitamente documentadas.

## Nomenclatura

Formato recomendado:

```text
snapshot-{scope}-{YYYYMMDD}-{type}-v{major}.{minor}.{patch}
```

Exemplos:

```text
snapshot-europe-20261231-scheduled-v1.0.0
snapshot-ina-20270315-event-driven-v1.0.0
snapshot-europe-20280101-methodological-v2.0.0
```

O identificador interno deve ser estável e não depender apenas do nome do arquivo.

## Conteúdo mínimo do snapshot

- manifesto do snapshot;
- registros de entidades e relações incluídos;
- registro de proveniência;
- eventos temporais associados;
- relatório de integridade;
- versões dos schemas;
- versões das regras;
- estatísticas de cobertura;
- lista de exclusões justificadas;
- hashes dos artefatos.

## Imutabilidade e correção

Snapshots fechados são imutáveis. Uma correção posterior deve:

- preservar o snapshot original;
- criar evento `curatorial_correction`;
- gerar nova versão do registro;
- indicar `supersedes_snapshot_id` quando a correção exigir novo snapshot;
- explicar se a correção altera ou não indicadores publicados.

## Comparabilidade

Dois snapshots só podem ser comparados diretamente quando:

- as entidades possuem identidade resolvida;
- as variáveis possuem significado equivalente;
- os schemas são compatíveis ou existe migração documentada;
- os critérios de cobertura são conhecidos;
- mudanças curatoriais foram separadas de mudanças empíricas.

## Publicação

O snapshot pode ser fechado sem ser publicado. A publicação exige revisão adicional dos produtos derivados e registro de `published_at`, versão pública e eventuais restrições de acesso.
