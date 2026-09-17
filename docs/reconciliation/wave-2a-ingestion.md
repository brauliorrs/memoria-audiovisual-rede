# Onda 2A — ingestão, artefatos brutos e lotes

## Delimitação validada

Este recorte porta seletivamente do PR #5 apenas a camada necessária para receber
fontes externas sem ainda introduzir cobertura, revisão curatorial, materialização,
publicação, analytics, UI ou IA.

Entram:
- contrato genérico de adaptadores;
- preservação content-addressed de entrada bruta;
- manifestos append-only de lote;
- coordenador de ingestão em preview/commit;
- retomada de lotes interrompidos;
- locking de artefato, manifesto e lote;
- fingerprint semântico fail-closed do conjunto adaptado.

Não entra o adaptador antigo do PR #5. A Porta 2 e suas invariantes permanecem
protegidas pelo código e pelos testes já presentes na main.

## Regras de segurança

1. Todo lote é validado antes da primeira persistência.
2. A fonte bruta é identificada por SHA-256 e nunca sobrescrita.
3. Um mesmo batch é serializado por lock durante todo o ciclo de commit.
4. O manifesto permanece append-only.
5. Retomada exige igualdade de fingerprint e de contagem de registros.
6. Manifestos legados sem fingerprint não são retomados automaticamente.
7. Mudança de saída do adaptador para a mesma fonte/versão aborta antes de nova persistência.
8. Evidências continuam fluindo individualmente para o serviço canônico e permanecem pending_review salvo decisão explícita.

## Gate

A Onda 2A só pode ser integrada com:
- suíte completa verde;
- testes específicos de ingestão/fail-closed verdes;
- contrato Porta 2 verde;
- dependency manifest verde;
- deployment snapshot verde.
