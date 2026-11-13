# MAR P0 — Backup criptografado e restauração externa: protocolo de execução

Data: 12/11/2026. **Estado: CLI e testes offline preparados. Backup REAL e restauração independente NÃO executados. Gate P0 externo: HOLD.**

## Infraestrutura já existente

- Origem: Neon/PostgreSQL 18, projeto neon-erin-field, branch mar-p0-validation-20261021 (br-lingering-smoke-b8hjdnzb), esquema mar_p0.
- A role mar_p0_limited tem permissão SELECT nas três tabelas, sem necessidade de ampliar privilégios.
- A recuperação integral interna por branching foi comprovada anteriormente em mar-p0-neon-integral-recovery-proof-20261112.md: 4 checkpoints, 8 páginas, 4 artefatos e SHA-256 idêntico para todos os dados e 69 definições de esquema.

## Tentativa de exportação offsite nesta sessão

Foi criado um projeto temporário Vercel mar-p0-recovery-lab com sandbox e drive privado. O sandbox conectou-se à porta 5432 do Neon e recebeu PostgreSQL client 18 e biblioteca AES-GCM. A tentativa de fornecer a credencial Neon ao executor Vercel por conectores foi **BLOQUEADA POR RESTRIÇÃO DE SEGURANÇA**. Não contornar esse bloqueio mediante codificação, uploads, comandos alternativos ou logs.

Foi confirmado que nenhum arquivo de dump ou backup foi escrito no Drive. O sandbox foi encerrado e removido, e o Drive vazio removido. O projeto Vercel de laboratório foi mantido, com duas chaves de teste não utilizadas; nenhuma credencial de acesso PostgreSQL foi registrada nele. A branch de validação, a main e a branch de recuperação anterior não foram alteradas.

**Resultado real deste ensaio: backup não exportado; restauração externa não executada.**

## Implementação para executor autorizado

O script scripts/mar_p0_offsite_pg_restore.py implementa exportação e restauração fail-closed. As credenciais devem ser disponibilizadas **diretamente pelo operador ao executor aprovado**, via secret manager, não por transferência entre ferramentas ou ChatGPT.

Requisitos de execução:

1. Python 3.11+ e cryptography, PostgreSQL client 18 (psql/pg_dump/pg_restore); certificado CA do sistema.
2. MAR_P0_READONLY_DATABASE_URL: URI da branch de validação Neon sob role mar_p0_limited; TLS verify-full e channel binding obrigatórios.
3. MAR_P0_RESTORE_AES_KEY_HEX: chave aleatória hex de 32 bytes, mantida separadamente do armazenamento cifrado.
4. Destino externo durável ao Neon, privado e versionado, com diretório 0700 e escrita exclusiva de backup cifrado 0600.
5. Outro executor com PostgreSQL 18 local, banco NOVO vazio cujo nome comece com mar_p0_restore_, e MAR_P0_ISOLATED_RESTORE_DATABASE_URL apontando apenas a localhost/127.0.0.1/::1.

Backup: com as variáveis já injetadas diretamente pelo secret manager no executor, executar:

    install -d -m 0700 /mnt/private-backup/mar_p0
    python -m scripts.mar_p0_offsite_pg_restore backup --encrypted-file /mnt/private-backup/mar_p0/validation.pgcustom.aesgcm --execute

O script calcula fingerprint SHA-256 de todas as linhas das três tabelas, da definição do esquema, e os indicadores de integridade interna; executa pg_dump custom limitado a mar_p0; remove o dump em claro do temporário após cifrar com AES-256-GCM; grava só arquivo cifrado no armazenamento persistente. Não permite overwrite.

Restauro: com o mesmo segredo fornecido diretamente pelo secret manager ao segundo executor e com a cópia cifrada proveniente do armazenamento externo:

    python -m scripts.mar_p0_offsite_pg_restore restore --encrypted-file /mnt/private-backup/mar_p0/validation.pgcustom.aesgcm --expected-sha256 SHA256_DO_BLOB_CIFRADO --execute

Verifica hash independente do ciphertext, tag de autenticação GCM, SHA-256 do dump, banco vazio, e executa pg_restore em uma transação, sem --clean, sem sobrescrever banco ou esquema preexistente. Confronta novamente contagens e SHA-256 por tabela, colunas/índices/constraints e verificações de FK e conteúdo.

