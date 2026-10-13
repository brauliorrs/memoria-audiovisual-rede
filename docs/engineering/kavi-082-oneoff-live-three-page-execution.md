# KAVI #82 — execução única e limitada, 13/10/2026

## Protocolo do ensaio real

Objetivo: validar apenas **uma página inicial + duas páginas consecutivas via resumptionToken** de metadados da API Finna, para os filtros previamente auditados `building:"0/KAVI/"` e `format:"0/Video/"`. É o mesmo executor do PR #69, com no máximo **três páginas** e **uma página por chamada de staging**; não inicia coleta integral nem baixa mídias.

Esta é uma execução **única** em GitHub Actions: um job adicional no workflow **já existente** `.github/workflows/quality.yml` só responde a `pull_request.opened`, apenas para a branch `corpus/kavi-082-live-proof-fresh-once-20261013`, PR originado no próprio repositório e destinado à `main`; depende da aprovação do job Quality Checks. Não há gatilho de `push`, `synchronize`, cron ou outra branch para essa sonda. Se o workflow falhar, manter HOLD e **não repetir automaticamente**. A tentativa anterior na PR #70 não executou coleta por falha de configuração do workflow antes da inicialização de qualquer job.

A rotina verifica robots, origem HTTPS permitida, preflight de facetas, contagem total externa inicial, integridade de cada checkpoint, SHA de cada resposta bruta, cursor de origem, bloqueio cooperativo por lock e não duplicação de IDs. Se `expires` não contiver fuso, o servidor é consultado uma única vez por cursor opaco; a resposta exata `Invalid or expired token` é ambígua e deve produzir HOLD, nunca restart.

## Persistência segura de evidências

O repositório é **público**: não publicar checkpoint bruto, `resumptionToken`, IDs individuais ou páginas JSON na branch, comentários, logs ou artefatos plaintext. O diretório `$RUNNER_TEMP/kavi-082-three-batch-checkpoint` permanece durante as três invocações. Ao final, inclusive em HOLD, é empacotado e criptografado com **X25519 ephemeral + HKDF-SHA256 + AES-256-GCM** usando uma chave pública exclusiva desta execução.

A chave privada de descriptografia é guardada **fora do repositório GitHub** pelo responsável pela investigação, jamais passada ao runner. Só saem da máquina virtual dois artefatos de GitHub Actions com retenção de até 90 dias:

1. `kavi082-oneoff-encrypted-checkpoint`: arquivo `kavi082-checkpoint-encrypted.json`, cifrado, contendo os checkpoints e as páginas originais; não pode ser lido sem a chave privada que permanece fora do GitHub.
2. `kavi082-oneoff-redacted-report`: apenas status, contagens, hashes, classificações agregadas e flags negativas.

**Não confundir persistência criptografada do artefato com persistência do filesystem do GitHub runner entre execuções**. Depois de executado, o runner é destruído, mas o arquivo cifrado pode ser recuperado para auditoria offline enquanto estiver retido, desde que a chave privada também seja preservada. Verificar hash SHA-256 da cópia do artefato antes de descriptografar e nunca incluir a chave privada em PR ou comentário público.

## Adjudicação

- **VALIDAÇÃO LIMITADA:** página inicial mais duas continuações, contagens crescentes, preflight inicial e reconferências consistentes, hashes/cursor válidos, auditoria offline true, sem mídia e sem promoção.
- **HOLD:** rejeição ambígua de token, drift de `resultCount`, bloqueio robots, falha de transporte, período de validade explicitamente vencido, exceção, corrupção, duplicata ou diferença entre o total externo e as páginas.
- Em sucesso, a amostra de três páginas **não** prova capacidade de percorrer todo o catálogo (~138 mil registros), de manter snapshot imutável ou comprovação de custódia institucional/direitos.
- **Nunca reiniciar epoch automaticamente.** Issue #59 / nº82 continua aberta; nº83 não começa.

Este workflow é **one-off experimental**; a PR que contém o workflow não deve ser integrada à `main` como agendamento permanente. Registrar os resultados na issue #59 e encerrar a PR depois do ensaio.
