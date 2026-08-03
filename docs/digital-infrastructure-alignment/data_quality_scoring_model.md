# Modelo de avaliação da qualidade

## Finalidade

Este documento descreve como as dimensões de qualidade serão avaliadas e agregadas sem converter incertezas metodológicas em precisão artificial.

## Unidade de avaliação

A avaliação pode incidir sobre:

- registro individual;
- relação entre entidades;
- conjunto de dados;
- snapshot;
- resultado de indicador;
- produto de publicação.

Cada avaliação deve apontar para uma versão específica do objeto.

## Pontuação por dimensão

| Valor | Estado | Interpretação |
|---|---|---|
| 0 | not_assessed | dimensão ainda não avaliada |
| 1 | insufficient | não atende aos requisitos mínimos |
| 2 | limited | utilizável apenas com restrições significativas |
| 3 | adequate | atende ao uso declarado com limitações documentadas |
| 4 | strong | evidência e processo robustos para o uso declarado |

## Regras mínimas por dimensão

### Completude

Considera campos obrigatórios, campos condicionais e variáveis relevantes ao tipo de objeto. Campos não aplicáveis não entram no denominador.

### Atualidade

Compara a última observação ou revisão com a janela de revalidação definida para a classe de variável.

### Consistência

Considera validações de schema, integridade referencial, coerência temporal e regras semânticas.

### Rastreabilidade

Exige vínculo reconstruível entre fonte, artefato, aquisição, transformação, versão, revisão e publicação.

### Força da evidência

Avalia adequação, autoridade, proximidade com o fato, persistência e triangulação da evidência.

### Cobertura

Compara unidades efetivamente avaliadas com o universo elegível e registra unidades não avaliáveis.

### Comparabilidade

Avalia estabilidade da definição, cobertura, método, schema, unidade de análise e janela temporal.

### Reprodutibilidade

Considera disponibilidade do método, parâmetros, versões, artefatos permitidos e dependências técnicas.

### Confiança curatorial

Deriva da decisão humana documentada e do grau de consenso, não de probabilidade produzida por modelo.

### Aptidão para uso

É atribuída separadamente para:

- `internal_exploration`;
- `restricted_research`;
- `scientific_analysis`;
- `public_record`;
- `public_indicator`;
- `longitudinal_comparison`.

## Agregação

Uma pontuação agregada poderá ser calculada apenas para triagem interna. Ela não substituirá as dimensões individuais.

Regras:

1. dimensões `0_not_assessed` não entram na média, mas reduzem a completude da avaliação;
2. cada tipo de objeto poderá possuir pesos versionados;
3. a média será acompanhada de cobertura da avaliação;
4. bloqueios críticos prevalecem sobre qualquer média;
5. a publicação deverá mostrar as dimensões relevantes, e não apenas um escore único.

## Faixas internas de referência

- `0.00–1.49`: qualidade insuficiente;
- `1.50–2.49`: qualidade limitada;
- `2.50–3.24`: qualidade adequada;
- `3.25–4.00`: qualidade forte.

Essas faixas são descritivas e não concedem maturidade automaticamente.

## Maturidade

A maturidade é decidida por regras de passagem. Exemplo:

- `M2_structured`: schema válido, identificadores estáveis e proveniência mínima;
- `M3_reviewed`: revisão concluída e ausência de erro crítico aberto;
- `M4_research_ready`: consistência, rastreabilidade e evidência com valor mínimo 3;
- `M5_publication_ready`: requisitos anteriores, cobertura adequada e aprovação de publicação;
- `M6_longitudinal_ready`: comparabilidade mínima 3 e vínculo entre snapshots compatíveis.

## Reavaliação

A avaliação deverá ser refeita quando ocorrer:

- nova observação;
- mudança de evidência;
- revisão curatorial;
- migração de schema;
- alteração de cobertura;
- abertura ou fechamento de snapshot;
- mudança de finalidade de uso;
- expiração da janela de revalidação.
