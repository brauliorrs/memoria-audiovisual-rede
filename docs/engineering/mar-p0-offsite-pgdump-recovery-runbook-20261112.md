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
