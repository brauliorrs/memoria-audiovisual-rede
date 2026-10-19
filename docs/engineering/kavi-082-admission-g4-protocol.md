# MAR — KAVI/Kuvi nº 82: contrato G4 de admissibilidade científica

**Versão:** 1.0 · **Data:** 2026-10-19 · **Unidade:** `fiaf-kavi`.  
**Estado:** HOLD provisório, não há incorporação de corpus nem coleta de mídia.  
**Referências:** [protocolo G0–G4](public-access-first-protocol.md), [G3 e licença](kavi-082-legitimate-discovery-indexing-g3.md), [prova de uma página](kavi-082-one-page-preflight-runbook.md), [método científico MAR](../methodology/mar-scientific-methodology.md).

## 1. Unidade científica delimitada

O candidato **não** é o conjunto de filmes preservados por KAVI/Kuvi: é o **subconjunto de registros de vídeo fornecidos pelo provedor de metadados** na API Finna, com `building:"0/KAVI/"` × `format:"0/Video/"`. A contagem de **138.393** observada em 19/10/2026 é total declarado naquele momento para o filtro, **não** total de filmes disponíveis para assistir, custodiais ou licenciados. A primeira página contém 200 registros classificados por **prefixo de ID** como `film_id_candidates`; isso não equivale a 200 obras validadas curatorialmente.

Diferenciar sempre: **provedor indexador**, **custodiante do objeto**, **titular de direitos**, **serviço onde o usuário descobre o título**, **página de exibição na origem**. A entidade institucional Kuvi (ex-KAVI) não é automaticamente titular/custodiante de cada filme indexado. Elonet, Elävä muisti e Elokuvapolku podem partilhar identificadores. A mesma obra tem uma unidade canônica e **múltiplas rotas de descoberta**, não três registros de filme.

É admissível estudar metadados de uma obra com direitos de mídia não confirmados **desde que o estado individual esteja explícito**, o uso fique no escopo CC0 da API e a reprodução continue exclusivamente na instituição de origem. **Não se exige licença para redistribuir mídia porque o MAR não redistribui mídia**. Não converter disponibilidade do player em permissão para baixar, copiar, hospedar, incorporar ou espelhar.

## 2. Quatro gates independentes que faltam

| Gate | Prova exigida para G4 | Evidência real em 19/10/2026 | Situação |
|---|---|---|---|
| **Cobertura** | Universos e filtros congelados; contagem, paginação terminal, zero lacunas/duplicidades, hashes/replay, estabilidade ou mecanismo de reconciliação da fonte. Definir se a observação corresponde ao `api_exposed_subset` e não ao site inteiro | 200 IDs distintos em uma página; `expected_total=138393`; `offline_integrity_verified=true`, `api_snapshot_freshness_verified=false`; cursor terminal não atingido | **HOLD** |
| **Semântica audiovisual** | Plano de amostragem antes da curadoria, estratos de filme longo/curta/outros vídeos, revisão independente de conteúdo e incertezas; não confiar apenas no prefixo `kavi.elonet_elokuva_` | 200 candidatos por prefixo; **0 fichas classificadas por revisão humana independente nesta rodada** | **HOLD** |
| **Proveniência/custódia** | Registro por item de provedor, identificador original, referência à fonte, responsável/custodiante **ou `unknown/not_established` explícito**, e evidência de deduplicação entre serviços; preservar link da página real, não adivinhar URL | Provedor de metadados e escopo identificados; **0 registros com custódia estabelecida**; cobertura de rotulagem individual não auditada | **HOLD** |
| **Direitos/acesso** | Somente metadados realmente distribuídos pela API sob CC0, rotular separadamente `media_rights`, `access`, `link_out` por item; casos sem direitos conhecidos podem usar `unknown` mas **não podem virar `public_domain`** por padrão | Termos CC0 demonstrados; vídeo de ficha Elonet assistido conforme testemunho do usuário; **0 registros com direitos de mídia verificados no lote** | **HOLD** |

**Atenção:** os valores "0" de direitos e custódia se referem à ausência de verificação no ensaio, **não** à inexistência de direitos ou de preservação. Uma ficha com `custody=unknown` continua elegível como **metadado de catálogo** numa política adequada, nunca como patrimônio necessariamente custodiado por Kuvi.

