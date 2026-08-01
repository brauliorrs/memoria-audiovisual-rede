# Integridade relacional da camada Estado–tecnologia

## Objetivo

Definir as regras que deverão garantir consistência entre instituições, tecnologias, fornecedores, contratos, fluxos de dados, sistemas de IA, evidências e avaliações de risco.

Esta etapa é exclusivamente estrutural. Nenhuma validação foi executada.

## Princípios

1. Todo identificador referenciado deve existir na tabela de origem correspondente.
2. Relações não podem depender apenas de inferência técnica quando exigirem vínculo institucional, contratual ou jurídico.
3. Registros publicados devem apontar para evidência verificável e status de revisão compatível.
4. Ausência de vínculo documentado não equivale a inexistência da relação.
5. Toda regra de integridade deve possuir código, severidade, versão e descrição reproduzível.

## Tipos de verificação

### Integridade de identificadores

- `institution_id` deve existir em `institutions.csv`.
- `technology_id` deve existir em `technologies.csv`.
- `provider_id` deve existir em `providers.csv` quando preenchido.
- `contract_id`, `data_flow_id`, `ai_system_id`, `risk_id` e `evidence_id` devem existir nas respectivas entidades.

### Integridade de evidência

Relações institucionais, contratuais, de IA e de risco devem possuir ao menos uma evidência associada antes de receber status `confirmed`.

### Integridade temporal

- `end_date` não pode anteceder `start_date`.
- contratos expirados não devem ser marcados como ativos sem justificativa explícita.
- snapshots devem registrar `observed_at`.

### Integridade semântica

- fornecedor não pode ser inferido apenas pela presença de software detectado;
- contrato não pode ser inferido apenas por menção institucional;
- sistema de IA operacional exige evidência superior a anúncio ou linguagem promocional;
- risco crítico exige regra versionada e revisão humana.

## Severidades

- `error`: impede publicação e integração.
- `warning`: permite armazenamento, mas não publicação como indicador validado.
- `info`: sinaliza lacuna documental ou enriquecimento recomendado.

## Estados de resolução

- `open`
- `accepted_exception`
- `resolved`
- `false_alarm`

## Produto previsto

A futura verificação poderá gerar:

- `data/output/statetech_integrity_report.json`
- `data/output/statetech_integrity_issues.csv`

Nenhum desses produtos é gerado nesta etapa.
