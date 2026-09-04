# Política de snapshots e ciclos longitudinais

## Objetivo

Definir como a infraestrutura abre, conduz, fecha, nomeia, preserva e publica ciclos de observação longitudinal sem sobrescrever estados anteriores nem confundir observação, correção metodológica e publicação.

## Princípio

Cada snapshot representa um estado imutável e auditável do organismo em um escopo e momento definidos. Um snapshot fechado nunca é reescrito. Correções posteriores geram nova versão do registro, evento curatorial ou snapshot substituto explicitamente relacionado ao anterior.

A existência do mecanismo de snapshots no código não significa que já exista uma série longitudinal oficial validada. A primeira série científica depende da validação operacional descrita no Research Handbook.

## Tipos de snapshot

- `baseline`: linha de base inicial de um conjunto de entidades ou variáveis;
- `scheduled`: ciclo periódico ordinário;
- `event_driven`: ciclo aberto por evento material documentado;
- `methodological`: ciclo destinado a migração de schema, revisão de taxonomia ou recalibração metodológica;
- `corrective`: ciclo que corrige erro sem reclassificar a correção como mudança empírica.

## Periodicidade

A periodicidade não é uma propriedade universal da plataforma. Ela deve ser definida por plano de observação versionado, considerando volatilidade, custo, relevância científica e capacidade operacional.

Como referência inicial, o projeto pode adotar:

- ciclo completo anual para o corpus ativo;
- ciclos mais frequentes para dimensões voláteis, quando houver capacidade e justificativa;
- ciclo extraordinário para evento material documentado;
- ciclo metodológico quando mudança de schema afetar comparabilidade.

Toda periodicidade efetivamente adotada deve constar no manifesto do ciclo. Exemplos de cadência não constituem obrigação permanente.

## Abertura de ciclo

Um ciclo só pode ser aberto quando possuir:

- `cycle_id` único;
- tipo de snapshot;
- escopo geográfico, institucional e documental;
- unidades e variáveis previstas;
- versão dos schemas;
- versão das regras de validação;
- data e agente de abertura;
- justificativa metodológica;
- ciclo anterior de referência, quando existir;
- plano de cobertura e tratamento das unidades não avaliáveis.

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

1. as unidades previstas estiverem classificadas como observadas, não avaliáveis ou justificadamente ausentes da rodada;
2. os registros incluídos passarem pela integridade estrutural;
3. registros elegíveis para publicação possuírem evidência e revisão compatíveis;
4. pendências críticas estiverem resolvidas ou formalmente excluídas;
5. o manifesto informar cobertura, lacunas, exceções e limitações;
6. os hashes dos artefatos integrantes estiverem registrados;
7. as versões de schemas, métodos e regras estiverem congeladas;
8. falhas de coleta não tiverem sido convertidas em resultados negativos.

Fechamento não significa completude absoluta nem validação empírica universal. Significa que o estado observado, sua cobertura e suas limitações estão formalmente documentados.

## Nomenclatura

Formato recomendado:

```text
snapshot-{scope}-{YYYYMMDD}-{type}-v{major}.{minor}.{patch}
```

O identificador interno deve ser estável e não depender apenas do nome do arquivo.

## Conteúdo mínimo

- manifesto do snapshot;
- registros de entidades e relações incluídos;
- proveniência e evidências associadas;
- eventos temporais;
- relatório de integridade;
- versões dos schemas, métodos e regras;
- estatísticas de cobertura;
- lista de exclusões justificadas;
- hashes dos artefatos;
- estado de revisão e elegibilidade de publicação.

## Imutabilidade e correção

Snapshots fechados são imutáveis. Uma correção posterior deve:

- preservar o snapshot original;
- criar evento `curatorial_correction`;
- gerar nova versão do registro;
- indicar `supersedes_snapshot_id` quando houver snapshot corretivo;
- explicar se a correção altera indicadores ou produtos publicados;
- preservar a distinção entre data da observação e data da correção.

## Comparabilidade

Dois snapshots só podem ser comparados diretamente quando:

- as entidades possuem identidade resolvida;
- as variáveis possuem significado equivalente;
- os schemas são compatíveis ou existe migração documentada;
- os critérios de cobertura são conhecidos;
- mudanças curatoriais foram separadas de mudanças empíricas;
- o intervalo e a diferença de condições de coleta são informados.

## Publicação

O snapshot pode ser fechado sem ser publicado. A publicação exige uma decisão adicional sobre produtos derivados, revisão, cobertura, licenciamento e restrições de acesso.

`closed` descreve o estado técnico e metodológico do ciclo. `published` descreve uma decisão editorial versionada. Nenhum desses estados, isoladamente, autoriza afirmações que ultrapassem a evidência disponível.

## Estado atual

O núcleo de snapshots, persistência e comparação está implementado estruturalmente. Permanecem pendentes a validação operacional controlada, a confirmação dos critérios de fechamento em corpora reais e o primeiro ciclo longitudinal científico oficial.