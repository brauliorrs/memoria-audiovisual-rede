# Política de versionamento e releases

## Objetivo

Estabelecer um processo reproduzível para identificar estados do software sem
confundir evolução de código com novas rodadas científicas, snapshots de dados ou
mudanças de schema.

## Identificadores independentes

O projeto mantém três dimensões separadas:

- `software_version`: versão do código, interface, pipeline e regras de processamento;
- `dataset_snapshot`: fotografia temporal dos dados e resultados observacionais;
- `schema_version`: versão dos contratos estruturais de dados.

Uma nova coleta ou snapshot não aumenta automaticamente a versão do software.
Uma mudança de software não altera automaticamente a versão do schema.

## Fonte de verdade da versão do software

A versão do pacote é declarada em `pyproject.toml`, em
`[project].version`.

Durante o ciclo de desenvolvimento, esse valor pode representar o próximo
baseline pretendido, mas só passa a identificar uma release publicada quando:

1. o commit exato foi aprovado;
2. os gates obrigatórios foram executados sobre o conteúdo candidato;
3. o changelog contém a seção correspondente;
4. existe uma tag `vX.Y.Z` apontando para esse commit;
5. existe uma GitHub Release construída sobre essa tag.

## Semantic Versioning

O software segue `MAJOR.MINOR.PATCH`.

Enquanto o projeto estiver em `0.y.z`:

- `PATCH`: correções compatíveis, documentação de engenharia e hardening sem
  mudança deliberada de contrato público;
- `MINOR`: nova capacidade, refatoração relevante ou mudança de contrato que ainda
  seja aceitável durante a fase pré-1.0;
- `1.0.0`: marco em que os contratos públicos essenciais forem considerados
  estáveis e houver política explícita para mudanças incompatíveis.

Após `1.0.0`, mudanças incompatíveis exigem incremento de `MAJOR`, novas
capacidades compatíveis incrementam `MINOR` e correções compatíveis incrementam
`PATCH`.

## Gates obrigatórios

Uma release de software exige, no mínimo:

- commit candidato identificado por SHA;
- `Quality Checks` concluído com sucesso sobre o commit candidato na `main`;
- suíte de testes sem falhas;
- Ruff e formatter check sem falhas no escopo definido pelo projeto;
- mypy sem falhas no escopo tipado;
- cobertura igual ou superior ao piso configurado;
- `check_deployment_ready.py` aprovado;
- changelog atualizado;
- ausência de divergência conhecida entre documentação, versão do pacote e artefato
  de release.

O workflow `Pipeline APE` acessa infraestrutura externa e não é, por si só, um
gate determinístico universal de release. Quando uma release altera o pipeline de
coleta, sua execução controlada deve ser verificada e o resultado registrado.

## Proteção da main

A política desejada é:

- mudanças relevantes entram por pull request;
- `Quality Checks` deve concluir com sucesso antes do merge;
- a configuração administrativa de branch protection deve ser verificada e
  documentada separadamente.

A indisponibilidade de uma API administrativa não deve ser interpretada como prova
de que a proteção está ativa ou inativa.

## Baseline 0.1.0

O valor `0.1.0` já existe no `pyproject.toml`, mas a primeira release não deve ser
criada retroativamente sem selecionar o commit que representa o baseline.

Antes de publicar `v0.1.0`:

1. concluir a auditoria dos workflows;
2. confirmar os gates no commit exato da `main`;
3. confirmar o estado da proteção da `main` ou registrar explicitamente a exceção;
4. promover o conteúdo de `[Unreleased]` para `[0.1.0] - YYYY-MM-DD`;
5. criar a tag somente depois dessas verificações;
6. criar a GitHub Release usando a tag aprovada.

## Relação com validação científica

Tags de software não substituem identificadores de protocolos ou validações.

Resultados científicos congelados devem continuar referenciando, conforme aplicável:

- versão do protocolo;
- hash dos artefatos;
- commit do software;
- snapshot dos dados;
- schema utilizado;
- ordem temporal de freeze e avaliação.

Nenhuma release de software reabre automaticamente um freeze científico anterior.
