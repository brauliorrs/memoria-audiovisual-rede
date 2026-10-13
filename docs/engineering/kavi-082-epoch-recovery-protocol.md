# KAVI nº 82 — isolamento e recuperação controlada por epoch

**Status:** incremento de infraestrutura **offline**, dependente de revisão e CI.
**Escopo:** `building:"0/KAVI/"` + `format:"0/Video/"`, somente metadados.
**Antecedentes:** issue #59; PR #65 (comparação UTC/Helsinki em Draft); PR #64 (auditoria e continuidade). O fuso do campo `expires` ainda não foi oficialmente confirmado.

## Decisão

A validade do token é determinada **pelo servidor Finna**, não pelo relógio de quem faz a requisição. Comparar UTC e `Europe/Helsinki` é diagnóstico; **não** cria duas novas oportunidades HTTP para o mesmo token.

Quando, e somente quando, houver uma **expiração comprovada do token no protocolo do servidor**, após verificação independente de resposta, contrato oficial e autorização humana, pode-se preparar **uma única nova execução isolada** do recorte KAVI/Finna. O epoch anterior não é apagado, copiado nem misturado ao sucessor.

Este PR implementa **apenas a preparação e o bloqueio local**; não existe hoje um classificador de expiração confirmada no adaptador Finna, nem aprovação para reinício automático.

## Recursos implementados

`scripts/kavi_finna_epoch_recovery.py`:

1. `initialize_epoch_workspace(root, evidence_sha256=...)`: cria `epochs/epoch-0001` e um controlador local com `restart_count=0`. Rejeita diretórios preexistentes e nenhum HTTP é iniciado. O operador pode passar `epochs/epoch-0001` à rotina já existente `run_kavi_finna_metadata_staging.py` em uma coleta **explicitamente autorizada**.
2. `restart_after_confirmed_expiry(...)`: exige motivo literal `provider_confirmed_token_expired`, confirmação humana, SHA-256 da evidência da resposta da API e do contrato oficial e uma contagem independente capturada no preflight anterior. Todos são dados que o **operador precisa verificar fora do checkpoint**; mero `expires` local, HTTP 400/429/500, erro de transporte e deriva de total **não** atendem ao gate.
3. Antes de preparar sucessor, reexecuta a auditoria offline aprovada, verifica SHA do checkpoint também sob `FileWriteLock` e cria marcador de congelamento no epoch antigo com somente hashes, totais e flags conservadoras. `stage_metadata` agora testa o marcador dentro de seu próprio lock e rejeita esse epoch **antes** de preflight/requisições HTTP.
4. Somente após congelar o anterior cria `epochs/epoch-0002` vazio e atualiza o controlador. O novo epoch começa sem cursor e sem registros; só a execução explicitamente autorizada pelo operador pode iniciar uma nova enumeração.
5. Tentativa posterior de preparar `epoch-0003` é rejeitada por `epoch_restart_budget_exhausted`. Não há loop, retries ou auto-restart.
6. `inspect_epoch_workspace` devolve apenas resumo de estados e limites, sem tokens, IDs ou brutos.

## Garantias e limites importantes

- **Conservação:** sem download de mídia, sem publicação, sem promoção ao corpus, sem migração de registros entre epochs.
- **Proteção cooperativa:** o marcador de congelamento e a verificação na rotina compartilhada impedem que dois escritores compatíveis continuem a execução encerrada. Não é um esquema contra manipulação maliciosa dos arquivos locais.
- **Falha de energia/crash:** se houver interrupção entre o marcador, a criação do diretório e a gravação do controlador, a execução pode ficar **bloqueada**, exigindo reconciliação manual. Não remover o marcador ou editar arquivos diretamente para forçar retomada.
- **Autorização:** SHA-256 de evidência e confirmação humana não equivalem a assinatura digital nem autenticam automaticamente a resposta do fornecedor. A responsabilidade de verificar a documentação da API e a resposta original permanece explícita. O classificador de expiração do servidor ainda precisa ser implementado e revisado em PR separado.
- **Escala:** reiniciar um lote de 138 mil registros pode ser inviável se o índice variar ou tokens expirarem rapidamente. Não interpretar um epoch iniciado como catálogo completo. Verificar, numa fase posterior, uma estratégia particionada demonstravelmente exaustiva e com deduplicação/proveniência.
- **Escopo:** não mudar o staging de outros corpora, além de uma guarda genérica para diretórios que contêm o marcador de epoch abortado. Os demais produtores não criam esse marcador.

## Demonstração sem rede

```python
from scripts.kavi_finna_epoch_recovery import (
    initialize_epoch_workspace, inspect_epoch_workspace,
)

initialize_epoch_workspace(
    "data/staging/kavi-finna-epochs",
    evidence_sha256="SHA256_DO_ESCOPO_PUBLICO_VERIFICADO",
)
# O diretório epochs/epoch-0001 está pronto, ainda sem páginas.
# Não há chamada à API nem autorização implícita para coletar.
```

A função `restart_after_confirmed_expiry` foi projetada para um futuro operador ou orquestrador que consiga atestar a **mensagem oficial de expiração**. Não criar prova fictícia de servidor para executar produção: os hashes dos testes são deliberadamente sintéticos.

## Critérios para integração

- Quality Checks/pytest ou unittest verde, revisão Codex sem P1/P2.
- Testes: diretório pré-existente, reexecução sem rede, checkpoint parcial/completo, escopo divergente, total divergente, operador não autorizado, erros que não comprovam expiração, dois epochs isolados, tentativa de continuar epoch encerrado, controle de restart único, inconsistência no controlador, diretório sucessor preexistente.
- **NÃO** executar a sonda viva do PR #65; não promover o corpus; manter issue #59/nº82 aberta e nº83 bloqueada.

## Próximo passo técnico

Investigar a forma exata com que a API Finna sinaliza **token expirado**, de modo verificável e sem confundi-lo com 429, 5xx ou timeout. Implementar classificador isolado e testes de contrato; somente então autorizar uma única sonda de validação de retomada com a política de um restart controlado. Resolver também a política de fuso do `expires` sem suposição indevida.
