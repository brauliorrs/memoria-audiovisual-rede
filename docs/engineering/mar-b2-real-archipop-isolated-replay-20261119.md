# MAR B2 — Reprocessamento controlado de um corpus real: ARCHIPOP (19/11/2026)

**Estado:** ensaio de engenharia sobre os dados científicos reais congelados, exclusivamente offline, sem incorporação de novas fontes, coleta, mídia ou publicação de fichas. Branch de revisão: `test/mar-b2-real-archipop-isolated-replay-20261119`.

## Escolha científica fundamentada

O ARCHIPOP integra o roster dos 62 corpora históricos do MAR. Os arquivos versionados `data/output/archipop_*.csv` e `archipop_relatorio.json` contêm uma instituição francesa e dois marcos de medição reais em 29/05/2026:

- **16:48:33 UTC:** 57 links de vídeo e 57 itens no catálogo curatorial.
- **16:52:58 UTC:** 58 links de vídeo e 58 itens no catálogo curatorial.

A projeção atual de ARCHIPOP registra **58** nos nove temas × França e nos nove temas × plataforma ARCHIPOP, **uma instituição**, **58 no histórico do índice de acesso** (ainda `not_authorized_for_new_site`) e **58 títulos na proveniência estatística da nuvem**. O replay não infere licença de republicação a partir dos links de origem.

## Procedimento reproduzível

`python3 scripts/rehearse_mar_archipop_real_b2.py`

1. Executa o **mesmo gerador B2 dos dados reais** para recompor, semanticamente, todas as **34 projeções** atuais de seus arquivos de origem versionados, incluindo o ARCHIPOP. A trilha inicial continua congelada pelo lock científico da `main`.
2. Escreve somente em diretório temporário externo ao repositório via o stage Python já aprovado. Compara o manifesto, `epochSha256` e SHA-256 de todos os 34 JSONs.
3. Confronta 57 → 58 em observações de série temporal com 58 em relatório B1, nove temas × país, nove temas × plataforma, instituição, entradas geográficas utilizadas no mapa, índice humano de acesso e proveniência da nuvem.
4. Preserva as 200 fichas KAVI, decisões de acesso e casos documentados sem recalcular autorizações a partir de dados científicos.
5. Tests de regressão: altera **apenas uma cópia temporária** do CSV real de ARCHIPOP para criar divergência 999 contra 58, comprovando a detecção de alteração de fonte pelo lock; corrompe o arquivo final do pacote temporário para conferir que `atomic_stage_files` rejeita a promoção e mantém a versão íntegra.

`python3 -m unittest discover -s tests -p "test_mar_archipop_real_b2_replay.py" -v`

## Critério de êxito e limitação

Êxito exige paridade dos 34 arquivos com a versão científica atual, histórico real ARCHIPOP 57 → 58 íntegro, todos os totais atuais = 58, 62 corpora, zero mudança de direitos/arquivos de origem, e os cenários adversariais com HOLD e sem substituição parcial. O workflow do site executa tudo antes do build Next.js; o `quality.yml` também descobre a suíte.

**Não alegar um teste de atualização integral entre dois bundles reais de 57 e 58 itens:** o repositório contém o histórico de duas observações, mas só a **projeção completa mais recente de 58 itens**. A versão antiga de todos os arquivos necessários não está versionada separadamente para reproduzir um bundle de 57. Portanto, o ensaio confirma a **reconstrução da versão real atual, a coerência da evolução histórica, a integridade e o rollback**. Uma regeneração integral de dois snapshots reais e posterior incorporação autorizada de novos corpora continuam etapas independentes.

Nenhum merge, nova publicação, novo serviço, alteração de dados científicos reais, Neon ou configuração Vercel é necessário para a execução desta revisão.
