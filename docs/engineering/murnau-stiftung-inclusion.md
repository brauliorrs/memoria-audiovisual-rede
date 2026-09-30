# Friedrich-Wilhelm-Murnau-Stiftung — decisão de incorporação

**Fila europeia:** antigo rank 7; cabeça operacional após o Forum des images.  
**Decisão metodológica:** **incorporar como corpus institucional ativo**, limitado ao catálogo público de filmes observado na listagem alfabética A–Z.

## 1. Fonte e gate

A instituição disponibiliza uma base pública de filmes com:

- busca por metadados;
- índice alfabético A–Z;
- fichas permanentes `/movie/<id>`;
- ano de produção e outros metadados;
- política `robots.txt` verificável pelo executor do MAR.

O corpus não baixa mídia e não trata a existência de uma ficha como evidência de streaming público.

## 2. Prova operacional

O probe real do PR #35 foi executado no GitHub Actions com o coletor fail-closed.

**Rodada que confirmou o gate:**
- Quality Checks: #1778;
- workflow run: `36789372829`;
- HEAD: `24d37ec3195a1b1516264676526d9692f641d542`;
- artifact: `murnau-stiftung-probe`;
- artifact id: `11130986290`;
- artifact digest: `sha256:7c30e907128595d45e8007c2914748c1148a2ace9853d4b39addfcbc97591736`.

Resultado:
- **3.889 IDs únicos** de fichas públicas;
- **26/26 partições A–Z** respondidas;
- todas as partições observadas sem erro;
- 24 fichas enriquecidas no limite de detalhe da rodada;
- `integrity_status=integro`;
- nenhum download de mídia.

Contagens por partição:

`A:207, B:216, C:49, D:153, E:147, F:234, G:253, H:200, I:148, J:74, K:219, L:172, M:276, N:87, O:38, P:131, Q:12, R:125, S:407, T:159, U:79, V:151, W:258, X:2, Y:4, Z:88`.

## 3. Distinção entre acervo físico e catálogo público

A Murnau-Stiftung declara mais de 6.000 filmes em seu acervo próprio. Esse número descreve o **acervo custodial/físico** e não é usado pelo MAR como denominador de completude do catálogo público.

O universo materializado nesta rodada é:

> **3.889 fichas públicas expostas nas 26 partições alfabéticas A–Z da superfície observada.**

Portanto:
- não se afirma que o catálogo público contém todos os filmes do acervo físico;
- não se afirma que os 3.889 títulos estejam disponíveis para streaming;
- não se usa a diferença `>6.000 - 3.889` como medida de ausência digital;
- o corpus representa somente o que foi publicamente materializado pelo protocolo da rodada.

## 4. Regra de completude operacional

Um snapshot Murnau é elegível para atualização quando:

1. `robots.txt` é verificável e permite as rotas observadas;
2. todas as 26 partições A–Z são consultadas;
3. pelo menos um registro público é materializado;
4. nenhuma partição obrigatória falha;
5. IDs são deduplicados;
6. snapshot e checks terminam sem erro.

Letras legitimamente vazias seriam permitidas; o critério é resposta íntegra da partição, não presença artificial de ao menos um título.

## 5. Relação com instrumentos experimentais

M3, M4 e demais instrumentos experimentais **não participaram** da decisão de incorporação.

A admissão decorre de:
- relevância audiovisual institucional;
- superfície pública de metadados;
- enumeração reprodutível;
- prova operacional;
- limites de inferência explícitos;
- CI e snapshot íntegros.

## 6. Estado na fila

Após a promoção da Murnau-Stiftung:
- `efg-friedrich-wilhelm-murnau-stiftung` deixa a fila e passa a `corpus_ativo`;
- **Gosfilmofond of Russia** (`fiaf-gosfilmofond`) torna-se a próxima unidade operacional da fila, com rank compactado para 6.

A incorporação de Gosfilmofond continua sujeita ao seu próprio gate e não herda automaticamente a decisão deste corpus.
