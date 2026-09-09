# Política de publicação e acesso aos dados

## Objetivo

Definir quais camadas da infraestrutura podem ser publicadas, quais permanecem internas e como cada produto informa versão, snapshot, cobertura, proveniência, limitações, revisão e estado editorial.

## Princípios

1. Dados brutos, detecções, decisões curatoriais, indicadores e textos públicos não são equivalentes.
2. Nenhum registro pendente de revisão alimenta produto público como resultado confirmado.
3. Toda publicação indica snapshot, schema, metodologia, cobertura e data de referência.
4. Ausência de evidência não é publicada como ausência de tecnologia, fornecedor, contrato ou IA.
5. Produtos públicos contêm metadados suficientes para interpretação e reprodução proporcional.
6. Informações sensíveis, inseguras ou juridicamente restritas não são publicadas.
7. Elegibilidade técnica não equivale a decisão editorial de publicação.
8. Correções e retiradas preservam o histórico.

## Camadas de acesso

### 1. Internal raw

Uso interno. Inclui artefatos brutos, respostas técnicas, sinais heurísticos, logs e anotações preliminares. Não é publicável por padrão.

### 2. Internal reviewed

Uso interno e de auditoria metodológica. Inclui registros revisados, falsos positivos, justificativas curatoriais, ocorrências de integridade e evidências não redistribuíveis.

### 3. Restricted research

Acesso sob solicitação ou acordo. Inclui dados derivados com restrições, evidências parcialmente protegidas e conjuntos que exigem contextualização adicional.

### 4. Public curated

Inclui registros revisados e editorialmente aprovados, evidências redistribuíveis ou referências públicas, snapshots fechados, cobertura explícita e limitações documentadas.

### 5. Public aggregate

Inclui indicadores, séries, distribuições e sínteses que superaram os controles de denominador, cobertura, revisão e publicação.

## Portões de publicação

Um item público atravessa, quando aplicável, os seguintes portões:

1. **integridade:** estrutura, referências e hashes válidos;
2. **metodologia:** definição, população e estados avaliativos corretos;
3. **evidência:** suporte identificável e proporcional ao enunciado;
4. **revisão:** quórum e decisão curatorial compatíveis;
5. **cobertura:** limites, exclusões e denominadores explícitos;
6. **direitos:** licença, privacidade e redistribuição avaliadas;
7. **editorial:** redação, contexto e canal aprovados;
8. **contestação:** ausência de bloqueio cautelar ativo.

A aprovação em um portão não implica aprovação automática nos seguintes.

## Produtos

A infraestrutura pode gerar:

- projeção pública versionada;
- arquivos CSV e JSON;
- manifestos de snapshot e publicação;
- indicadores e documentação metodológica;
- pacotes versionados para depósito científico;
- painel analítico;
- futura API somente leitura;
- vitrine pública independente do observatório analítico.

A existência de um arquivo em diretório público interno não significa que ele já esteja publicado em site, API ou painel.

## Metadados obrigatórios

Todo produto público deve informar:

- `product_id`;
- `product_type`;
- `publication_version`;
- `snapshot_id`;
- `schema_version`;
- `methodology_version`;
- `generated_at` e `published_at`;
- cobertura temporal e institucional;
- denominador ou população elegível, quando aplicável;
- `validation_status`;
- `editorial_status`;
- `comparability_class`;
- referência de proveniência;
- licença;
- limitações conhecidas;
- produto substituído, quando aplicável;
- estado de contestação ou retirada, quando aplicável.

## Regras por formato

### CSV

- UTF-8;
- cabeçalhos estáveis e documentados;
- metadados associados;
- valores ausentes distintos de `false` ou `0`;
- identificadores persistentes.

### JSON

- validado por schema;
- tipos explícitos;
- datas em ISO 8601;
- metadados de versão no nível raiz;
- ausência representada por `null` ou estado avaliativo explícito.

### API

- somente leitura na primeira versão;
- endpoints versionados;
- paginação e filtros documentados;
- resposta vinculada a snapshot e proveniência;
- nenhuma exposição da camada bruta interna.

### Painel e vitrine

- cobertura e data de referência visíveis;
- definições e limitações acessíveis;
- distinção entre resultado, hipótese e estado inconclusivo;
- ligação ao manifesto e à metodologia;
- vitrine institucional separada do ambiente analítico quando essa arquitetura for adotada.

## Licenciamento

Cada produto declara licença própria. A licença dos dados derivados não substitui direitos incidentes sobre documentos, imagens, vídeos e fontes originais.

## Estados editoriais

Produtos podem ser:

- `draft`;
- `eligible`;
- `published`;
- `contested`;
- `suppressed`;
- `superseded`;
- `withdrawn`;
- `archived`.

## Retirada e correção

Uma correção não apaga a versão anterior. A nova publicação aponta para o produto substituído, registra a razão, o impacto e a data. Conteúdo contestado pode ser marcado, suprimido ou retirado cautelarmente sem que isso represente reconhecimento automático de erro.

## Estado atual

A projeção pública derivada e o versionamento editorial estão implementados estruturalmente. A API, a vitrine definitiva e a primeira política operacional de publicação científica ainda dependem de validação e decisão institucional.