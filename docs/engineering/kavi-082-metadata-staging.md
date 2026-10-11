# KAVI nº 82 — coletor staged de metadados Finna/Elonet

## Decisão arquitetural

O desenvolvimento **não cria um segundo pipeline MAR**. Há um adaptador novo para a API Finna e uma camada estreita, reutilizável, de **staging local de metadados**. São reutilizados, sem cópia de código, os componentes:

- `digital_infrastructure.raw_artifacts.RawArtifactStore`: preservação imutável, content-addressed e verificada por SHA-256;
- `digital_infrastructure.locking.FileWriteLock`: serialização de gravações;
- o pipeline de corpus `pipeline._run_corpus_pipeline` permanece **intocado**; seu uso exige aprovação de um gate posterior de inclusão.

A integração direta com `IngestionCoordinator` / `BatchManifestStore` foi **deliberadamente rejeitada neste estágio**: eles materializam entidades do contrato de infraestrutura digital, com `commit` e `AdaptedRecord`, enquanto fichas de filmes precisam de outro esquema e não podem ser publicadas antes de validação curatorial. A extração dessas funções comuns para um pacote compartilhado independente pode ser feita em refactor futuro, preservando compatibilidade.

## Evidência e escopo pré-registrados

- Issue #59; sonda PR #60 integrada à main; documentação inicial `docs/engineering/kavi-082-probe.md`.
- Fonte `https://api.finna.fi/v1/search`, API e documentação oficiais.
- Filtro institucional `building:"0/KAVI/"`, observado ao vivo sob nome de Kuvi / Taide- ja kulttuurivirasto.
- Filtro audiovisual `format:"0/Video/"`, também observado em respostas reais.
- Contagem de referência observada: **138.377 registros de vídeo no índice**, NÃO número de filmes sob custódia ou vídeos licenciados. O número é **dinâmico**: o preflight de cada execução reavalia a contagem e bloqueia a retomada caso haja mudança.
- Fingerprint de evidência: SHA-256 do artefato da sonda verificada (passado explicitamente por argumento). Os códigos de filtro só são aceitos na versão pre-registrada e são reconfirmados nas facetas públicas em cada execução.
- A documentação [Finna API](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish) especifica que `resumptionToken=*` inicia o lote, os tokens seguintes continuam a enumeração, o lote final pode estar vazio e **limit/page/facet[] não devem acompanhar o token**. A chamada inicial preserva apenas os filtros autorizados; as chamadas posteriores usam somente o token emitido pela API.
- Metadados Finna têm regime próprio (CC0, conforme termos), mas **nenhum direito de mídia é inferido** de `onlineUrls`.

## Contrato de staging

1. **Preflight fail-closed**, consultando `robots.txt` para cada URL pelo guard já existente, faceta `building`, faceta `format`, filtro composto `limit=0` e contagem exata. Se há mudança de rótulo/código ou facetas ambíguas, abortar.
2. **Paginação opaca com resumptionToken**, sem fabricar IDs; primeiras URLs documentadas e continuação estritamente com token emitido pela API. Status HTTP, MIME, JSON, ID e título são verificados.
3. **Integridade forte**: total estável, IDs distintos dentro e entre páginas, detecção de ciclo/repetição de token, nenhuma página intermediária vazia, término apenas quando contagem deduplicada = total do preflight.
4. **Artefatos imutáveis** em `data/staging/kavi-finna/raw/` via `RawArtifactStore`. Checkpoint local com hash do escopo, hash de cada lote, contagem, hash de IDs e da cadeia de tokens. Retomada exige `--resume`, revalida **todos** os artefatos e detecta qualquer mudança de hash, contagem ou escopo.
5. **Nenhuma publicação**: resumo do staging não inclui tokens; checkpoint e brutos ficam fora do Git. A presença de `onlineUrls` é registrada apenas como indicador booleano na normalização. `custody_status=not_established` e `media_rights_status=not_verified`; nenhuma imagem ou vídeo é obtido. `promotion_authorized=false` mesmo após término integral da paginação.
6. **Limites**: execução real somente com `--execute`, no máximo 25 páginas por execução, padrão **1 página**. Nenhum job do CI executa coleta em lote contra a Finna. Testes usam fontes sintéticas, incluindo interrupção/reinício e corrupção de arquivos.

## Reproduzir

```bash
python -m unittest discover -s tests -p 'test_metadata_staging.py' -v
python -m unittest discover -s tests -p 'test_kavi_finna_adapter.py' -v

# Exibe a configuração, sem acessar rede:
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 <SHA256_DA_EVIDENCIA_APROVADA>

# Para uma execução explicitamente autorizada, limitada a uma página:
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 <SHA256_DA_EVIDENCIA_APROVADA> --execute --max-pages 1

# Continuação local explícita; os artefatos anteriores são relidos e verificados:
python scripts/run_kavi_finna_metadata_staging.py \
  --evidence-sha256 <MESMO_SHA256> --execute --max-pages 1 --resume
```

## Gates pendentes para incorporar KAVI

- Confirmar em execução viva **bounded** o contrato concreto de `resumptionToken` e, se necessário, ajustar o parser com evidências; não presumir que testes simulados já provaram enumeração real.
- Completar a enumeração por lotes com zero páginas ausentes, zero duplicidade, total compatível e fingerprints preservados.
- Auditar estratos reais de fichas para separar filme, conteúdo televisivo, material diverso, catalogação bibliográfica e custódia de acervo.
- Comprovar proveniência e regimes de direitos por registro, evitando converter disponibilidade em licença.
- Fazer revisão humana e **aprovação explícita de incorporação**. Só então construir o mapeamento para o pipeline MAR e liberar os indicadores oficiais. A análise #82 continua aberta; #83 não foi iniciada.
