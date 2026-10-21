# Estratégia de reconciliação dos PRs #5 e #7 com a `main`

Status: **plano de integração; não autoriza merge direto de #5 ou #7**.

## 1. Decisão arquitetural

Os PRs #5 e #7 não serão tratados como unidades de merge/rebase.

- **#5** será tratado como fonte da arquitetura longitudinal de infraestrutura digital, analytics e documentação científica.
- **#7** será tratado como fonte das camadas posteriores de plataforma científica, baseline operacional, internacionalização, UI e T2A/IA.
- A linha de integração nascerá da `main` depois da estabilização dos PRs #8 e #12.
- Cada componente de #5/#7 será portado para a linha nova em PRs pequenos e verificáveis.

A justificativa é objetiva: #5 e #7 nasceram de uma base anterior da `main`, #7 é empilhado sobre #5, e ambos preservam uma versão antiga do adaptador que não contém as correções já validadas no #8.

## 2. Baseline de referência

### PR #8 — Porta 2

HEAD validado: `ac176f6b1726f97467360a5a18618609e4bb4ab7`.

Invariantes que passam a ser **não negociáveis** durante a reconciliação:

1. `api_open_detected=True` + `evidence_urls` não pode ser convertido em `not_detected` quando `api_types` estiver vazio.
2. Cada `evidence_url` deve ser preservada individualmente.
3. `evidence_url` deve participar da identidade estável da detecção/evidência quando houver múltiplas evidências para o mesmo sinal.
4. `curated` e `publishable` devem ser derivados da última versão válida de cada entidade no ledger, não apenas da coleta `raw` corrente.
5. Revisão humana é append-only; observação bruta não é sobrescrita.
6. Fonte inalcançável/bloqueada/timeout não pode ser convertida automaticamente em ausência de tecnologia.
7. Detecção automática permanece `pending_review` até decisão curatorial explícita.
8. `false_positive` nunca entra na camada publicável; somente estados explicitamente permitidos podem alimentar produtos públicos.

### PR #12 — dependências

A reconciliação também deve preservar o alinhamento entre dependências diretas declaradas em `pyproject.toml` e o manifesto de runtime, incluindo `jsonschema` como dependência direta.

## 3. Regra de compatibilidade de namespace

A migração `memoria_audiovisual.statetech` → `memoria_audiovisual.digital_infrastructure` **não será big-bang**.

Durante a transição:

- `digital_infrastructure` será o namespace canônico novo;
- `statetech` permanecerá temporariamente como camada de compatibilidade;
- consumidores serão migrados em lotes pequenos;
- os testes de contrato do #8 deverão executar contra o namespace canônico novo antes da remoção de qualquer shim;
- a remoção de `statetech` só poderá ocorrer quando busca de imports, testes e workflows mostrarem zero consumidores ativos.

## 4. Ondas de reconciliação

### Onda 0 — baseline integrada

Objetivo: criar uma `main` verde contendo as correções de #8 e #12.

Gates:

- CI completo verde;
- `Validate Porta 2 contract` verde;
- checagem de dependências verde;
- deployment snapshot verde;
- nenhuma alteração de significado em dados históricos.

### Onda 1 — namespace e contratos centrais

Portar de #5 apenas os elementos necessários para estabelecer o namespace novo sem alterar comportamento científico:

- package `digital_infrastructure`;
- contratos/schemas centrais;
- modelos, IDs, evidência, proveniência e ledger;
- serviço de dados;
- shims temporários em `statetech`.

Gates específicos:

- todos os testes do #8 continuam verdes;
- IDs estáveis não mudam sem migração explícita;
- nenhuma observação histórica é reescrita;
- schema registry resolve as duas rotas durante a transição quando necessário.

### Onda 2 — núcleo longitudinal de #5

Portar separadamente:

1. ingestão e artefatos brutos content-addressed;
2. batches/manifests;
3. cobertura e matriz de parâmetros;
4. revisão curatorial;
5. materialização;
6. preflight/postflight;
7. visão pública e revisão de publicação.

Regra: cada bloco entra em PR próprio ou em PR pequeno com um único objetivo verificável.

Gates:

