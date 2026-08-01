# Governança curatorial e papéis humanos

## Objetivo

Definir responsabilidades, separação de funções, trilha de auditoria e critérios de autorização para coleta, revisão, validação, fechamento de snapshots, aprovação de indicadores e publicação de produtos.

## Princípios

1. Nenhum agente deve acumular, isoladamente, coleta, validação final e publicação do mesmo registro crítico.
2. Toda decisão curatorial deve ser atribuível a um agente identificado.
3. Ações humanas e automatizadas devem permanecer distinguíveis.
4. Correções devem criar nova versão, sem apagar o histórico.
5. Conflitos de interesse devem ser declarados antes da revisão.
6. Modelos de IA podem apoiar triagem, mas não aprovar evidências, riscos ou publicações.

## Papéis

### data_collector
Responsável por coleta manual ou supervisão de coleta automatizada. Pode registrar fonte, método, artefato bruto e observação inicial. Não pode confirmar sozinho registros críticos que coletou.

### technical_auditor
Avalia sinais técnicos, tecnologias, APIs, padrões, interoperabilidade, busca e restrições. Pode propor classificação e confiança, mas não autoriza publicação final.

### institutional_researcher
Investiga natureza institucional, fornecedores, contratos, financiamento, governança e relações Estado–tecnologia.

### curator_reviewer
Revisa evidências, coerência semântica, temporal e relacional. Pode confirmar, rejeitar, marcar como provável ou inconclusivo.

### senior_curator
Resolve divergências, aprova exceções metodológicas, valida riscos altos ou críticos e autoriza correções com impacto longitudinal.

### snapshot_manager
Abre ciclos, verifica completude, congela versões, fecha snapshots e registra manifesto. Não pode alterar registros após o fechamento.

### indicator_steward
Mantém definições, denominadores, regras de inclusão, cobertura mínima e comparabilidade dos indicadores.

### publication_approver
Autoriza produtos públicos após verificar validação, cobertura, licença, limitações, proveniência e integridade.

### system_administrator
Mantém infraestrutura e permissões. Não possui autoridade metodológica automática.

### automated_agent
Executa coleta, transformação, detecção, validação sintática ou comparação. Toda ação deve registrar software, versão, configuração e timestamp.

## Separação mínima de funções

- coleta e validação final: agentes distintos para registros críticos;
- definição e publicação de indicador: revisão independente;
- avaliação de risco alto ou crítico: pelo menos dois revisores, incluindo senior_curator;
- fechamento de snapshot: snapshot_manager e uma aprovação curatorial;
- publicação pública: publication_approver diferente do responsável primário pela coleta.

## Matriz resumida de permissões

| Ação | Collector | Auditor/Researcher | Reviewer | Senior Curator | Snapshot Manager | Indicator Steward | Publication Approver |
|---|---:|---:|---:|---:|---:|---:|---:|
| Criar registro | sim | sim | sim | sim | não | não | não |
| Propor classificação | sim | sim | sim | sim | não | não | não |
| Confirmar registro comum | não isoladamente | não isoladamente | sim | sim | não | não | não |
| Confirmar risco alto/crítico | não | não | não isoladamente | sim | não | não | não |
| Fechar snapshot | não | não | não | aprova | executa | não | não |
| Aprovar definição de indicador | não | não | consulta | sim | não | executa | não |
| Autorizar publicação | não | não | consulta | consulta | não | consulta | sim |

## Trilha de auditoria

Toda ação deverá registrar:

- `audit_action_id`;
- `agent_id`;
- `agent_role`;
- `action_type`;
- `target_entity_type`;
- `target_entity_id`;
- `previous_version_id`, quando aplicável;
- `resulting_version_id`, quando aplicável;
- `decision_status`;
- `decision_reason`;
- `evidence_ids`;
- `conflict_of_interest_status`;
- `performed_at`;
- `software_context`, para agentes automatizados.

## Conflitos de interesse

Conflito deverá ser declarado quando o revisor:

- tiver vínculo empregatício, contratual ou consultivo com a instituição ou fornecedor analisado;
- tiver participado diretamente do sistema, contrato ou projeto avaliado;
- possuir interesse financeiro relevante;
- tiver relação pessoal capaz de comprometer independência;
- for autor primário do registro em controvérsia e não houver segunda revisão.

Estados:

- `none_declared`;
- `declared_managed`;
- `declared_recusal_required`;
- `under_assessment`.

## Divergências

Divergências entre revisores serão registradas, nunca apagadas. Possíveis resultados:

- consenso após revisão;
- decisão do senior_curator;
- manutenção como inconclusivo;
- solicitação de nova evidência;
- suspensão da publicação.

## Exceções

Toda exceção deverá declarar regra afetada, justificativa, aprovador, período de validade e impacto sobre comparabilidade ou publicação.
