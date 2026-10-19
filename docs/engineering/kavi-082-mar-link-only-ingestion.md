# MAR — KAVI/Kuvi nº 82: integração integral de **fichas e metadados** com links para a origem

**Diretriz da coordenação (2026-10-19):** o objetivo não é somente inventariar se o KAVI tem um catálogo, nem estudar uma amostra permanente de filmes. O MAR deve **integrar progressivamente todo o universo de registros audiovisuais legítimos e alcançáveis**, extraindo seus **parâmetros documentais** e mantendo um **link para a ficha da obra na plataforma de origem**. Não se faz download, hospedagem ou reprodução audiovisual no MAR.

## 1. Corrigir a interpretação do gate anterior

O G4 de [admissibilidade](kavi-082-admission-g4-protocol.md) mantém exigências válidas para **afirmar cobertura integral, certeza de custódia e conclusão científica sobre o universo**. Ele **não** deve ser interpretado como proibição metodológica de **incrementar um índice de metadados parcial, rotulado como parcial**, nem exigir liberação de direitos de reprodução de vídeos para criar fichas com metadados CC0 e endereço da instituição.

**Separar três decisões:**

| Camada | Pode avançar com cobertura parcial? | Condição necessária |
|---|---|---|
| **Staging de metadados autorizados** | Sim | Robots/termos vigentes, API oficial, escopo explícito, integridade, checkpoint e limites |
| **Catálogo MAR de fichas com links** | Sim, **após gate específico de qualidade/publicação por lote**, com status `partial`, fonte, campo e lacunas transparentes | IDs estáveis, páginas efetivamente retornadas, URL de ficha efetivamente fornecida ou comprovada, dados mínimos, licença de metadados e deduplicação |
| **Declaração científica de cobertura integral/custódia/estatísticas globais** | Não | Fecho da enumeração, reconciliar total, possível volatilidade, proveniência e direitos/classificação por obra, revisão acadêmica |

Portanto, a passagem de `PARTIAL` para `COMPLETE` deve atualizar **o grau de cobertura do índice**, sem promover automaticamente classificação do audiovisual, custódia ou autorização de mídia. O número divulgado de **138.393** para a faceta `KAVI × Video` em 19/10/2026 é **universo indexado na API naquele snapshot**, não quantidade real de filmes assistíveis; a API pode retornar deduplicações e excluir registros da interface web. <https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish>.

## 2. Quais parâmetros de uma obra o MAR deve disponibilizar

**Identidade e referência:** `source_record_id`, `source_service`, `metadata_provider`, `source_record_url`, `video_link` e `partner_site` (página humana de origem, jamais MP4/HLS/MPD).

**Descrição:** título, título alternativo se fornecido, data/ano, créditos/autores, sinopse/resumo, temas, gêneros, idiomas, formatos e vínculos a coleção. Campos ausentes ficam desconhecidos; a projeção v1 materializa os campos mapeados presentes nos metadados da API. Não afirmar que o MAR já recebe todos os campos possíveis se eles não tiverem sido requisitados pela API.

**Controle e proveniência:** fonte, data da observação, hash do escopo, integridade da página, status da classificação audiovisual, responsável/custodiante (inclusive `unknown`), licença aplicável ao **metadado** e direitos da **mídia** separados, situação de acesso por obra e completude do lote.

**Distinção de serviços:** Elonet, Elävä muisti, Elokuvapolku e Ritva são **fontes de descoberta** e podem ter catálogos próprios. Preservar relações e contextos curatoriais, não somar todos os links como obras independentes. Deduplicar por ID institucional/provedor e reconciliar entre serviços **somente com equivalências demonstradas**; títulos iguais não bastam.

**Reprodução:** usuário clica no registro externo, que pode exigir confirmação humana; todas as visitas e reproduções permanecem na instituição que detém ou oferece o conteúdo. Links de arquivos de mídia não são usados como URL pública.

## 3. Incremento de engenharia v1: projeção de staged auditado para o esquema MAR

Arquivo `src/memoria_audiovisual/kavi_finna_mar_index.py` + CLI `scripts/project_kavi_finna_mar_index.py`.