- ingestão é idempotente ou explicitamente versionada;
- ledger permanece append-only;
- revisão/materialização nunca promove automaticamente `pending_review`;
- `curated`/`publishable` continuam baseados na última versão do ledger;
- evidências múltiplas continuam distinguíveis por URL/identidade.

### Onda 3 — analytics e documentação de #5

Portar:

- motor analítico;
- catálogo de indicadores;
- registro de metodologia;
- indicadores de acesso/interoperabilidade;
- persistência analítica;
- documentação científica correspondente.

Gates:

- nenhum indicador usa dados `pending_review` como evidência publicada;
- denominadores são explícitos e versionados;
- ausência de dado não é convertida silenciosamente em zero;
- reexecução não sobrescreve histórico incompatível.

### Onda 4 — plataforma científica de #7

Portar em blocos independentes:

- `scientific_infrastructure`;
- reference corpus e manifests;
- baseline operacional;
- internacionalização;
- UI e apresentação de indicadores.

Gates:

- baseline oficial continua reproduzível com IA experimental desligada;
- interface não apresenta ausência de artefato como resultado empírico;
- produtos científicos apontam para fonte canônica, versão e hash.

### Onda 5 — T2A/IA de #7

Portar somente após a Onda 4 estabilizada:

- runtime/flags de IA;
- experiment registry;
- surface typing;
- filas/revisões independentes;
- validações M3/M4;
- IA de conteúdo e IA institucional.

Gates:

- feature flags desligam completamente dependências experimentais do baseline;
- prediction freeze, human freeze e ordem temporal são verificadas antes de qualquer métrica;
- protocolo/versão/commit/hash precisam coincidir;
- IDs duplicados, ausentes ou extras abortam a avaliação;
- revisão humana incompleta aborta a avaliação;
- dados experimentais não alteram retroativamente baseline oficial.

### Onda 6 — artefatos gerados e histórico

Snapshots, ledgers, filas, avaliações, raw artifacts e resultados materializados de #7 só entram depois do código que os valida.

Cada lote deve ter:

- commit produtor identificável;
- protocolo e versão;
- hashes verificáveis;
- vínculo com snapshot/experimento;
- validação temporal;
- inventário de exposição/publicabilidade.

## 5. Ordem de extração dos PRs antigos

### Do #5

Portar primeiro código de núcleo e contratos. Deixar para depois workflows de publicação, documentação extensa e analytics. Não importar o adaptador `1.1.0` como está: ele deve ser reconstruído sobre as invariantes do #8.

### Do #7

Portar somente depois que o núcleo equivalente de #5 já existir na linha nova. O PR #7 é delta sobre #5 e não deve ser retargeted diretamente para `main` como mecanismo de integração.

## 6. Arquivos de conflito obrigatório

Qualquer port que toque estes pontos exige revisão manual explícita:

- `scripts/audit_digital_infrastructure.py`;
- `src/memoria_audiovisual/digital_infrastructure_audit.py`;
- adaptador de auditoria no namespace novo;
- serviço/ledger/revisão/materialização;
- `.github/workflows/quality.yml`;
- schemas de infraestrutura digital;
- arquivos de baseline/ledger/freeze.

Nesses arquivos, não se aceita resolução de conflito por escolha integral de um lado (`ours/theirs`).

## 7. Critério de aborto

A reconciliação deve parar antes do merge de qualquer onda se ocorrer um dos seguintes:

- regressão de qualquer invariante do #8;
- perda ou colapso de `evidence_url`;
- reclassificação de indisponibilidade como ausência;
- sobrescrita de versão histórica;
- dependência do baseline em IA/T2A;
- alteração de IDs sem migração explícita;
- artefato gerado sem origem/hash/protocolo verificáveis;
- CI verde apenas por remoção/enfraquecimento de teste.

## 8. Critério de conclusão

A reconciliação estará concluída quando:

1. todo componente necessário de #5/#7 estiver portado ou explicitamente descartado;
2. #5 e #7 puderem ser encerrados como superseded sem perda funcional relevante;
3. o namespace `digital_infrastructure` for canônico;
4. a compatibilidade `statetech` puder ser removida sem consumidores ativos;
5. todos os gates científicos, de proveniência, ledger, dependências e CI estiverem verdes na `main`.