## 3. Implementação fail-closed (sem executar API)

- Dossiê audível: [`kavi-082-admission-evidence.json`](kavi-082-admission-evidence.json), preenchido só com os valores observados na execução [GitHub Actions #39290009804](https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39290009804) e respectivos hashes. Evidências não obtidas ficam com valores nulos/zero, **nunca preenchidos por suposição**.
- Validador offline: `scripts/validate_kavi_082_admission.py`. Inspeciona formato, escopo, licença de metadados, política link-only, hashes, total, integridade, paginação, categorias, rotulagem individual declarada, revisões independentes e links públicos de prova. Rejeita ativação de corpus e nunca emite `admitted` ou `promotion_authorized=true`.
- Saídas: `REJECT_INVALID_EVIDENCE` para estrutura/provas inconsistentes (exit 2); `HOLD_PROVISIONAL` para investigação incompleta (exit 0); ou `READY_FOR_HUMAN_ADJUDICATION` somente quando os **requisitos formais** do contrato estiverem satisfeitos (exit 0). **Ready não é admissão.**
- **Limite deliberado:** o validador não faz HTTP, não verifica conteúdo de um link nem autentica que uma declaração de revisão humana ocorreu de fato. Um dossiê sintético coerente pode retornar `READY_FOR_HUMAN_ADJUDICATION` em teste, mas isso **não é evidência científica**. Revisores devem inspecionar documentos, amostra congelada e proveniência **fora deste script**; a promoção requer outra decisão formal humana no protocolo de inclusão.
- **Proteção:** SHA de IDs e de escopo ajuda a detectar discrepâncias entre versões; hash sozinho não prova cobertura, propriedade ou direitos. Dados brutos e `resumptionToken` não são publicados em Git; tokens de recomeço não podem ser inferidos de digest.

**Reprodução offline:**

```bash
python scripts/validate_kavi_082_admission.py \
  docs/engineering/kavi-082-admission-evidence.json
# HOLD_PROVISIONAL, promotion_authorized=false
python -m unittest discover -s tests -p 'test_kavi_082_admission.py' -v
```

## 4. Gate de futura admissão (revisão humana real)

1. **Decidir o recorte:** o corpus será um espelho metodológico **de metadados Finna** (não acervo custodiado) com universo `api_exposed_subset`, ou uma amostra declarada de observação? Se parcial, somente um **protocolo científico específico para amostra** pode autorizar essa classe de inclusão, sem denominar o subset como completo.
2. **Planejar e congelar amostra curatorial** estratificada para classificação audiovisual, múltiplos serviços e registros não fílmicos. Determinar taxonomia, critérios de seleção, quem revisa, conflito de julgamentos, estado `não avaliável` e estatísticas descritivas antes da anotação.
3. **Registrar proveniência e direitos de metadados por registro**: provedor e ID, custódia conhecida/desconhecida, meio de descoberta, direitos/estado de acesso conhecidos/desconhecidos, permissões limitadas ao metadado, link canônico **verificado** para o portal custodial/de origem. O esquema futuro deve separar links a ficha dos URLs de mídia para jamais oferecer playback pelo MAR.
4. **Somente após isso**, avaliar em documento autônomo a viabilidade de enumeração completa (tokens, validade de janela, taxa de chamadas, volatilidade do total, exclusões, snapshots, tombstones, cutoff e recuperação). **Não iniciar job massivo** com base no sucesso de uma página.
5. **Auditoria independente dupla** verifica integridade material, descrição da população, anotação/erros, direitos e classificação. O G4 mecânico pode então informar `READY_FOR_HUMAN_ADJUDICATION`, sem executar qualquer promoção.
6. **Autoridade curatorial** decide formalmente a inclusão na camada de corpus adequado, define versionamento, snapshots e indicadores admissíveis. Até então: `hold_provisional`, `corpus_activation=false`, dados restritos ao staging e nenhuma mídia.

## 5. Decisão desta entrega

O gate G3 de uma página está concluído e **não será repetido como atividade de rotina**. A análise nº 82 continua aberta, o PR #71 antigo permanece Draft, e o próximo número da fila não é iniciado implicitamente. Este incremento entrega **contratos e testes G4**, não autorização para coleta total ou incorporação de qualquer registro ao MAR.
