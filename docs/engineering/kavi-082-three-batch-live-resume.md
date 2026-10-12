# KAVI — análise nº 82: prova viva de três retomadas limitadas

## Objetivo

Este ensaio é posterior aos merges dos PRs #61–#64. Ele verifica a mesma rotina auditada `execute_verified_batch` em **três invocações separadas**, cada uma limitada a **uma única página de metadados Finna**, no mesmo diretório local temporário. A primeira abre a enumeração e as outras duas retomam o checkpoint. O propósito é testar a continuidade real, o preflight repetido, os hashes de artefatos, a expiração de cursores e a integridade da cadeia, sem alterar o corpus MAR.

O endpoint e filtros são exatamente os já verificados e autorizados na issue #59: `api.finna.fi/v1/search`, `building:"0/KAVI/"`, `format:"0/Video/"`, `resumptionToken` oficial; continuação passa apenas o token. O fato de a API emitir `token` e `expires` está documentado pela Finna: https://www.kiwi.fi/spaces/Finna/pages/51842373/Finnan%2Bavoin%2Brajapinta%2BFinna%2BAPI

## Execução limitada e redigida

- Com `--execute`, o job faz no máximo **3 chamadas para páginas** (1 inicial + 2 continuações), cada página sujeita à resposta do servidor (anteriormente cerca de 200 registros). Cada uma tem preflight robots, facetas e contagem; não presumir contagem constante sem verificá-la.
- O total do primeiro preflight é mantido externamente ao checkpoint, em memória, e fornecido nas duas retomadas. Se houver deriva no total, interrupção da API, token não verificável, prazo expirado, IDs duplicados, mismatch de proveniência ou hash inválido, emitir **HOLD** e abortar sem tentar reiniciar ou pular IDs.
- O executor audita todos os artefatos brutos a cada retomada e depois de cada lote. A verificação imediatamente anterior a cada uso do token ocorre sob `FileWriteLock`. Intervalo mínimo de 1 segundo nas retomadas.
- `TemporaryDirectory` conserva o checkpoint **entre as três invocações dentro do mesmo job** e é descartado ao final. Portanto, este teste **não demonstra persistência entre runners, máquinas ou dias distintos**.
- A saída pública inclui apenas contagens, estados parciais, SHA-256 da sequência, classificações agregadas e flags negativas. Nunca exportar IDs originais, cursores, páginas JSON completas ou URLs de mídia. O workflow faz upload **apenas do resumo público**, mesmo se houver HOLD.
- Nenhuma mídia é baixada; `promotion_authorized=false`, `media_downloaded=false`. Nenhum registro é incorporado ao MAR. Um sucesso **não** demonstra enumeração completa, snapshot imutável ou custódia/licença confirmada.

## Gate de CI

A suíte offline roda com toda PR da `main`. O teste **vivo** só roda em PR cuja branch seja exatamente `corpus/kavi-finna-three-batch-resume-v1`; não existe agenda, repetição automática ou full harvest. Em caso de HOLD real, o CI falha fechado, e o código não deve ser alterado para desativar gates apenas para tornar o teste verde.

## Critérios de adjudicação

**VALIDAÇÃO LIMITADA:** três páginas, incremento estrito de contagem, total e escopo constantes, integridade offline íntegra, expiração e direitos conservadores, CI verde e revisão concluída sem P1/P2.

**HOLD:** qualquer diferença, expiração, erro HTTP, bloqueio robots, problema de parsing, conteúdo não verificável, timeout ou nova observação metodológica impeditiva. Preservar apenas relatório público; nenhuma incorporação.

Mesmo que o gate limitado seja positivo, a issue #59 e a análise nº 82 permanecem abertas. Próxima decisão será sobre armazenamento persistente seguro, política de snapshot dinâmico, duração real de tokens e possibilidade de enumeração **sem exigir mudança implícita no catálogo**; não avançar à análise nº 83.

## Reproduzir

```bash
python -m unittest discover -s tests -p 'test_kavi_finna_three_batch_resume.py' -v
python scripts/probe_kavi_finna_three_batch_resume.py \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049

# Somente com autorização explícita para uma consulta pública limitada:
python scripts/probe_kavi_finna_three_batch_resume.py \
  --evidence-sha256 466006cb7a499efff354e7f4425aface044440218bdb9a20a1550a3fe079e049 \
  --execute
```
