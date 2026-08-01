# Dicionário de variáveis

Versão inicial para desenho de dados. Campos opcionais devem permanecer vazios quando não houver evidência suficiente.

## 1. Natureza institucional

| Campo | Descrição |
|---|---|
| `institution_id` | Identificador estável da instituição |
| `institutional_ownership` | Natureza pública, privada, híbrida, supranacional ou desconhecida |
| `institutional_level` | Nacional, regional, local, supranacional ou não aplicável |
| `public_body_type` | Arquivo, cinemateca, emissora pública, fundação, ministério etc. |
| `government_affiliation` | Órgão, governo ou estrutura administrativa vinculada |
| `administrative_autonomy` | Grau documentado de autonomia |
| `public_service_function` | Função pública associada ao audiovisual |
| `funding_model` | Público, misto, privado, projeto, desconhecido |
| `legal_status` | Forma jurídica documentada |

## 2. Fornecedores e relações tecnológicas

| Campo | Descrição |
|---|---|
| `provider_id` | Identificador estável do fornecedor |
| `provider_legal_name` | Razão social ou nome oficial |
| `provider_country` | País de sede quando documentado |
| `provider_type` | Empresa, órgão público, fundação, consórcio, comunidade open source |
| `provider_role` | Hospedagem, nuvem, software, digitalização, busca, IA, integração etc. |
| `provider_relationship` | Contratado, operador, mantenedor, parceiro, desenvolvedor, desconhecido |
| `relationship_start_date` | Início documentado |
| `relationship_end_date` | Fim documentado |
| `provider_confidence` | Confiança da identificação |

## 3. Contratos e compras

`procurement_detected`, `procurement_identifier`, `contracting_authority`, `supplier_name`, `contract_title`, `contract_value`, `currency`, `award_date`, `contract_start_date`, `contract_end_date`, `procurement_method`, `procurement_portal`, `contract_url`, `contract_scope`, `contract_status`.

## 4. Stack tecnológico

`technology_id`, `technology_name`, `technology_function`, `stack_layer`, `deployment_model`, `ownership_model`, `hosting_location`, `cloud_provider`, `data_residency_country`, `open_source_status`, `vendor_lock_in_signal`, `critical_dependency`.

Valores controlados para `stack_layer`:

`physical_infrastructure`, `cloud_and_hosting`, `network_and_cdn`, `database`, `repository_management`, `metadata_layer`, `api_and_interoperability`, `search_and_discovery`, `authentication`, `rights_management`, `analytics`, `ai_and_automation`, `presentation_interface`, `external_distribution_platform`.

## 5. Fluxos de dados

`data_flow_id`, `data_source`, `data_destination`, `data_flow_type`, `data_exchange_method`, `data_format`, `transfer_frequency`, `purpose`, `personal_data_signal`, `cross_border_data_flow`, `third_party_processing`, `automated_decision_signal`.

Tipos iniciais: `metadata_ingestion`, `metadata_export`, `media_streaming`, `catalogue_synchronisation`, `authentication_exchange`, `analytics_tracking`, `content_syndication`, `api_query`, `bulk_export`, `manual_transfer`.

## 6. Governança

`data_controller`, `data_processor`, `data_governance_document`, `privacy_policy_available`, `terms_of_use_available`, `retention_policy_detected`, `data_sharing_policy`, `open_data_policy`, `data_license`, `rights_statement`, `algorithmic_transparency`, `auditability`.

## 7. IA e automação

`ai_system_id`, `ai_use_detected`, `ai_system_name`, `ai_provider`, `ai_function`, `ai_model_type`, `ai_deployment_stage`, `human_oversight`, `training_data_disclosure`, `automated_output_public`, `algorithmic_transparency`, `impact_area`.

Funções iniciais: `automatic_transcription`, `speech_to_text`, `ocr`, `image_recognition`, `face_recognition`, `object_detection`, `automatic_translation`, `metadata_enrichment`, `entity_extraction`, `recommendation`, `search_ranking`, `content_moderation`, `rights_detection`, `restoration`, `classification`.

Estágios: `announced`, `pilot`, `operational`, `discontinued`, `unknown`.

## 8. Dependências e riscos

`platform_dependency`, `vendor_concentration`, `single_provider_dependency`, `proprietary_format_dependency`, `external_platform_dependency`, `authentication_dependency`, `cloud_dependency`, `interoperability_risk`, `service_discontinuity_risk`, `digital_extinction_risk`, `public_accountability_risk`.

Escala: `not_assessed`, `low`, `moderate`, `high`, `critical`.

## 9. Evidência e validação

Todos os conjuntos relacionais devem admitir: `evidence_id`, `evidence_url`, `evidence_type`, `evidence_date`, `observation_date`, `evidence_excerpt`, `collection_method`, `confidence`, `validation_status`, `reviewer_note`.

Estados de validação: `pending_review`, `confirmed`, `probable`, `inconclusive`, `false_positive`, `not_assessable`.