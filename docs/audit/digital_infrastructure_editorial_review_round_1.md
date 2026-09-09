# Revisão editorial da documentação de infraestrutura digital — rodada 1

## Escopo

Esta rodada iniciou a revisão arquivo por arquivo de `docs/digital-infrastructure-alignment/`, priorizando documentos que controlam a interpretação dos demais:

- `README.md`;
- `technical_implementation_roadmap.md`;
- `module_mapping.md`;
- `indicator_catalog.md`;
- `ai_systems_protocol.md`.

## Problemas identificados

1. O índice ainda descrevia partes implementadas como módulos futuros.
2. O roadmap técnico apresentava todas as fases no futuro, embora várias já estejam implementadas estruturalmente.
3. O catálogo conceitual podia ser confundido com o registro computável ativo dos indicadores.
4. O protocolo de IA não explicitava todos os estados avaliativos nem a diferença entre ausência de evidência pública e ausência institucional de IA.
5. O mapeamento de módulos apontava para uma arquitetura hipotética diferente dos caminhos existentes no repositório.
6. Não havia controle automatizado específico para referências analíticas obsoletas e linguagem metodologicamente insegura neste diretório.

## Correções aplicadas

- o índice passou a declarar a hierarquia canônica entre Research Handbook, registros analíticos e documentação técnica;
- o roadmap técnico agora registra o estado real de cada fase;
- o mapa de módulos foi alinhado ao pacote `src/memoria_audiovisual/digital_infrastructure/` e ao pacote `analytics/`;
- o catálogo foi renomeado conceitualmente e separado do registro ativo;
- o protocolo de IA passou a trabalhar com evidências públicas, estados avaliativos e regra formal de ativação de indicador;
- foi criado `scripts/audit_digital_infrastructure_docs.py`;
- o workflow `Documentation Quality` passou a executar essa auditoria.

## Primeira execução automatizada

A primeira execução encontrou:

- **0 erros bloqueantes**;
- **9 avisos**.

Oito avisos eram falsos positivos relacionados à branch durável `digital-infrastructure-history`. A regra foi corrigida para distinguir branch histórica de branches provisórias. O aviso editorial real, “módulo futuro”, foi corrigido em `module_mapping.md`.

## Limite desta rodada

Esta rodada não conclui a leitura substantiva de todos os documentos do diretório. Os próximos blocos prioritários são:

1. evidência, validação e proveniência;
2. snapshots, comparação longitudinal e eventos;
3. publicação, revisão, contestação e retirada;
4. qualidade, maturidade, fitness for use, ética e risco;
5. fluxos, contratos e dados pessoais;
6. documentos de implementação das Fases 1 e 2.

## Critério de conclusão da etapa 3

A etapa será considerada concluída quando:

- todos os documentos tiverem sido classificados como vigentes, históricos ou substituídos;
- definições duplicadas apontarem para uma fonte canônica;
- referências provisórias não permanecerem em documentos normativos;
- indicadores conceituais e ativos estiverem inequivocamente separados;
- linguagem de detecção, ausência, risco e IA estiver proporcional à evidência;
- a auditoria automática concluir sem erros e sem avisos não justificados.
