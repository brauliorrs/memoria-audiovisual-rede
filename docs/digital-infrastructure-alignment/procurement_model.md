# Modelo de compras e contratos tecnológicos

## Objetivo

Registrar instrumentos que conectem instituições audiovisuais públicas a fornecedores, sistemas e serviços tecnológicos.

## Fontes previstas

- portais de compras e transparência;
- TED e portais nacionais de contratação;
- contratos, adjudicações, editais e atas;
- relatórios anuais e documentos orçamentários;
- páginas institucionais com identificação explícita do fornecedor.

## Entidade `ProcurementContract`

Campos principais:

- `contract_id`;
- `institution_id`;
- `contracting_authority`;
- `supplier_id` e `supplier_name`;
- `procurement_identifier`;
- `contract_title`;
- `contract_scope`;
- `technology_ids`;
- `provider_roles`;
- `procurement_method`;
- `contract_value` e `currency`;
- `award_date`, `start_date`, `end_date`;
- `contract_status`;
- `procurement_portal` e `contract_url`;
- `evidence_id`;
- `validation_status`.

## Regras

- não inferir contrato a partir da simples presença de tecnologia;
- separar fornecedor contratado de subcontratado, parceiro ou operador;
- preservar valor original e moeda, sem conversão silenciosa;
- contratos sem valor público permanecem válidos com `contract_value` vazio;
- aditivos devem referenciar o contrato principal quando identificáveis;
- objetos amplos devem ser descritos sem atribuir ao audiovisual uma parcela não documentada;
- instrumentos de cooperação não devem ser classificados automaticamente como compra.

## Relações

Um contrato pode envolver vários fornecedores, tecnologias e papéis. A implementação futura deve admitir tabelas relacionais em vez de repetir o contrato principal.