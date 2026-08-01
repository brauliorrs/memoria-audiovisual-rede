# Política de publicação e acesso aos dados

## Objetivo

Definir quais camadas da plataforma poderão ser publicadas, quais permanecerão internas e como cada produto deverá informar versão, snapshot, cobertura, proveniência, limitações e estado de validação.

## Princípios

1. Dados brutos, inferências heurísticas e resultados curados não serão tratados como equivalentes.
2. Nenhum registro pendente de revisão alimentará produto público.
3. Toda publicação deverá indicar o snapshot, a versão do schema e a versão metodológica utilizada.
4. A ausência de evidência não será publicada como ausência da tecnologia, fornecedor, contrato ou sistema de IA.
5. Produtos públicos deverão conter metadados suficientes para reprodução e interpretação.
6. Informações sensíveis, inseguras ou juridicamente restritas não serão publicadas.

## Camadas de acesso

### 1. Internal raw

Uso interno. Inclui:

- respostas HTTP e artefatos brutos;
- HTML, JSON, XML e documentos coletados;
- sinais heurísticos ainda não revisados;
- logs técnicos;
- anotações curatoriais preliminares.

Não é publicável por padrão.

### 2. Internal reviewed

Uso interno e de auditoria metodológica. Inclui:

- registros revisados;
- falsos positivos identificados;
- justificativas curatoriais;
- ocorrências de integridade;
- evidências que não podem ser redistribuídas.

Pode ser compartilhado apenas em ambiente controlado.

### 3. Restricted research

Acesso sob solicitação ou acordo de pesquisa. Inclui:

- dados derivados com restrições de redistribuição;
- evidências documentais parcialmente protegidas;
- conjuntos que exijam contextualização adicional;
- dados necessários à replicação, mas inadequados para publicação aberta integral.

### 4. Public curated

Camada pública principal. Inclui apenas:

- registros confirmados ou curados;
- evidências redistribuíveis ou referências públicas;
- snapshots fechados;
- indicadores com cobertura e comparabilidade adequadas;
- limitações documentadas.

### 5. Public aggregate

Resultados agregados destinados ao painel, relatórios e API pública. Inclui:

- indicadores;
- séries temporais;
- distribuições;
- matrizes comparativas;
- sínteses de risco e dependência.

## Produtos de publicação

A plataforma poderá expor:

- painel Streamlit;
- arquivos CSV;
- arquivos JSON;
- API pública somente leitura;
- manifestos de snapshot;
- catálogo de indicadores;
- documentação metodológica;
- pacotes de dados versionados para depósito científico.

## Metadados obrigatórios

Todo produto público deverá informar:

- `product_id`;
- `product_type`;
- `publication_version`;
- `snapshot_id`;
- `schema_version`;
- `methodology_version`;
- `generated_at`;
- `coverage_start` e `coverage_end`;
- `coverage_ratio`, quando aplicável;
- `validation_status`;
- `comparability_class`;
- `provenance_reference`;
- `license`;
- `known_limitations`;
- `supersedes_product_id`, quando aplicável.

## Regras por formato

### CSV

- UTF-8;
- cabeçalhos estáveis e documentados;
- um arquivo de metadados associado;
- valores ausentes diferenciados de `false` ou `0`;
- identificadores persistentes.

### JSON

- validado por schema;
- tipos explícitos;
- datas em ISO 8601;
- metadados de versão no nível raiz;
- ausência representada por `null`, nunca por inferência.

### API

- somente leitura na primeira fase;
- endpoints versionados;
- paginação;
- filtros documentados;
- resposta com snapshot e proveniência;
- limites de uso e política de cache;
- nenhuma exposição de camada bruta interna.

### Painel

- resultados acompanhados de cobertura e data de referência;
- filtros não poderão produzir indicador abaixo do limiar de publicação;
- tooltips com definição e limitações;
- distinção visual entre resultado confirmado, provável e inconclusivo;
- acesso ao manifesto e à metodologia correspondente.

## Licenciamento

Cada produto deverá declarar licença própria. A licença dos dados derivados não substitui os direitos incidentes sobre documentos e fontes originais.

## Retirada e correção

Produtos podem ser:

- `draft`;
- `published`;
- `superseded`;
- `withdrawn`;
- `archived`.

Uma correção não apagará a versão anterior. A nova publicação deverá apontar para o produto substituído e registrar a razão da alteração.

## Critérios mínimos para publicação

Um produto público exige:

- snapshot fechado;
- integridade relacional sem erros bloqueantes;
- registros elegíveis para publicação;
- cobertura acima do limiar definido;
- schema e metodologia versionados;
- manifesto completo;
- revisão humana final.
