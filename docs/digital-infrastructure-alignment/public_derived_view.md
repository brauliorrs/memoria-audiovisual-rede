# Visão pública derivada da infraestrutura digital

## Finalidade

A visão pública derivada é uma projeção técnica, versionada e rastreável dos eventos que superaram os controles mínimos de triagem e revisão. Ela não equivale, por si só, a publicação editorial em site, API, painel, relatório ou rede social.

## Entradas

```text
comparação longitudinal
+ relatório de triagem
+ ledger append-only
+ revisões humanas
+ regras de elegibilidade
→ projeção pública derivada
```

## Elegibilidade

Eventos rotineiros podem integrar a projeção quando não possuem bloqueios de qualidade, cobertura, direitos ou contestação.

Eventos não rotineiros exigem a decisão e o quórum previstos para sua classe. O cumprimento do quórum produz elegibilidade técnica, não aprovação automática da redação pública.

Ficam fora da projeção:

- eventos rejeitados;
- decisões adiadas ou sem evidência suficiente;
- quórum incompleto;
- falhas de coleta;
- estados não avaliáveis;
- mudanças exclusivamente metodológicas;
- eventos com supressão cautelar ativa.

## Redação cautelosa

A projeção pode produzir descrições padronizadas, mas qualquer texto público deve preservar a proporcionalidade entre evidência e enunciado.

Um possível desaparecimento deve ser descrito como sinal anteriormente observado e não identificado na rodada posterior, salvo quando evidências independentes sustentarem descontinuação confirmada.

A projeção não transforma erro, bloqueio, `not_assessable`, `still_missing` ou alteração de cobertura em mudança institucional.

## Rastreabilidade

Cada item preserva, no mínimo:

```text
event_id
comparison_id
snapshot_id
entity_id
variable_or_relation
change_type
effective_class
previous_values
current_values
publication_basis
review_ids
evidence_ids
coverage_reference
methodology_version
contest_status
```

## Bases de elegibilidade

Exemplos:

- `routine_projection`: evento rotineiro sem bloqueios;
- `human_review_quorum`: evento liberado pelo quórum aplicável;
- `editorial_revision`: projeção regenerada após decisão editorial;
- `corrective_revision`: projeção corrigida sem transformar correção em mudança empírica.

## Versionamento

Os produtos são preservados por snapshot e revisão. Uma versão existente não pode ser sobrescrita silenciosamente. O manifesto informa:

- versão da projeção;
- snapshot e comparação de origem;
- total por classe;
- eventos excluídos e motivos;
- revisões utilizadas;
- regras e metodologia;
- produto anterior substituído, quando houver.

## Execução operacional

A implementação pode ser acionada pelos scripts de construção e regeneração da visão pública. Os exemplos de caminho e comando são operacionais e não constituem o contrato científico; o contrato é definido pelos schemas, métodos e manifestos ativos.

A preservação durável pode usar a branch histórica dedicada, sem que o nome da branch componha o significado do dado.

## Limite deliberado

A presença de um item na projeção pública significa somente elegibilidade técnica para consumo por outra camada. A publicação externa exige decisão editorial, canal definido, metadados completos e ausência de bloqueio ativo.

## Estado atual

A construção, o versionamento e a regeneração da projeção estão implementados estruturalmente. A integração definitiva com a vitrine, o observatório e uma futura API ainda depende da validação operacional e da arquitetura pública escolhida.