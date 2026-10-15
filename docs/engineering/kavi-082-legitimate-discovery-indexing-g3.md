# MAR — análise nº 82: descoberta e indexação legítima de KAVI/Kuvi (G3)

**Data da revisão:** 2026-10-15 · **Escopo:** metadados e links; sem download/streaming pelo MAR.  
**Decisão:** **HOLD provisório de admissão ao corpus** com caminho de indexação de metadados **identificado e documentalmente autorizado no escopo CC0 da API Finna**. `investigation_complete=false`; não afirmar coletor de produção validado.  
**Base:** [issue #59](https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59), [protocolo público G0–G4](public-access-first-protocol.md), [mapa de serviços](kavi-082-subservices-access-map.md) e ensaios versionados `kavi-082-probe.md`, `kavi-082-resumption-integrity.md`, `kavi-082-metadata-staging.md`, `kavi-082-upstream-token-error-contract.md`.

## 1. Escopo correto: descoberta humana primeiro

- **Instituição:** Finnish Arts and Culture Agency (Kuvi; antigo KAVI). Não criar duas instituições/coleções só por alteração administrativa.
- **Serviços:** Elonet (filmografia e VOD), Elävä muisti (memória audiovisual editorial com possível sobreposição), Elokuvapolku (ensino e links a filmes), Ritva/RTVA (metadados de rádio/TV com execução em pontos de consulta); cinema e programação cultural não são fichas de filmes.
- **G1:** fichas Elonet observadas a partir de links Elokuvapolku, por exemplo `kavi.elonet_elokuva_117938` e `kavi.elonet_elokuva_118019`. O visitante relatou reprodução de `kavi.elonet_elokuva_157199` **após desafio de confirmação humana**. Marcar a fonte do relato: não é execução independente de player pela ferramenta.
- **G2:** o direito de assistir no site de origem não equivale a baixar, republicar, incorporar player ou reproduzir por proxy no MAR. Um HTTP 403 em navegador automatizado não invalida a experiência humana de acesso, mas também **não autoriza** contornar o desafio.
- **Identificação de obras:** IDs Finna/Elonet retornados por uma fonte auditável, URL de ficha canônica e relação com serviço que descobriu o item. Não fabricar sufixos de ID, não converter evento/editorial em filme cadastrado e não triplicar a mesma obra encontrada em serviços distintos.

## 2. Autorizações e limites documentados

| Questão | Evidência oficial | Decisão para o MAR |
|---|---|---|
| Metadados da API Finna | [Finna API Terms of Use](https://www.kiwi.fi/spaces/Finna/pages/53839699/Finna%2BAPI%2BTerms%2Bof%2BUse): interface aberta sem registro obrigatório; **metadados efetivamente fornecidos pela API sob CC0 1.0** | **Indexação desses metadados é permitida pelos termos publicados**, sujeita às regras de acesso, carga e outras normas aplicáveis |
| Recursos associados | Mesmos termos: CC0 **não cobre** imagens, vídeos ou recursos nos campos `urls`, `onlineUrls`, `images`; examinar `imageRights` e `accessRestrictions` | Armazenar apenas metadados cobertos e **hiperlinks a fichas**; não baixar recursos nem reproduzir mídia |
| Cobertura do universo Finna | Termos da API: por direitos de terceiros **nem todos os metadados exibidos no serviço** são fornecidos na API | Mesmo enumeração completa da API **não equivale ao universo de fichas do site**; registrar explicitamente `api_exposed_subset` |
| Descrições da interface web | [Termos do Elonet](https://elonet.finna.fi/Content/terms?lng=en-gb): descrições em geral utilizáveis, com exceções e possíveis restrições em interfaces específicas | Preferir os campos CC0 da API; **não** presumir que textos editoriais, sinopses extensas e contribuições do usuário tenham CC0 |
| Automação no site com autenticação | Termos do Elonet proíbem métodos automatizados nas funcionalidades que exigem login; podem limitar o serviço | **Não raspar a interface sujeita a desafio humano**, não automatizar login nem contornar proteção |
| Rate e integridade | [Documentação API Finna](https://www.kiwi.fi/spaces/Finna/pages/53839221/Finna%2BAPI%2Bin%2BEnglish): `limit` de 0–100, paginação ordinária limitada a 100 mil, `resumptionToken` para lotes grandes | Preferir rota oficial de API, somente com `robots.txt` do host auditado e limites do provedor observados; proteger contra truncamento, repetição e token inválido |
| OAI-PMH Finna | [Finna OAI-PMH harvesting](https://www.kiwi.fi/pages/viewpage.action?pageId=301990412): provedor oficial e seleção por *sets* do provedor; não suporta filtragem livre; documentação menciona que exclusões não são notificadas | **Alternativa a estudar**, não substituto autorizado: ainda **não demonstrado** set que isole `KAVI × vídeo`, sem prova de deletions ou compatibilidade de custódia |
| Custódia e direitos | KAVI/Elonet cataloga obras que nem sempre estão sob sua custódia, e os direitos variam por item | Faceta institucional Finna indica **provedor de metadados**, não necessariamente detentor do filme ou autorização de reprodução no MAR |

**Importante:** os termos publicados são evidência de licença **sobre o subconjunto de metadados ofertado pela API**, não certificado de que o backend está acessível por qualquer robô, nem de que todos os dados da ficha individual possam ser copiados. Registro de fonte é recomendado pelos termos mesmo para CC0.

## 3. Viabilidade técnica encontrada — reaproveitar o que já existe

A prova anterior [KAVI-082 probe](kavi-082-probe.md) verificou filtros que foram **devolvidos pela própria API**: `building:"0/KAVI/"` (provedor Kuvi/KAVI) e `format:"0/Video/"` (vídeo). Amostra histórica: cerca de **138.377–138.379 registros no índice**, valor volátil. Isso não representa a quantidade de filmes assistíveis, nem a quantidade de obras custodiadas.

A prova de continuação [KAVI-082 resumption integrity](kavi-082-resumption-integrity.md) validou **400 metadados em duas páginas reais**, com correspondência entre IDs, trilha de escopo e integridade; **399 candidatos a filme e 1 outro vídeo**, nenhum com direito de mídia ou custódia individual estabelecidos. A execução de duas páginas **não equivale a enumeração integral**.

**Executor já existente**: `scripts/run_kavi_finna_metadata_staging.py` + `src/memoria_audiovisual/kavi_finna_adapter.py` + `RawArtifactStore` / estágio `stage_metadata`. Possui:
- opt-in `--execute`, execução limitada a 1–25 páginas, controle de requisições, preflight de `robots.txt`, validação de filtros/código institucional, checkpoints imutáveis e hashes;
- `promotion_authorized=false` e `media_downloaded=false` por contrato; metadados e cursors não são transferidos automaticamente à produção;
- rejeição segura de respostas de erro ou tokens inválidos/expirados; o servidor não diferencia de modo inequívoco token inválido vs. expirado e o executor não deve reiniciar arbitrariamente.

**Conclusão de engenharia:** NÃO construir outro coletor Finna ou iniciar enumeração massiva para provar que o site é público. O problema remanescente não é ausência de código-base de coletor, mas evidência de autorização operacional atual, delimitação de catálogo, fecho de cobertura, separação entre `film_candidate` e outras formas audiovisuais e direitos/proveniência das fichas.

## 4. Matriz de estados G0–G4 (até esta revisão)

| Gate | Evidência atingida | Lacuna / limite | Resultado |
|---|---|---|---|
| G0 – instituição e rotas | KAVI/Kuvi, Elonet, Elävä muisti, Elokuvapolku, Ritva diferenciados | Mudanças e redirecionamentos podem ocorrer | **Suficiente para investigação** |
| G1 – descoberta pública humana | Fichas individuais Elonet e link cruzado Elokuvapolku; filme reproduzido conforme relato do visitante | Alguns catálogos e ficha Elävä muisti impedem leitura automatizada | **Acesso humano confirmado em escopo limitado** |
| G2 – metadados/mídia | Fichas e descrição pública; reprodução humana relatada de uma obra | Licenças de mídias e custódia individual não comprovadas | **Fichas públicas ≠ mídia livre** |
| G3 – automação | API oficial CC0, filtros de origem, 400 metadados em 2 lotes e código staged implementado | `robots` atual não revalidado nesta sessão; enumeração integral, rotina de replay da cobertura e estabilidade de token não comprovadas; OAI set específico não verificado | **Parcialmente verificado** |
| G4 – decisão | Inventário `fiaf-kavi.json` preservado e decisão segregada | Gate científico de corpus não concluído | **HOLD provisório, investigação aberta** |

**Nota metodológica de acesso:** os `robots.txt` foram avaliados em execuções históricas do projeto, com HTTP 200 em vários probes, mas nesta revisão as tentativas de abrir `elonet.finna.fi/robots.txt`, `api.finna.fi/robots.txt` e `www.finna.fi/robots.txt` não forneceram evidência utilizável por esta ferramenta. **Não declarar que os robots atuais foram auditados**, nem usar testes antigos como permissão permanente.

## 5. Próxima ação mínima — não iniciar outro loop

1. **Gate de autorização, sem coleta:** validar novamente os `robots` do host de API, política de uso do serviço, identidade pública do cliente e intervalo de requests; se não verificado, parar em `environment_limited` e preservar as provas anteriores.
2. **Escopo identificável:** reutilizar o filtro **observado** de `building × format`; num único ensaio permitido e auditado, confirmar que o conjunto retornado corresponde a vídeos atribuídos ao provedor e registrar percentuais de classes (`film_candidate`, outros), sem declarar que tudo é filme sob custódia.
3. **Prova de completa enumeração somente em protocolo separado e aprovado:** a API documenta `resumptionToken`, mas os testes atuais não provam >100 mil registros sem falhas; qualquer tentativa de fecho deve prever expiração/cursor, corte em caso de erro, proibição de reinícios ilimitados, divergência de total, deduplicação e direito de interrupção por limite/carga.
4. **Mapeamento de saída, sem mídia:** somente quando admitido, cada linha terá `provider=Kuvi/KAVI`, `discovery_service`, `source_record_id`, `canonical_item_url`, `title`, `year`, `content_type`, `rights_evidence`, `access_category`, `evidence_observed_on`, `dataset_scope` e `provenance`. Sempre encaminhar o visitante ao Elonet/serviço de origem. Não gerar URLs canônicas por mera concatenação de ID sem confirmação da forma oficial.
5. **Elävä muisti, Elokuvapolku e Ritva:** manter estudos de superfície específicos e não acrescentar seus conteúdos aos 138 mil resultados sem prova de pertença, licença e desduplicação; OAI-PMH só será considerado se houver *set* documentado compatível e regras de remoção explicitadas.

### Decisão formal desta iteração

- **PUBLIC_ACCESS_OBSERVED:** sim (fichas Elonet; reprodução humana informada e atribuída).
- **METADATA_LICENSE_SCOPE:** CC0 somente para registros efetivamente servidos pela API Finna; recursos de mídia excluídos.
- **MACHINE_ENUMERATION:** mecanismo disponível, prova parcial e infraestrutura staged existente; **não declarar cobertura completa**.
- **AUTOMATED_WEB_SCRAPING:** não autorizado/avaliado para interfaces com desafio humano; **sem bypass**.
- **CORPUS_ADMISSION:** **HOLD PROVISÓRIO**, `investigation_complete=false`, `promotion_authorized=false`, `media_downloaded=false`.
- **NEXT_QUEUE:** manter análise nº 82 aberta; nº 83 segue sem início automático.

Esta é uma revisão de evidências públicas e artefatos do repositório. **Nenhuma nova chamada viva ao endpoint de pesquisa Finna foi realizada nesta iteração.**