- **Não cria coletor novo**. Lê somente o `RawArtifactStore` e checkpoint já existentes, após verificação independente por `audit_finna_staging`, e revalida hashes de cada página, IDs ordenados de origem, escopo e total antes de converter.
- **Transforma** as fichas JSON da API no formato descritivo compatível com as colunas MAR `video_title`, `video_subject`, `video_description`, `video_published_at`, `video_link`, `partner_site`, além de IDs, campos informacionais, direitos e proveniência. Exporta CSV e JSON de **prévia de revisão**, não os arquivos de produção nem um corpus ativo.
- **Não adivinha URL**. Usa o `recordPage` retornado pela API, que a documentação da Finna define como link relativo à ficha em `www.finna.fi`. URL Elonet é preferida **apenas se houver comprovação independente por item e correspondência exata com o ID**. Endereços de `onlineUrls`, `images` e mídia não são exportados. Ausência de `recordPage` produz `missing_source_item_link`, não um link fabricado.
- **Permite cobertura parcial** no objeto de prévia, com `expected_total_api_index`, `record_count`, `coverage_status=partial`, número de links presentes/ausentes e `promotion_authorized=false`.
- **Impede autopromoção**: nenhum novo corpo bruto, mídia, player ou stream é obtido; diretório de prévia não se comunica com o catálogo ativo; não abre conexão de rede. Um gate adicional de publicação está pendente para efetivamente disponibilizar os lotes ao usuário final.

**Uso exclusivamente offline, com staging pré-existente, persistente e auditado:**

```bash
python -m scripts.project_kavi_finna_mar_index \
  --directory /private/kavi-finna-staging \
  --output-directory /private/kavi-mar-review-empty \
  --evidence-sha256 <SHA256_DA_PROVA_VALIDADA> \
  --expected-total <TOTAL_OBSERVADO_NO_PREFLIGHT_DO_STAGING>
```

A execução histórica de 19/10/2026 foi realizada em **diretório temporário descartado pelo CI**: o GitHub preservou apenas resumo redigido e hashes, não os 200 registros. **Não é correto afirmar que 200 fichas foram inseridas no MAR**; a prévia depende de nova coleta autorizada quando houver estratégia persistente de atualização. Não repetir a sonda antiga como se fosse inclusão.

## 4. Etapas concretas restantes para a integração de todo o acervo

1. **Esquema v2 de campos Finna**: conferir defaults e selecionar explicitamente `field[]` necessários (incluindo `recordPage` e descritores) no início do lote, validando que a API permite esses campos com `resumptionToken=*`. Não confiar no nome dos campos nem no prefixo de IDs sem verificar o payload de fonte.
2. **Publicação incremental autorizada**: após contratos por lote e aprovação editorial, promover **somente metadados linkáveis, semanticamente elegíveis e licenciados**, com snapshots e estatística de cobertura; registros não revisados mantêm rótulo próprio e não contribuem para conclusões sobre custódia. Evitar publicação de fichas sem link de origem quando o produto exige acesso à obra.
3. **Enumeração legítima completa de cada serviço**: definir custo por 138 mil IDs, janelas de resumptionToken, checkpoint/replay, regras para token inválido/expirado e mudanças da contagem; **não** iniciar coleta maciça até resolver limite de token, expiração, replay e autorizações atuais.
4. **Atualização contínua e desistências**: observar altas/alterações/remoções, não excluir ficha somente por falha temporária; registrar `last_observed`, `not_found` ou `restricted` com evidência e versionamento de observações.
5. **Elävä muisti / Elokuvapolku / Ritva**: descobertas por serviços distintos, verificação de links para fichas e estratégias próprias de extração onde autorizadas. A API Finna `building=0/KAVI/` pode não cobrir esses serviços inteiros; o plano institucional requer registros de cobertura por subserviço.

**Decisão:** começar a **engenharia real de integração progressiva de metadados com links**, não esperar a completude de todo o arquivo antes de projetar fichas. O PR desta fase **não** publica dados no MAR, porque o staging real do ensaio anterior foi descartado e ainda falta a validação da saída de links pela API. O HOLD atual continua apenas para **ativação automática/publicação e afirmações globais**, não como impedimento de evolução da integração.
