# MAR P0 — política operacional de backups imutáveis e recuperação

Data: 13/11/2026. Estado atual: implementação proposta no PR #91, **sem ativação em produção**.

## Base de evidência e escopo

O teste externo real foi aprovado no [run #43295473787](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/43295473787), com dois runners separados, backup autenticado AES-256-GCM exportado do Neon e restauração integral num PostgreSQL local novo, com correspondência de SHA-256 e estrutura. O artefato desse ensaio expira em 12/12/2026. Esta prova pontual não estabelece retenção durável.

Origem permitida: somente a branch de validação mar-p0-validation-20261021, esquema mar_p0, banco neondb, papel SELECT mar_p0_limited e endpoint Direct fixo. Nenhuma mídia audiovisual nem manuscrito integra esse backup. A main, os coletores e os corpora não são modificados por esta implementação.

O repositório é **público**, com branch padrão **main**. GitHub Actions cron só roda com workflow no branch padrão. Os arquivos adicionados ao PR #91 não programam backups reais até revisão, merge e provisionamento externo.

## Objetivos, contratos e impactos

| Controle | Política | Falha obrigatória |
| --- | --- | --- |
| Backup recorrente | Diário às 03h17 UTC, RPO alvo 24 h | Falta do Neon restrito ou qualquer erro de dump/hash → HOLD |
| Criptografia | AES-256-GCM, nonce aleatório, autenticação antes do upload | Chave inválida, payload alterado ou plaintext → HOLD |
| Armazenamento | Bucket S3 privado, **fora do Neon**, criptografado, versionado | Bucket ausente/público/sem criptografia → HOLD |
| Retenção | Object Lock **COMPLIANCE por no mínimo 90 dias** em cada versão | GOVERNANCE, versão suspensa ou retenção inferior a 90d → HOLD |
| Controle de acesso | IAM com duas roles separadas (upload e recovery), OIDC temporário | Credencial permanente, política excessiva ou branch não autorizada → HOLD |
| Restauração diária | Runner separado, versão e SHA-256 do backup daquele dia | Comparação de registro/esquema/integridade divergente → HOLD |
| Teste semanal | Domingo, 06h17 UTC, cópia anterior de 24 a 192 horas | Sem versão válida, chave indisponível ou erro de restore → HOLD |
| Monitoramento | GitHub workflows falham explicitamente, alerta de Actions habilitado pelo operador | Ausência de cópia fresca ou ciclo de recuperação falho → incidente |

As rotinas não concedem autorização para coleta, atualização de corpus ou promoção da branch de validação.

## Implementação no PR

- scripts/mar_p0_offsite_s3.py: valida Object Lock COMPLIANCE 90 dias, versionamento, os quatro bloqueios de acesso público e criptografia de repouso SSE-S3/SSE-KMS. Só transmite o envelope cifrado MAR P0; exige SHA-256, cria chave única com upload condicional, exige VersionId. Na recuperação verifica VersionId, Object Lock e hash antes de gravar em diretório privado.
- scripts/mar_p0_install_pg18_ci.sh: instalação assinada PGDG do PostgreSQL 18 no Ubuntu 26.04, conforme a execução real previamente aprovada.
- .github/workflows/mar-p0-durable-backup.yml: cron 17 3 * * *, executa export/arquivo S3 em runner A e restaura em runner B. Fixa repositório e branch main. Nunca grava em Neon.
- .github/workflows/mar-p0-weekly-recovery.yml: cron 17 6 * * 0, seleciona uma versão de 24–192h diretamente no S3 e a restaura sem depender dos outputs do backup diário.
- tests/test_mar_p0_offsite_s3.py: testes offline contra permissões incorretas, bucket público, versionamento desativado, hash adulterado, retenção insuficiente, overwrite, seleção de versão fora do período e recuperação.

## Provisionamento externo necessário (NÃO executado)

Não existe autorização de acesso a uma conta AWS por meio dos conectores disponíveis. O responsável deve provisionar o backend e seus controles antes de qualquer execução operacional.

1. Criar bucket S3 privado, fora do projeto Neon, com **Versioning Enabled**, **Object Lock Enabled**, **Default Retention COMPLIANCE 90 days**, Block Public Access nos quatro itens, Default encryption SSE-S3 (AES256) ou SSE-KMS, e política de bucket que negue tráfego HTTP sem TLS. A funcionalidade COMPLIANCE impede exclusão antecipada até por administradores; confirmar previamente a política e os custos de retenção.
2. Configurar provedor AWS IAM OIDC para token.actions.githubusercontent.com, audiência sts.amazonaws.com, duas roles distintas. Usar trust policy com audience e subject exatos de cada environment, sem wildcard aberto. Para repositórios com subject imutável de 2026, conferir o valor efetivo da claim; a configuração pode incluir IDs do repo/org.
3. Permissões mínimas: ambas roles precisam ler o status de Versioning, Object Lock, Block Public Access e default encryption do bucket. Upload precisa de s3:PutObject e s3:PutObjectRetention **somente** em arn:aws:s3:::BUCKET/mar-p0/validation/*. Recovery precisa de s3:ListBucketVersions no bucket (restrição de prefixo), s3:GetObjectVersion, s3:GetObjectRetention e leitura HEAD/GET de versões **somente** no prefixo. Nenhuma das duas roles recebe s3:Delete*, s3:BypassGovernanceRetention ou permissão para modificar a política de bucket. Se usar KMS, limitar GenerateDataKey ao export e Decrypt ao restore.
4. Criar Environment no GitHub **mar-p0-backup-automation** com acesso a **main somente** e sem aprovação manual por cron. Environment secrets: MAR_P0_READONLY_DATABASE_URL (Neon Direct, role SELECT) e MAR_P0_RESTORE_AES_KEY_HEX (chave AES de 32 bytes). Environment variables: MAR_P0_S3_BUCKET, MAR_P0_S3_REGION, MAR_P0_AWS_UPLOAD_ROLE_ARN.
5. Criar Environment **mar-p0-restore-automation**, também **main somente**. Environment secret: MAR_P0_RESTORE_AES_KEY_HEX (mesma chave). Environment variables: MAR_P0_S3_BUCKET, MAR_P0_S3_REGION, MAR_P0_AWS_RESTORE_ROLE_ARN. **Não** cadastrar URI do Neon neste environment.
6. Custodiar a chave AES num cofre separado da AWS e dos artefatos, por no mínimo o prazo de retenção + janela de recuperação. Testar recuperação da chave; planejar rotação com várias chaves antes de revogar a anterior. Nenhum segredo deve ser colado em chats, issues, commits ou logs.
7. Revisar o PR, permissões, ambiente e custos; somente então aprovar eventual merge na main. Fazer primeiro workflow_dispatch de forma manual, conferir upload imutável e restauração diária; em outro momento testar versão com 24+ horas na recuperação semanal. Agendamentos GitHub podem atrasar e não estabelecem SLA de RTO.

**Proteção GitHub:** os environments automáticos não devem permitir jobs de PR nem outros branches; restringir deployment branches a main, confiar no GitHub OIDC com subject exato e usar tokens temporários de AWS. O environment manual mar-p0-neon-isolated e sua aprovação por revisor permanecem separados.

## Aceitação e critérios de saída

R01: bucket sem proteção / role excessiva → bloqueado antes de upload.
R02: ciphertext adulterado ou não criptografado → recusado.
R03: upload real confirma VersionId, SHA-256 e COMPLIANCE >=90 dias.
R04: runner independente faz download de versão pinada e compara hashes de todas as linhas, esquema e integridade.
R05: restauração semanal recupera uma versão com pelo menos 24 h, sem consultar Neon.
R06: AWS/IAM nega escrita com role recovery e leitura/exclusão com role de upload, por testes não destrutivos.
R07: custódia externa da chave comprovada; alertas de falha monitorados.

**Gates:** P0_OFFSITE_RECOVERY_PROOF = PASS (ensaio pontual, 13/11/2026). P0_OPERATIONAL_BACKUP = HOLD até bucket real, IAM, environments e exercícios operacionais validarem-se. Aprovar backup operacional não autoriza outros fluxos de coleta.
