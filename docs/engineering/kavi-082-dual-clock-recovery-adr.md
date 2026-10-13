# ADR KAVI-082 — decisão técnica proposta: relógios alternativos e recuperação controlada

**Data:** 2026-10-13. **Estado:** PROPOSTA; a política de retomada em produção NÃO foi alterada.  
Referências: issue #59, PR #65 em Draft, documentação de Finna `resumptionToken`, [Finna API (English)](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish).

## Análise crítica da proposta

O pedido é calcular a validade da data `resumptionToken.expires` considerando UTC e horário local, e reiniciar a coleta que apresentar token expirado. **A comparação de dois relógios é útil como hipótese; duas chamadas repetidas com o mesmo token, trocando apenas o fuso do relógio do cliente, não são úteis.** O servidor determina a validade do token; o cliente não pode alterar essa validade ao interpretar `expires`.

Para `horário local`, explicitar **Europe/Helsinki**, não fuso da execução (UTC ou Fortaleza). O horário finlandês alterna UTC+2 / UTC+3 e há intervalos inexistentes e repetidos na mudança de horário de verão. Nenhuma dessas hipóteses é prova de que o servidor Finna as usa: é possível que utilize outro fuso. Enquanto a documentação oficial não confirmar, registrar `timezone_authority=unconfirmed`.

## Política operacional recomendada

1. **Avaliação local sem rede:** calcular uma hipótese UTC e uma hipótese `Europe/Helsinki`, inclusive DST, a partir de `expires` sem fuso. Resultado possível: `both_future`, `both_past`, `disagreement`, `helsinki_nonexistent_time`, `helsinki_dst_fold_ambiguous`. Valores com offset explícito continuam a seguir o contrato já implementado.
2. **Apenas UMA chamada de continuação por token:** após replay do checkpoint, integridade de SHA, preflight, verificação de cursor sob lock, ritmo de requisições e restrições robots, a autorização eventual para pedir próxima página deve ser ancorada em política explícita de aceitação do servidor — **não em adivinhar qual relógio é oficial**. O código de produção continua conservador enquanto não for construída e revisada essa exceção.
3. **Distinguir resultados do servidor:** continuação bem-sucedida + incremento monotônico dos IDs apenas autoriza persistir a página ainda não promovida; token declarado inválido/expirado pela API requer classificação inequívoca (endpoint e resposta efetiva a documentar); falhas 429, 5xx, rede, parsing, timeouts, deriva do total ou robots não são prova de expiração e nunca autorizam reset.
4. **Em expiração comprovada:** a sequência corrente vira `ABORTED_EXPIRED_TOKEN` preservando hashes, auditorias e proveniência. Um *novo epoch de coleta* pode iniciar por `resumptionToken=*` sob um **novo diretório isolado**, mesmo escopo e autorização, nunca anexando a páginas do epoch anterior. O primeiro preflight da nova execução fixa um novo total externo; esta execução fica marcada separadamente e sujeita a auditoria.
5. **Orçamento de reinício:** limite inicial proposto de **uma nova tentativa por escopo**, com backoff e observabilidade; caso repita a expiração, `HOLD` e intervenção humana. Não iniciar loops infinitos ou recaptura de um catálogo inteiro. Separar `KAVI/Finna` dos demais coletores e do corpus MAR.
6. **Completude:** só reconhecer um epoch como finalizado se token terminal, contagem, IDs únicos, reexecução da auditoria, rastreabilidade e direitos conservadores forem consistentes. Reiniciar do zero pode resultar em conjunto diferente quando o índice muda; por isso comparar hashes/totais entre epochs e preservar origem/versão.
7. **Escala:** a documentação Finna menciona limite de 100.000 para paginação tradicional, uso de tokens para conjuntos extensos e possibilidade de recortes por `last_indexed`. Investigar particionamento estável, comprovadamente exaustivo e sem sobreposição antes de reiniciar repetidamente aproximadamente 138 mil resultados. Não presumir que `last_indexed` cria um snapshot imutável.

## Protótipo de risco zero integrado ao PR #65

`scripts/finna_expiry_hypotheses.py` implementa **somente** o cálculo das hipóteses UTC/Helsinki, sem conexão HTTP, token, checkpoint ou promoção. `tests/test_finna_expiry_hypotheses.py` verifica as cinco classificações, DST de verão/inverno e intervalos duplicados/inexistentes. O CI roda essa validação offline permanentemente. O runtime `scripts/kavi_finna_batch_gate.py` continua **rejeitando datas naive**: esta ADR não aprova relaxamento implícito.

## Gates para desenvolvimento futuro

- Confirmar semântica da resposta real de token expirado, preferencialmente com referência oficial, sem gerar tokens inválidos por tentativa/brute force.
- Evoluir `before_fetch` para uma única continuação com política revisada; nunca inserir duas chamadas idênticas por mudança de relógio.
- Testes sem rede para cada classe de erro, orçamento máximo de reinício, preservação do epoch antigo, diretório novo, isolamento do escopo, drift de total, idempotência, deduplicação e zero mídia.
- Abrir PR específico para recuperação; Quality Checks, Codex, uma única sonda viva explicitamente delimitada após aprovação metodológica. Manter PR #65 Draft/HOLD e questão #59 aberta até validação operacional.

**Decisão:** concordância parcial com avaliação dupla (como diagnóstico); discordância com tentativas HTTP duplicadas e reinício automático geral.
