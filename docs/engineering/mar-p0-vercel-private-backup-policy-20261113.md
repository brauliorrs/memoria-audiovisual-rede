# MAR P0 — backup recorrente Vercel Blob PRIVATE (proposta)

13/11/2026. **Status: pronto para revisão, não ativo.** Alternativa Vercel à proposta AWS do PR #92. Não ativar duas arquiteturas simultaneamente sem auditoria.

## Capacidade comprovada e limites

Vercel Private Blob permite autenticação para leitura e gravação (GA desde 30/06/2026). O SDK oficial Python oferece uploads privados sem overwrite e downloads autenticados. O projeto Vercel mar-p0-recovery-lab já existe, mas nenhum Private Blob Store foi criado ou confirmado nesta etapa.

**LIMITE CRÍTICO:** Vercel Blob não tem, nas funções verificadas, garantia equivalente ao S3 Object Lock COMPLIANCE (retenção WORM de 90 dias), nem recuperação automática de objetos excluídos. Os controles do script (não sobrescrever, não apagar, hashes e nomes únicos) **não** impedem exclusão por administrador ou por alguém com token de leitura/gravação. GitHub Actions executado fora do Vercel recebe token BLOB_READ_WRITE_TOKEN; tal token também tem permissão de delete. O OIDC rotativo documentado para Vercel Functions não pode ser assumido como credencial OIDC read-only para GitHub Actions. A prova operacional e os requisitos de imutabilidade são gates diferentes. Não declarar WORM no Vercel.

## Dados e fluxos

A origem permitida é somente a branch de validação Neon, esquema mar_p0, banco neondb e role mar_p0_limited (SELECT). Sem vídeos, mídia ou alteração dos coletores. O programa mar_p0_offsite_pg_restore.py foi recuperado da implementação com prova real #43295473787 (Neon → backup AES-GCM externo → PostgreSQL independente, todas as contagens e SHA coincidentes).

Arquivos implementados:
- scripts/mar_p0_offsite_vercel.py: aceita exclusivamente envelope cifrado MAR P0, no máximo 65 MiB, SHA-256 no pathname, upload Private sem overwrite e verificação por download autenticado; não implementa DELETE.
- .github/workflows/mar-p0-vercel-daily-backup.yml: agendamento diário 03h17 UTC; pg_dump encrypt → Vercel Private Blob → readback → download em runner separado → PostgreSQL 18 isolado com comparação integral.
- .github/workflows/mar-p0-vercel-weekly-recovery.yml: aos domingos, 06h17 UTC; lista blobs privados, seleciona snapshot anterior (24–192 horas), verifica SHA e restaura sem conexão ao Neon.
- tests/test_mar_p0_offsite_vercel.py e tests/test_mar_p0_vercel_workflow_guards.py: teste sem rede de caracteres de segredo, chave errada, corrupção, restrição PRIVATE, overwrite, seleção de histórico e branch.

Os agendamentos só executam código da branch padrão main e ainda não foram incorporados a ela. Nunca disponibilizar segredos em comentários, arquivos, URLs públicos ou logs.

## Política de retenção

O objetivo é guardar cada snapshot por no mínimo **90 dias** sem rotina de limpeza. Entretanto, **90 dias é uma política administrativa**, NÃO retenção irremovível do provedor. A implantação deve registrar explicitamente o risco de exclusão por conta ou token comprometidos. Para garantia WORM, é necessária uma segunda cópia em serviço compatível com retenção imutável ou aceitação formal documentada de proteção inferior. Não usar Vercel Blob como única cópia de segurança de dados essenciais sem aceitar e mitigar esse risco.

## Configuração pelo operador, não realizada

1. Escolher projeto Vercel apropriado e criar um **Private Blob store**. A escolha do projeto, custos e criação devem ser aprovados pelo responsável. Não usar Public.
2. Criar GitHub Environment **mar-p0-vercel-export** protegido contra branches diferentes da main. Secrets: MAR_P0_READONLY_DATABASE_URL (Neon Direct com usuário SELECT), MAR_P0_RESTORE_AES_KEY_HEX (AES 32 bytes), MAR_P0_VERCEL_BLOB_READ_WRITE_TOKEN (token desse Private store).
3. Criar GitHub Environment **mar-p0-vercel-recovery**, também limitado à main. Secrets: MAR_P0_RESTORE_AES_KEY_HEX e MAR_P0_VERCEL_BLOB_READ_WRITE_TOKEN. Não colocar URL do Neon no ambiente de recuperação. Os dois jobs usam RW token devido ao limite do provedor; não fingir segregação de permissões que não existe.
4. Manter cópia recuperável da chave AES fora do GitHub e do Vercel, com responsável definido. Rotacionar apenas com plano de recuperar snapshots anteriores.
5. Inspecionar e aprovar PR; executar workflow_dispatch após merge em main, conferir leitura privada e restore independente. Exercitar recuperação semanal com snapshot de 24–192 horas de idade; falhar se não houver backup elegível.
6. Monitorar falha dos jobs, lacuna >48h sem backup, tentativas de acesso inesperado, ausência de snapshots antigos e uso/custos do Blob. Cron GitHub pode atrasar ou ser descartado. Nenhuma mudança de coletores ou promoção de corpus resulta dessa rotina.

## Matriz de aceitação

P0-V01: origem fixada/readonly e criptografia autentificada antes do upload.
P0-V02: destino Private, overwrite recusado, nenhum delete no código e token restrito a environment main.
P0-V03: download e SHA-256 coincidem com ciphertext inicial.
P0-V04: outro runner recupera integralmente Postgres isolado, schema e hashes coincidentes.
P0-V05: exercício semanal recupera snapshot anterior e detecta sua ausência.
P0-V06: custódia de chaves separada, auditoria periódica do armazenamento, monitoramento de falhas.
P0-V07: risco de exclusão não protegida aceito formalmente ou cópia secundária WORM comprovada.

**Decisão:** P0_OFFSITE_RECOVERY_PROOF = PASS (ensaio pontual 13/11/2026). P0_VERCEL_LIVE_BACKUP = HOLD. P0_PROTECTED_90D_RETENTION = HOLD. P0_OPERATIONAL_BACKUP = HOLD até provisionamento, teste real, controle de acesso e resolução do risco de retenção.
