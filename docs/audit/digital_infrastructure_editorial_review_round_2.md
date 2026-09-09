# Revisão editorial da infraestrutura digital — rodada 2

## Escopo

Esta rodada revisou os documentos que governam snapshots, comparação longitudinal, triagem, revisão de eventos, projeção pública, publicação, correções e contestações.

## Documentos revisados

- `snapshot_policy.md`;
- `longitudinal_comparison_policy.md`;
- `longitudinal_event_triage.md`;
- `longitudinal_event_review.md`;
- `publication_access_policy.md`;
- `public_derived_view.md`;
- `publication_revision_policy.md`;
- `claims_corrections_and_contestations.md`.

## Problemas encontrados

1. periodicidades de snapshot apresentadas como política fixa, embora ainda dependam do plano oficial de observação;
2. comparação longitudinal descrita como produto futuro apesar da implementação estrutural existente;
3. ausência em coleta posterior tratada com vocabulário insuficientemente distinto de desaparecimento confirmado;
4. estado `confirmed` próximo demais de autorização automática de publicação;
5. projeção pública derivada confundida potencialmente com publicação externa;
6. política de publicação sem portões editoriais e de contestação suficientemente separados;
7. revisão derivada sem tipologia explícita de correção, contestação, direitos e retirada;
8. protocolo de contestações sem registro mínimo, governança temporal e estado atual.

## Decisões editoriais

- implementação estrutural e validação operacional permanecem separadas;
- snapshots fechados são imutáveis;
- periodicidade é definida por plano de observação versionado;
- não detecção posterior produz candidato a desaparecimento, não desaparecimento confirmado;
- comparação, triagem, revisão, elegibilidade técnica e publicação são camadas distintas;
- quórum de revisão não substitui decisão editorial;
- correções não são eventos empíricos quando o objeto observado não mudou;
- contestações podem gerar marcação, supressão ou retirada cautelar sem admissão automática de erro;
- versões anteriores permanecem preservadas.

## Auditoria automatizada

O script `scripts/audit_digital_infrastructure_docs.py` passou a exigir seções canônicas nos documentos desta rodada e a bloquear regressões como:

- permissão de sobrescrita de snapshot fechado;
- associação automática entre confirmação e publicação;
- ausência de limites editoriais, metodológicos ou de contestação.

## Estado após a rodada

O núcleo temporal e editorial está documentalmente alinhado à arquitetura implementada. Permanecem pendentes:

- validação operacional com dois snapshots controlados;
- teste de falha de coleta, mudança metodológica e possível desaparecimento;
- simulação completa de correção e contestação;
- definição institucional de revisores e responsáveis editoriais;
- integração definitiva com a vitrine, o observatório e a futura API.
