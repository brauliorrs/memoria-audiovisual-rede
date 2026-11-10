# MAR — auditoria e correção do ciclo mensal (10/11/2026)

## Evidência e fronteiras

Fonte primária: GitHub Actions **Organismo Mensal** em
[2026-11-01, run #41326600431](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/41326600431).
O ciclo em `main` percorreu 60 corpora, com 52 sucessos e 8 falhas,
terminando com exit code 1. Isso não é um erro de deploy Vercel e não está
relacionado à integração experimental Psycopg/Neon do PR #90.

Os scripts escreveram um manifesto local do ciclo, mas a etapa de upload
do workflow foi pulada após o comando terminar com erro. O registro por
corpus, contendo as oito falhas, não ficou disponível como artefato do run.

## Diagnóstico por fonte, extraído do log

| Corpus | Evidência observada | Tratamento |
| --- | --- | --- |
| APE / Archives Portal Europe | HTTP 403 no PDF oficial `20251215_OnlyInstitutionsWithContent.pdf` | HOLD da fonte. Não contornar controle 403 nem usar fonte não oficial como se fosse APE |
| ASIM / Mallorca | zero fichas audiovisuais retornadas por rota EFG | Revisar acesso público, consulta e parser, com fixture genuína |
| Bundesarchiv | zero registros analíticos da rota EFG | Reavaliar rota de catálogo institucional e suas condições de acesso |
| Bulgarian National Film Archive | zero registros analíticos da rota EFG | Revalidar via catálogo oficial, não inferir itens a partir de páginas gerais |
| CICLIC | zero fichas audiovisuais apesar de rota responder | Investigar paginação/AJAX e atual HTML com testes determinísticos |
| Czech Television / iVysílání | corpus/catalogo analítico vazio | Revisar seletor, paginação e URLs públicos; não usar dados fabricados |
| Eye Filmmuseum | zero de 630 registros esperados na amostragem | Verificar se endpoint de fragmentos mudou; manter discrepância explícita |
| Filmoteca Valenciana | zero de 60 mínimo, antigo domínio `www.restauracionesfilmoteca.com` | Código corrigido para domínio IVC oficial `restauracionsfilmoteca.ivc.gva.es`, com páginas espanholas `/es/archivo/…` e fichas `/es/ficha/…`, sujeito a teste controlado |

A rota institucional nova da Filmoteca Valenciana e seus seis índices
de ficção/não ficção foram confirmados por páginas oficiais do IVC:
https://restauracionsfilmoteca.ivc.gva.es/es/ .
A mera existência da rota não prova que todas as fichas tenham player
público nem que o piso 60 seja atingido. Os testes do PR são offline.

## Alterações mínimas e contratos preservados

1. O workflow passa a preservar `observatorio_ciclo_mensal.json`,
   `observatorio_resultados_ciclos.csv` e
   `observatorio_linha_do_tempo_ciclos.csv` mesmo que o comando de
   coleta falhe, com retenção limitada. Os artefatos completos continuam
   exclusivos de ciclos bem-sucedidos.
2. Cada resultado de corpus passa a identificar
   `failure_stage=collection|validation|snapshot`, sem alterar os
   estados `success`/`failed`, a contagem de falhas ou o código final
   diferente de zero quando necessário. O campo é mantido no manifesto
   e no CSV histórico.
3. A Filmoteca passa a consultar apenas um conjunto fixo de sete índices
   oficiais em espanhol e as fichas deduplicadas por ID Vimeo. Sem
   baixar vídeos, sem player hospedado no MAR. Um índice indisponível
   força `integrity_status=instavel` e
   `collection_complete=false`. O piso de 60 vídeos **não foi
   reduzido** e não se declara restauração concluída sem nova validação.
4. Os demais sete conectores não são classificados como corrigidos:
   permanecem bloqueados individualmente até inspeção de respostas
   atuais, atualização de parser/rota e teste com evidência pública
   legítima. Não desativar a auditoria global nem trocar `failed`
   por `success` para fazer o CI passar.

## Plano de testes e limites

- Testes offline para URLs e deduplicação da Filmoteca, rejeição de
  listagem indisponível, contagem de falhas, estágio de erro e upload
  do manifesto no caso de falha.
- CI normal da branch de correção; **sem invocar** `Organismo Mensal`
  completo, sem baixar mídia, sem conectar à branch principal Neon,
  sem executar migrações de banco.
- Após CI, sonda unitária por instituição com poucas requisições
  públicas e autorização explícita antes de reconstruir todo o corpus.
- A integração PostgreSQL isolada do PR #90 passou em 10/11/2026,
  mas o Gate P0 **permanece HOLD** até backup criptografado em destino
  externo independente e restauração comprovada. O ciclo mensal não
  pode usar esse armazenamento experimental automaticamente.

## Gate de saída para cada uma das oito falhas

Uma fonte só volta a `success` após evidências recentes de acesso
permitido, extração válida, contagem coerente, links/proveniência
preservados e aprovação do verificador de corpus, sem ampliar a coleta
sem autorização.
