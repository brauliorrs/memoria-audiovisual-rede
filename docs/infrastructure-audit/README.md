# Auditoria de infraestrutura digital

Esta pasta organiza a documentação metodológica e técnica da camada que observa tecnologias, APIs, metadados, interoperabilidade, busca, restrições públicas e sinais declarados de IA nas superfícies digitais dos corpora.

## Documentos

- [Arquitetura](ARCHITECTURE.md): finalidade, princípios, fluxo, camadas, produtos e limites interpretativos.
- [Contrato de dados](DATA_CONTRACT.md): campos, enums, chaves, regras de qualidade e versionamento.
- [Protocolo de validação](VALIDATION_PROTOCOL.md): passagem de sinais heurísticos para evidências validadas e critérios de publicação.
- [Porta 2](PORTA_2.md): critérios técnicos de passagem entre a infraestrutura estrutural e a execução piloto controlada.
- [JSON Schema](../../schemas/digital_infrastructure_audit.schema.json): representação formal do contrato estrutural.

## Componentes de código

- detector heurístico: `src/memoria_audiovisual/digital_infrastructure_audit.py`;
- adaptador contratual: `src/memoria_audiovisual/statetech/digital_infrastructure_adapter.py`;
- revisão curatorial versionada: `src/memoria_audiovisual/statetech/digital_infrastructure_review.py`;
- executor: `scripts/audit_digital_infrastructure.py`;
- testes dos detectores: `tests/test_digital_infrastructure_audit.py`;
- testes da Porta 2: `tests/test_digital_infrastructure_phase2.py`;
- automação: `.github/workflows/audit-digital-infrastructure.yml`.

## Estado atual

A implementação candidata à Porta 2 alinha a coleta heurística ao contrato de dados `1.0.0` e ao núcleo append-only Estado–tecnologia. Cada rodada recebe `snapshot_id`; cada sinal é normalizado como detecção independente; toda detecção automática inicia em `pending_review`; e decisões curatoriais criam novas versões em vez de sobrescrever a observação original.

O executor preserva as saídas legadas e cria três superfícies distintas:

- `digital_infrastructure_audit_raw.*`: observações e detecções automatizadas;
- `digital_infrastructure_audit_curated.*`: decisões humanas concluídas, excluindo falsos positivos;
- `digital_infrastructure_audit_publishable.*`: somente `confirmed` e `probable`, aptos a alimentar indicadores quando os demais critérios metodológicos forem satisfeitos.

O histórico transacional é mantido em `digital_infrastructure_audit_ledger.jsonl`. O ledger é append-only e pode ser versionado; uma nova rodada não deve reutilizar um `snapshot_id` deliberadamente já registrado.

## Sequência de passagem

1. código alinhado ao contrato de dados `1.0.0`;
2. observação, detecção e revisão separadas;
3. saída bruta, curada e publicável separadas;
4. registro longitudinal append-only e revisão sem sobrescrita;
5. validação automatizada do contrato e das barreiras de publicação;
6. execução piloto controlada;
7. validação humana da amostra diversa definida no protocolo;
8. somente depois, exposição de indicadores de infraestrutura/IA no Streamlit.

A interface pública permanece passiva em relação à coleta: o Streamlit não dispara auditorias. A exposição de novos indicadores fica deliberadamente bloqueada até existirem registros curados/publicáveis suficientes.

## Regra de publicação

Nenhum indicador técnico deve ser apresentado como resultado científico enquanto estiver em `pending_review`. `false_positive` nunca alimenta a camada curada ou publicável. `inconclusive` e `not_assessable` podem compor auditoria e denominadores metodológicos, mas não são evidência positiva. A ausência de detecção nunca deve ser publicada como prova de ausência da tecnologia.
