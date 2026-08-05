# Governança e implementação da infraestrutura digital

Esta pasta documenta a arquitetura técnica, os contratos de dados, a proveniência, a revisão humana, a memória longitudinal e as regras de publicação da infraestrutura de pesquisa **Memória Audiovisual em Rede**.

A interpretação científica do projeto é definida pelo [`Research Handbook`](../research/README.md). As especificações computáveis dos indicadores são definidas em `data/templates/analytics/indicator_registry.json`, `data/templates/analytics/methodology_registry.json` e no pacote `src/memoria_audiovisual/analytics/`. Os documentos desta pasta descrevem como essas definições são implementadas e governadas.

## Pergunta de infraestrutura

**Como instituições de memória audiovisual dependem de plataformas, padrões, sistemas, fornecedores, fluxos de dados e serviços tecnológicos externos para preservar, descrever, disponibilizar e fazer circular seus acervos?**

## Limite interpretativo

Esta camada registra **evidências observáveis**, decisões curatoriais e relações documentadas. Ela não transforma detecções automáticas em fatos institucionais verificados.

- ausência de detecção não prova ausência institucional;
- fornecedor, contrato ou fluxo de dados não é inferido apenas pela identificação de software;
- resultados marcados como implementados ainda podem depender de validação empírica;
- alegações sensíveis exigem evidência identificável e revisão compatível;
- estados desconhecidos, não avaliáveis, ambíguos e pendentes permanecem distintos de ausência confirmada.

## Organização documental

### Modelo e variáveis

- [`conceptual_model.md`](conceptual_model.md): entidades, relações e limites analíticos.
- [`variable_dictionary.md`](variable_dictionary.md): dimensões e variáveis.
- [`procurement_model.md`](procurement_model.md): compras e contratos tecnológicos.
- [`data_flow_model.md`](data_flow_model.md): fluxos entre sistemas.
- [`ai_systems_protocol.md`](ai_systems_protocol.md): evidências públicas de IA e automação.
- [`risk_assessment_protocol.md`](risk_assessment_protocol.md): dependências e riscos.

### Evidência, integridade e proveniência

- [`evidence_and_validation_protocol.md`](evidence_and_validation_protocol.md): evidência, confiança e validação.
- [`relational_integrity.md`](relational_integrity.md): referências, coerência temporal e bloqueios.
- [`data_provenance_model.md`](data_provenance_model.md): fonte, aquisição, transformação, agentes e versões.

### Memória longitudinal

- [`temporal_memory_model.md`](temporal_memory_model.md): eventos, versões e preservação histórica.
- [`snapshot_policy.md`](snapshot_policy.md): abertura, fechamento e tipos de snapshot.
- [`longitudinal_comparison_policy.md`](longitudinal_comparison_policy.md): comparação entre períodos.
- [`schema_migration_policy.md`](schema_migration_policy.md): migrações e comparabilidade.
- [`retention_policy.md`](retention_policy.md): retenção dos produtos temporais.

### Curadoria, qualidade e indicadores

- [`curatorial_governance.md`](curatorial_governance.md): papéis humanos e segregação de funções.
- [`review_and_approval_workflow.md`](review_and_approval_workflow.md): revisão e aprovação.
- [`data_quality_and_maturity_policy.md`](data_quality_and_maturity_policy.md): qualidade e maturidade.
- [`fitness_for_use_policy.md`](fitness_for_use_policy.md): aptidão por finalidade.
- [`indicator_governance_policy.md`](indicator_governance_policy.md): governança dos indicadores.
- [`indicator_catalog.md`](indicator_catalog.md): famílias conceituais e propostas futuras; não substitui o registro computável ativo.

### Publicação e acesso

- [`publication_access_policy.md`](publication_access_policy.md): camadas de acesso.
- [`data_products_catalog.md`](data_products_catalog.md): produtos previstos e implementados.
- [`public_derived_view.md`](public_derived_view.md): visão pública derivada.
- [`public_delivery_projection.md`](public_delivery_projection.md): projeção estável para consumo público.
- [`api_publication_contract.md`](api_publication_contract.md): contrato da futura API somente leitura.

### Ética, direito e responsabilização

- [`ethical_legal_risk_policy.md`](ethical_legal_risk_policy.md): princípios e níveis de risco.
- [`automated_collection_limits.md`](automated_collection_limits.md): limites da coleta automatizada.
- [`personal_data_and_sensitive_information_policy.md`](personal_data_and_sensitive_information_policy.md): dados pessoais e sensíveis.
- [`claims_corrections_and_contestations.md`](claims_corrections_and_contestations.md): correções e contestações.

### Implementação

- [`technical_implementation_roadmap.md`](technical_implementation_roadmap.md): plano histórico e estado consolidado das fases técnicas.
- [`fase1_implementation.md`](fase1_implementation.md): implementação do núcleo de dados e proveniência.
- [`fase2_implementation.md`](fase2_implementation.md): integração da auditoria, revisão, memória e analytics.
- [`module_mapping.md`](module_mapping.md): ligação entre documentos, schemas e módulos existentes.
- [`implementation_acceptance_criteria.md`](implementation_acceptance_criteria.md): critérios de aceite.
- [`implementation_backlog.md`](implementation_backlog.md): backlog vigente e prioridades atuais.

## Estado atual

O núcleo técnico está implementado estruturalmente. A prioridade vigente é consolidar documentação, validar empiricamente os detectores e indicadores, executar um ciclo longitudinal controlado e definir a vitrine pública. A existência de código, schemas e testes não deve ser apresentada como validação empírica concluída.
