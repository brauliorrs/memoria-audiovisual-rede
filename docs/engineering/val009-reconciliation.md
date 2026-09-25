# VAL-009 — reconciliação técnica com a baseline de software v0.1.0

**Estado:** engenharia experimental, sem selo científico e sem execução independente.
**Baseline imutável:** tag `v0.1.0`, commit `23f3f982db138a68d9f2be154549219e44d69404`.

## Evidência de origem examinada

A `main` da baseline contém a infraestrutura de ingestão e governança de releases,
mas não contém os módulos científicos M3 v2.3.0 que permanecem em branches antigos.
O branch `development/val-009-freeze-executor` divergiu amplamente da `main`; por
isso, não pode ser integrado integralmente. Foram examinados estes artefatos
específicos daquele branch:

- `docs/research/experiments/2026-09_m3_v23_validation_readiness.md`;
- `docs/research/experiments/2026-09_m3_v23_independent_preregistration_draft.md`;
- `data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_3_draft.json`;
- `src/memoria_audiovisual/digital_infrastructure/surface_review_v23.py`;
- `src/memoria_audiovisual/digital_infrastructure/surface_metrics_v23.py`;
- `tests/test_surface_metrics_v23.py`.

A minuta original reserva `MAR-T2A-M3-VAL-009` e usa `2.3.0-dev`, mas ainda registra
`candidate_reference_is_freeze=false` e `execution_authorized_by_this_artifact=false`.
Não reinterpretar essas flags, nem o commit de referência da minuta, como um selo.
A avaliação histórica VAL-007 continua reprovada e não pode ser recalculada como
nova evidência independente. CAL-008 representa desenvolvimento/calibração.

## Entrega nesta etapa

`val009_preflight.py` acrescenta uma barreira técnica independente do coletor,
classificador e calculador: recebe exclusivamente bytes dos artefatos, um conjunto
externo de hashes esperados e o commit observado. A função
`verify_preflight(...)` verifica **tudo antes de devolver linhas**. Somente
`guarded_development_evaluate(...)` pode chamar o calculador injetado, depois
de um preflight bem-sucedido. Todo erro lança `PreflightFailure`; nunca gera
métricas parciais.

O contrato técnico sintético exige:

1. Identidade e versões de protocolo, candidato e commit; protocolo com estado
   `sealed` e referência do candidato efetivamente congelada. A minuta atual
   falha aqui por desenho.
2. Pinagem SHA-256 dos bytes exatos de protocolo, candidato, base importada,
   coletor, configuração, seletor, calculador, dependências, exclusões, manual,
   seleção, evidências, fila cega, previsões, revisões, ambos os freezes,
   divulgação e snapshots brutos usados na seleção.
3. Cobertura exata de IDs entre seleção, evidências, fila cega, previsões e
   revisões; identidade estável de entidade, URL e snapshot. IDs duplicados,
   ausentes, extras, snapshots não atribuídos e amostra insuficiente abortam.
4. Fila humana de campos permitidos, sem previsão ou anotação prévia;
   revisões humanas completas, identificadas, datadas, justificadas e vinculadas
   ao snapshot; compatibilidade entre classe e marcador de item.
5. Integridade dos manifestos de congelamento e divulgação e a ordem temporal
   explícita: selo < captura <= seleção < freeze das previsões < início da
   revisão humana <= revisões < freeze humano < abertura das previsões.
6. Referências explícitas a custodiante, revisor distinto, testemunho externo e
   local de armazenamento restrito das previsões.

Os nomes estáveis de artefatos e os campos do novo contrato são definidos no
módulo e ilustrados **somente com dados sintéticos** em
`tests/test_val009_preflight.py`. Os metadados da minuta antiga não satisfazem
esse novo contrato sem uma migração deliberada e verificada.

### Limites explícitos

- O módulo **não** executa coleta, não gera previsões, não abre dados secretos,
  não faz selagem científica e não incorpora os módulos v23 antigos.
- `TrustedSeal` deve vir de um registro de confiança separado e verificável.
  Um chamador que fabrique esse registro pode fabricar também hashes e datas:
  o módulo não autentica assinaturas nem comprova a ordem temporal só por
  declarações textuais. A governança externa é um requisito de produção.
- Um caminho com prefixo `restricted://` apenas registra a intenção; não
  comprova criptografia, autorização nem cegamento efetivo. Estes controles
  precisam de verificação operacional independente.
- Mesmo que um calculador devolva `PASS` no ensaio sintético, o wrapper devolve
  `development_dry_run_only`, `independent_validation=false` e
  `m4_scaling_allowed=false`.
- A integração com snapshots persistidos exige uma adaptação que preserve
  `requested_url` e `url` final sem reconstrução especulativa, e que permita
  auditoria da lista de exclusões inclusive aliases e exposições posteriores.

## Sequência necessária após esta entrega

1. Fazer a correspondência dirigida, arquivo por arquivo, entre o seletor v23,
   seu candidato/base importada, o calculador v23 e os contratos da `main`,
   portando apenas dependências auditadas e testes independentes.
2. Projetar/persistir snapshots brutos e manifestos imutáveis de seleção,
   respeitando ambos os endereços solicitados/finais e seus hashes, inclusive
   respostas de erro e restrições. Gerar os bytes reais do contrato acima.
3. Auditar inventário suplementar de exposição após as 117 unidades conhecidas,
   aliases e itens associados; concluir manual final de anotação.
4. Definir custodiante, revisor, cofre privado, testemunho durável independente,
   controle de acessos, registro imutável de eventos e prova operacional do
   cegamento. Integrar o preflight com esses registros autênticos.
5. Revisar e selar o pré-registro, versões, código, dependências, exclusões e
   artefatos necessários **antes** de qualquer nova coleta, freeze ou divulgação.
   Só então considerar executar a VAL-009 sob o protocolo aprovado.

Esta etapa não modifica os resultados VAL-007, não eleva o candidato 2.3.0 e não
cria versão de software nova ou tag de release.
