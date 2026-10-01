# Gosfilmofond — decisão de incorporação do catálogo público

**Fila europeia:** antigo rank 8; cabeça operacional após a Murnau-Stiftung.  
**Decisão metodológica:** **incorporar como corpus institucional ativo**, limitado à superfície pública de metadados enumerada por `/films/` + `admin-ajax.php`.

## 1. Fonte e gate

O catálogo público do Gosfilmofond expõe filtros por metadados e fichas permanentes `/films/<key>/`. A própria superfície usa o endpoint WordPress `/wp-admin/admin-ajax.php` para paginação.

O executor MAR relê `robots.txt` em modo fail-closed. Na rodada de admissão:
- `/films/` estava permitido;
- `/wp-admin/admin-ajax.php` estava explicitamente permitido;
- o maior tamanho de página declarado pela interface era 100;
- a primeira resposta declarava 598 páginas.

O corpus não escaneia IDs e não baixa mídia.

## 2. Prova operacional

A enumeração staged real foi executada no GitHub Actions no PR #38.

Rodada que comprovou o gate de corpus:
- workflow: Quality Checks #1808;
- run id: `36904019386`;
- HEAD da rodada: `70e63e5d1e7ce162276aed9f2ad188c050014a18`;
- artifact: `gosfilmofond-staged-baseline`;
- artifact id: `11185896280`;
- artifact ZIP SHA-256: `fd2f0d421fcec2800629e923f66b9003107b7b7e1ca0fa42c7acf4120ce96bbc`.

O workflow completo foi cancelado após novos commits no PR, mas **as etapas de materialização, validação do baseline e upload do artefato já haviam concluído com sucesso** antes do cancelamento. A promoção continua condicionada ao Quality Checks do HEAD final do PR.

Resultado da rodada:
- **59.733 registros públicos únicos**;
- **598 páginas AJAX enumeradas**;
- `integrity_status=integro`;
- todos os arquivos esperados encontrados;
- 24 arquivos de saída preservados no artefato;
- nenhum download de mídia.

## 3. Regra de completude operacional

Um snapshot Gosfilmofond só é elegível quando:

1. `robots.txt` é verificável e permite catálogo + endpoint AJAX;
2. o tamanho de página é obtido da própria interface pública;
3. a paginação total é estabelecida pela resposta pública;
4. todas as páginas obrigatórias são percorridas;
5. páginas intermediárias têm a cardinalidade esperada;
6. não existem duplicações entre páginas;
7. os permalinks ficam restritos a `https://gosfilmofond.ru/films/<key>/`;
8. snapshot e catálogo concordam na contagem;
9. os checks terminam sem erro.

Os limites mínimos de 50.000 registros e 500 páginas são guardrails contra truncamento grosseiro do mecanismo observado, não estimativas do acervo físico.

## 4. Distinção entre catálogo web e acervo físico

O MAR não usa números institucionais de rolos, materiais ou itens custodiais como denominador deste corpus.

O universo materializado na rodada de admissão é:

> **59.733 fichas públicas enumeradas em 598 páginas AJAX da superfície observada.**

Portanto:
- não se afirma cobertura integral do acervo físico;
- não se afirma que as fichas correspondam a streaming público;
- não se infere licença de reprodução a partir da ficha;
- a completude é definida somente em relação à paginação pública materializada.

## 5. Robustez adicionada após o baseline

O review do PR identificou dois pontos P2 e ambos foram corrigidos antes da promoção:
- respostas AJAX em envelope JSON agora são decodificadas antes do parsing de cards;
- artefatos staged passam a ser preservados com `always()` mesmo quando o check de baseline falha.

Há teste regressivo específico para o envelope JSON.

## 6. Relação com instrumentos experimentais

M3, M4 e demais instrumentos experimentais **não participam** da decisão de incorporação.

A admissão decorre exclusivamente de relevância institucional audiovisual, enumeração pública reprodutível, política de acesso técnico verificável, completude operacional delimitada e CI.

## 7. Estado na fila

Após a promoção:
- `fiaf-gosfilmofond` deixa a fila e passa a `corpus_ativo`;
- **Croatian State Archive - Croatian Cinematheque** (`fiaf-croatian-cinematheque`) torna-se a próxima unidade operacional, com rank compactado para 6.

A unidade seguinte continua sujeita ao seu próprio gate; nenhuma decisão é herdada do Gosfilmofond.