A CLI exige --execute; sem ele, é apenas dry-run. Nenhuma credencial, key, URI ou payload deve aparecer em GitHub Actions, logs ou anexos.

## Critérios do Gate P0 externo

**PASS somente após** exportação REAL de mar_p0 para um arquivo cifrado preservado fora do Neon e restauração com sucesso num PostgreSQL isolado em outro executor, com SHA-256 e contagens conferidos, política de retenção/versionamento e evidências de backup acessíveis após perda da origem. Nenhuma validação de corpora Czech Television pode ser inferida do P0.

**HOLD atual:** não existe comprovante de dump real ou restauração externa. Os novos testes sintéticos são apenas regressões do procedimento.

Arquivos alterados nesta fase: scripts/mar_p0_offsite_pg_restore.py, tests/test_mar_p0_offsite_pg_restore.py e este runbook, exclusivamente no PR #91, nunca na main.


## Gatilho protegido GitHub Actions — preparado em 12/11/2026

Foi adicionado o workflow `.github/workflows/mar-p0-offsite-recovery-gated.yml` **somente na branch do PR #91**. Ele não usa cron nem roda por abertura/push comum de PR. A ativação depende de **label aplicado manualmente pelo usuário `brauliorrs`**: `mar-p0-offsite-restore-approved`, especificamente no PR #91, branch `fix/monthly-cycle-evidence-20261110`, mesma origem do repositório, primeira tentativa da execução. Os dois jobs exigem aprovação do environment GitHub `mar-p0-neon-isolated`, conforme as regras de revisão existentes. Não usa `pull_request_target` nem write token.

**Ações do operador, sem enviar valores a esta conversa:**

1. Abrir configurações do repositório GitHub → Environments → `mar-p0-neon-isolated` → Environment secrets. Configurar `MAR_P0_READONLY_DATABASE_URL` com URI **Direct/unpooled**, banco `neondb`, role `mar_p0_limited`, branch de validação `br-lingering-smoke-b8hjdnzb`, endpoint fixado `ep-damp-term-b8wqhmz0.c-14.us-east-1.aws.neon.tech` (e não `-pooler`). Nunca colar o valor no PR, Issues, logs ou chat.
2. Configurar o segredo `MAR_P0_RESTORE_AES_KEY_HEX` no mesmo environment com 32 bytes aleatórios representados por 64 dígitos hexadecimais, gerados **pelo operador em ambiente protegido**. Guardar cópia de recuperação da chave fora do GitHub e do backup. Não copiar variáveis ou chaves criadas no laboratório Vercel por ChatGPT.
3. Confirmar que o environment está protegido por revisão; criar, se necessário, o label `mar-p0-offsite-restore-approved` na página GitHub de Labels; aplicá-lo ao PR #91 com a conta `brauliorrs`. Aprovar explicitamente os jobs pelo environment ao receber a notificação.
4. Revisar os dois jobs concluídos: `export-encrypted` (somente leitura Neon, AES-256-GCM, upload de ciphertext como GitHub artifact com retenção de 30 dias) e `restore-isolated` (outro runner, banco PostgreSQL 18 local novo, ciphertext obtido do artifact, autenticação GCM, SHA-256/counters/constraints do `mar_p0` conferidos).
5. Arquivar no PR apenas URL do run, SHA-256 do ciphertext, 3 contagens, validação de estrutura e evidência de recuperação. **Nunca** publicar dump em claro nem chave, URI, senha ou credenciais.

**Verificações de segurança do workflow:** limita disparo a um PR específico e usuário explicitamente autorizado; jobs em máquinas descartáveis diferentes; consulta Neon somente em `pg_dump`/SQL read-only, role de menor privilégio e endpoint fixo `Direct`; bloqueio no código para URL de banco remoto de restauração, prefixo de banco local, banco previamente populado, ciphertext adulterado, nonce/chave inválidos e inconsistência estrutural. O resultado nunca promove corpus Czech TV, não altera `main`, não modifica a branch de validação e mantém `production_gate=HOLD`.

**Situação na criação do workflow:** o GitHub environment pode ter ainda segredos ausentes; isso **não** é configurado automaticamente pelos conectores, justamente para não repetir o bloqueio de transferência de credenciais. O workflow foi criado, mas **nenhum backup ou restore externo foi executado** nesta fase. Somente uma execução futura efetivamente aprovada, com todos os controles passando, poderá alterar o status da prova externa para PASS, respeitando o prazo de retenção do artefato de teste.
