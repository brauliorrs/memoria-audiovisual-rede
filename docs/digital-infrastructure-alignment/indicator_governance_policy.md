# Política de governança de indicadores

## Objetivo

Definir como variáveis validadas serão convertidas em indicadores publicáveis, comparáveis e auditáveis sem confundir evidência técnica, inferência analítica e julgamento curatorial.

## Princípio central

Nenhum indicador poderá ser publicado sem:

- definição versionada;
- universo e denominador explícitos;
- regra de inclusão e exclusão;
- unidade de análise;
- período de referência;
- classe de comparabilidade;
- nível de confiança;
- vínculo com snapshot fechado;
- responsável pela revisão.

## Classes de indicador

### Descritivos

Contagens, proporções e distribuições diretamente derivadas de registros validados.

Exemplos:

- instituições com API pública confirmada;
- instituições com IIIF confirmado;
- fornecedores privados identificados;
- contratos tecnológicos confirmados;
- sistemas de IA em estágio operacional confirmado.

### Relacionais

Medem relações entre instituições, tecnologias, fornecedores, contratos, fluxos e plataformas.

Exemplos:

- número médio de fornecedores por instituição;
- concentração de fornecedores por camada do stack;
- proporção de instituições dependentes de plataforma externa;
- densidade de relações instituição–tecnologia.

### Longitudinais

Medem mudança entre snapshots comparáveis.

Exemplos:

- adoção ou descontinuação de APIs;
- mudança de fornecedor;
- início ou término de contratos;
- alteração no regime de acesso;
- surgimento, suspensão ou retirada de sistemas de IA.

### Analíticos e de risco

Dependem de regras interpretativas versionadas e revisão humana.

Exemplos:

- dependência crítica de fornecedor único;
- concentração de infraestrutura;
- risco de descontinuidade;
- opacidade contratual;
- baixa auditabilidade algorítmica.

## Estados de publicação

- `draft`: definição em elaboração;
- `reviewed`: definição metodológica revisada;
- `approved`: apto para cálculo;
- `published`: resultado divulgado;
- `deprecated`: não deve mais ser usado em novos produtos;
- `withdrawn`: retirado por erro ou insuficiência metodológica.

## Níveis de confiança

- `high`: evidência primária, relação validada e cobertura adequada;
- `moderate`: evidência suficiente, mas com alguma limitação de cobertura ou temporalidade;
- `low`: resultado exploratório, não apto a afirmação institucional forte;
- `not_publishable`: insuficiente para publicação.

## Regras de denominador

O denominador deve declarar:

- universo teórico;
- universo observado;
- registros avaliáveis;
- registros não avaliáveis;
- exclusões metodológicas;
- cobertura territorial e institucional;
- versão do schema e do snapshot.

Percentuais nunca usarão como denominador casos não observados sem declaração explícita.

## Supressão

Um indicador será suprimido quando:

- houver registros pendentes relevantes;
- a cobertura for insuficiente;
- o denominador for instável;
- a comparação atravessar schemas incompatíveis;
- a métrica permitir interpretação enganosa;
- o resultado expuser informação não publicável.

## Versionamento

Mudança em definição, fórmula, universo, classificação ou regra de inclusão gera nova versão do indicador. Resultados de versões diferentes não serão conectados como série histórica sem ponte metodológica documentada.
