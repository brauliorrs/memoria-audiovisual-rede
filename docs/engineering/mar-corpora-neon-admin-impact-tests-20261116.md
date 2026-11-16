# MAR — auditoria de impacto: PostgreSQL/Neon + painel administrativo de corpora
Data: 16/11/2026. **Pré-registro antes de modificar código ou banco.**

## 1. Linha de base verificada
- Código: PR #98 (draft), ramificado do PR #95 (draft). O registro está em `corpus_admission_engine.REGISTRY` (cinco conectores admitidos tecnicamente: Eye, Czech Television, CICLIC, ASIM, BNFA). Estado `registered` não significa aprovação científica. PR #93 segurança P0 continua em HOLD de produção.
- Neon: projeto `holy-bread-70461948` (`neon-erin-field`), branch `main` de produção `br-raspy-river-b8qx9oo9`. Inspeção somente leitura mostrou tabelas `neon_auth.*`, **nenhuma `mar_corpora.*`**. Branch prévia isolada `mar-p0-validation-20261021` (`br-lingering-smoke-b8hjdnzb`) disponível para derivar teste.
- A plataforma pública atual é Streamlit. Dependências `streamlit==1.55.0`; **não existe controle de acesso administrativo auditado na aplicação pública**. Exposição do painel nesse app seria risco crítico.
- Não criar permissões ou secrets de produção implicitamente, não utilizar `MAR_P0_READONLY_DATABASE_URL`, não compartilhar credenciais da fonte com o leitor de dashboard.

## 2. Contratos e componentes
A. Schema aditivo `mar_corpora` com `connector_registry` (espelho exato e imutável do registro em código; SHA-256 da definição) e `audit_events` (eventos acrescidos por INSERT, com identidade, estágio declarativo, hash de evidência e data do servidor). Proibir UPDATE/DELETE/TRUNCATE por privilégio e trigger; isto é append-only por política PostgreSQL, **não WORM** contra owner/superuser. Índices por corpus/último evento e view `current_status`. Nada altera `neon_auth` ou dados P0.
B. Dois papéis NOLOGIN distintos (`mar_corpora_reader`, `mar_corpora_ingester`) para concessão posterior a contas reais específicas; leitor só SELECT, ingester só SELECT+INSERT. Sem senha gerada ou acesso externo nesta etapa.
C. Importador local executado somente por operador (nunca em inicialização do app ou cron) que espelha cinco conectores, confere hash e recusa divergência sem atualização silenciosa. Registra evento `registered` único por fonte. Histórico de validação adicional apenas por evidências formalmente registradas em PR específico; banco **não decide nem comprova** revisão independente.
D. Painel de administração separado de `app/streamlit_app.py` em `admin/corpora_dashboard.py`, de uso interno, **somente leitura**, com exigência de login OIDC do Streamlit e e-mail verificado pertencente a allowlist no servidor. O painel deve falhar fechado sem auth, allowlist ou URL do banco de leitura. Sem botões de aprovação/publicação nem queries DML; resultados paginados. Não incluir a rota no menu público.
E. Configuração por ambiente de duas URLs diferentes de banco (`MAR_CORPORA_READONLY_DATABASE_URL`, `MAR_CORPORA_INGESTER_DATABASE_URL`), cada uma de papel restrito em branch escolhida; nenhum hardcode de senha. Migração rastreada em SQL do repositório e testada exclusivamente em branch Neon isolada; **não migrar main sem gate de aprovação**.

## 3. Matriz de impacto e testes (antes de código)
| Risco | Contrato | Teste |
| --- | --- | --- |
| Falsa aprovação científica por status de banco | View informativa, sem coluna de autorização; nenhum código chama PR #95 para publicar | DB1 |
| Corrupção de registro técnico | Insert idempotente, recusa drift SHA em corpus existente | DB2 |
| Alteração/supressão de histórico | INSERT-only + trigger e privilégios separados | DB3 |
| Identidade e origem | Actor não pode ser inferido de string arbitrária como prova de revisão; evento contém hash declarativo | DB4 |
| UI pública vazando dados internos | Entry point exclusivo `admin/` com login OIDC/allowlist verificado; sem query pré-auth | DB5 |
| Credenciais elevadas | Duas URLs env distintas; painel somente conexão read-only | DB6 |
| Escala | SQL filtro/paginação com índice por corpus, queries parametrizadas | DB7 |
| Contratos anteriores | `REGISTRY`, `FIELDS`, `CORPORA`, acervo e workflow P0 inalterados | DB8 |
| Migração | Rodar somente em branch isolada, observar schema, inserts, guards, rollback por isolamento | DB9 |
| CI | unittest novos e suite de qualidade verdes em SHA final | DB10 |

## 4. Gates e reversão
Definition of Done deste incremento: código e migração versionados, teste isolado Neon bem-sucedido, painel administrativo criado e protegido; PR draft com CI e revisão independente antes de merge. Não atestar deploy nem PostgreSQL de produção modificado. A promoção de banco exige planejamento de permissões, backup/restauração P0, aprovação humana e migração manual futura via conexão direta. Reversão: descartar branch Neon de ensaio separadamente (somente mediante autorização de exclusão), remover módulo, painel e migração do PR; nenhum dado de produção afetado.
