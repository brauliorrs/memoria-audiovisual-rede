# MAR — Motor universal de admissão de corpora (contratos e testes antes do código)

**Data:** 16/11/2026. **Base técnica:** PR #95, `feat/mar-approved-corpora-admission-20261116` (draft), mantido separado da `main`. O PR #94 cuida da navegação, PR #96 da reconciliação Eye/Czech e PR #97 das propostas documentais, sem publicação. O PR #93 permanece HOLD para backup em produção.

## Inventário e limites

- O leitor PR #95 publica fichas adicionais somente mediante par `mar_admitted/<corpus>.csv` + manifesto verificado por SHA-256, campos e URLs; cinco corpora ativos na *allowlist* de admissão: `eye`, `czech-television`, `ciclic`, `asim`, `bnfa`.
- `CORPORA` é registro analítico/científico existente e amplo, não uma autorização para a nova admissão. Não alterar flags científicas `organism_active`, `monthly_refresh_enabled`, nem `counts_as_analyzed_corpus`.
- APE, KAVI em atualização e futuras fontes **não são automaticamente habilitados** por sua existência no registro científico, pelo coletor ou por probes. Nenhum novo corpus foi efetivamente aprovado neste incremento.
- O motor não descobre novos domínios automaticamente: cadastro de um novo conector é revisão de código e prova de origem, com teste individual e nova aprovação científica. Metadados de status em JSON nunca se tornam uma credencial ou autorização por si só.

## Matriz de impacto

| Mudança | Dependências | Risco a prevenir | Testes | Rollback |
| --- | --- | --- | --- | --- |
| Registro tipado imutável de conectores | `approved_corpus_admission.CORPUS_HOSTS`, domínios legados | Alargar host permitido ou tornar fonte HOLD publicável | U1, U2, U3 | Reverter import do registro |
| Contrato canônico de ficha | `FIELDS`, leitor CSV e PR #97 | Quebra de 12 campos, direitos inferidos, mídia direta | U4, U5 | Restaurar 12 campos literais |
| Estado científico/operacional individual | planejamento e verificação offline, sem DB | Autoaprovação, bypass, salto para `published` por rótulo | U6, U7, U8 | Remover módulo de workflow |
| Índice de saúde e capacidade | catálogo e futuras instituições | Confundir "conector cadastrado" com corpus validado/publicado | U9, U10 | Remover exportação derivada |
| Compatibilidade e integração | leitor PR #95, testes de publicação, app | Regressões, rede/secrets, escrita em `main` | U11, U12 | Remover arquivos novos e reverter import |

## Contratos de implementação

1. **Registro:** `ConnectorSpec` imutável com `corpus_code`, `institution`, `adapter_module`, `record_hosts`, `source_kind`, `onboarding_state`. Registro em Python com cinco entradas revisadas, sem execução dinâmica de imports ou plugins. APE expressamente em HOLD fora da allowlist. `record_hosts` conserva exatamente os domínios do PR #95. Chaves duplicadas/domínios inválidos bloqueados.
2. **Modelo comum:** ficha documental de 12 campos PR #95 (id, URL, título, ano, autores, assunto, idiomas, gêneros, descrição, estados de acesso/direitos/revisão). Estado de mídia sempre `unverified`, direitos `not_verified`; campos desconhecidos permanecem vazios. A extensão de campos exige migração versionada.
3. **Estados por fonte:** `registered` → `probed` → `evidence_validated` → `curator_reviewed` → `admission_ready`; `HOLD` é destino a partir de qualquer estado e só pode reabrir com autorização explícita para `registered`. Transições não pulam etapas, requerem IDs de evidência para os passos de validação/revisão, e nunca implicam publicação. `published` é reservado ao gate real (CSV + manifesto PR #95 e revisão independente de PR no GitHub).
4. **Decisão operacional:** uma função pura estima se uma fonte pode **submeter proposta** (não publicar). Bloqueia APE, fonte desconhecida ou estado insuficiente. A aprovação de um manifesto continua sob o validador PR #95 e revisão independente de código/dados; não substituir esse gate por uma máquina de estados autorreferida.
5. **Regressões:** U1 registro inicial = 5 fontes e domínios iguais ao contrato; U2 APE/fora de registro HOLD; U3 host e código inválidos; U4 12 campos; U5 mídia não verificada; U6 trilha linear; U7 salta/regride sem evidência = rejeição; U8 HOLD impede entrada sem reabertura explícita; U9 painel mostra status **operacional**, não científico; U10 >100 registros sintéticos possíveis sem ativação automática; U11 testes legados `test_approved_corpus_admission` verdes; U12 CI geral e teste de deploy separado.
6. Nenhum coletor, requisição HTTP, scraping, cron, migração Neon, mudança de secrets, dados publicados, mídia baixada ou PR mergeado neste incremento.

**Definition of Done:** código, documentação e testes registrados no PR, CI quality íntegro no HEAD, revisão humana e eventual merge sequenciado após PR #95. Um teste verde NÃO substitui autorização científica do corpus.
