# Fase 2 — adaptação da auditoria e ingestão

## Objetivo

Conectar a auditoria heurística de infraestrutura digital ao núcleo de dados e proveniência da Fase 1, sem publicar resultados automaticamente.

## Fluxo implementado

```text
InfrastructureAudit
→ DigitalInfrastructureAuditAdapter
→ observações normalizadas por sinal
→ IngestionCoordinator
→ preview ou commit controlado
→ artefato bruto e manifesto
→ ledger
→ fila de revisão CSV/JSON
→ decisões humanas append-only
→ dupla revisão quando sensível
→ materialização relacional controlada
```

## Interface operacional de revisão

O script `scripts/review_statetech_observations.py` oferece duas operações:

```text
export → lê observações JSON e gera fila CSV ou JSON
import → valida decisões CSV ou JSON e registra no ledger
```

Exemplos:

```powershell
python scripts/review_statetech_observations.py export --observations data/output/observations.json --output data/review/queue.csv
python scripts/review_statetech_observations.py import --input data/review/decisions.csv
```

A importação exige `observation_id`, `reviewer_id`, `reviewer_role`, `decision` e `justification`. Evidências podem ser fornecidas como lista JSON ou texto separado por `|` ou `;`. Qualquer erro interrompe a importação na decisão inválida; decisões já registradas permanecem no histórico append-only.

## Dupla revisão para sinais sensíveis

São tratados como sensíveis:

- grupos `ai_evidence` e `restriction`;
- observações com termos associados a reconhecimento facial, biometria ou dados pessoais.

Uma observação comum exige uma confirmação válida. Uma observação sensível exige duas confirmações de revisores distintos. Revisores recusados por conflito de interesse ou sob avaliação não contam para o quórum.

A fila exportada informa:

```text
sensitive
required_confirmations
```

A primeira confirmação de um sinal sensível não libera materialização. A observação permanece na fila até a segunda confirmação válida.

## Revisão append-only

Cada decisão preserva:

```text
review_id
observation_id
reviewer_id
reviewer_role
decision
justification
evidence_ids
conflict_of_interest_status
reviewed_at
supersedes_review_id
```

Revisões posteriores devem apontar explicitamente para a revisão mais recente. Justificativa é obrigatória, e decisões `confirmed`, `probable` e `false_positive` exigem evidência.

## Materialização

Somente observações com detecção positiva, decisão `confirmed`, quórum curatorial suficiente, instituição resolvida e evidência existente podem ser encaminhadas ao `CuratorialMaterializer`.

Tecnologias, APIs, formatos de metadados, protocolos e mecanismos de busca confirmados geram `technology` e `institution_technology_relation`. Evidências confirmadas de IA geram `ai_system` conservador, mantendo campos não sustentados como `unknown`. Restrições continuam sem materialização até existir contrato de domínio próprio.

## Arquivos principais

```text
scripts/audit_digital_infrastructure.py
scripts/review_statetech_observations.py
src/memoria_audiovisual/statetech/curatorial_review.py
src/memoria_audiovisual/statetech/review_files.py
src/memoria_audiovisual/statetech/materialization.py
tests/test_statetech_curatorial_review.py
tests/test_statetech_review_files.py
```

## Garantias metodológicas

1. Nenhuma detecção é confirmada automaticamente.
2. Revisões são append-only e possuem cadeia explícita de substituição.
3. A interface de arquivos valida os campos obrigatórios antes do registro.
4. Observações sensíveis exigem dois revisores distintos.
5. Conflitos de interesse podem impedir que uma confirmação conte para o quórum.
6. Somente o estado curatorial vigente e suficiente libera materialização.
7. Fornecedores não são inferidos pela mera detecção de tecnologia.
8. Grupos sem contrato adequado não são forçados para entidades incompatíveis.

## Limites atuais

- nenhuma coleta, migração histórica ou teste foi executado durante o desenvolvimento;
- ainda não existe interface gráfica;
- a importação por arquivo não oferece rollback global do lote;
- não há assinatura digital das decisões;
- instituição e evidência continuam dependendo de identificadores resolvidos;
- artefatos e manifestos permanecem locais.

## Próximo incremento

Criar um pacote de preparação e validação de migração histórica dos CSV/JSON legados, com relatório de compatibilidade, detecção de duplicidades e modo exclusivamente dry-run antes de qualquer ingestão.
