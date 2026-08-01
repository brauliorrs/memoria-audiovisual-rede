# Auditoria de infraestrutura digital

Esta pasta organiza a documentação metodológica e técnica da camada que observa tecnologias, APIs, metadados, interoperabilidade, busca, restrições públicas e sinais declarados de IA nas superfícies digitais dos corpora.

## Documentos

- [Arquitetura](ARCHITECTURE.md): finalidade, princípios, fluxo, camadas, produtos e limites interpretativos.
- [Contrato de dados](DATA_CONTRACT.md): campos, enums, chaves, regras de qualidade e versionamento.
- [Protocolo de validação](VALIDATION_PROTOCOL.md): passagem de sinais heurísticos para evidências validadas e critérios de publicação.
- [JSON Schema](../../schemas/digital_infrastructure_audit.schema.json): representação formal do contrato estrutural.

## Componentes de código já existentes

- detector: `src/memoria_audiovisual/digital_infrastructure_audit.py`;
- executor: `scripts/audit_digital_infrastructure.py`;
- testes: `tests/test_digital_infrastructure_audit.py`;
- automação: `.github/workflows/digital-infrastructure-audit.yml`.

## Estado atual

A infraestrutura de código e a estrutura documental estão definidas. Nenhuma execução é necessária para esta etapa. Os resultados brutos, validados e longitudinais permanecem produtos previstos até que uma rodada seja deliberadamente autorizada.

## Ordem recomendada para evolução

1. alinhar o código existente ao contrato de dados `1.0.0`;
2. criar modelos internos para observação, detecção e revisão;
3. separar saída bruta de saída curada;
4. criar registro longitudinal sem sobrescrita;
5. implementar leitura passiva no Streamlit, sem disparar coleta pela interface;
6. somente depois executar rodada piloto e validar os detectores.

## Regra de publicação

Nenhum indicador técnico deve ser apresentado como resultado científico enquanto estiver em `pending_review`. A ausência de detecção nunca deve ser publicada como prova de ausência da tecnologia.