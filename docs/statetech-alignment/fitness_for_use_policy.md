# Política de aptidão para uso

## Objetivo

Definir para quais finalidades um objeto de dados pode ser utilizado, considerando qualidade, maturidade, cobertura, sensibilidade e comparabilidade.

A aptidão é específica ao uso. Um registro pode ser adequado para exploração interna e inadequado para publicação pública ou comparação longitudinal.

## Classes de uso

### `internal_exploration`

Uso exploratório por equipe autorizada. Admite registros preliminares, desde que identificados como não validados.

### `restricted_research`

Uso em ambiente de pesquisa controlado, com acesso limitado, documentação de limitações e proibição de divulgação de afirmações não confirmadas.

### `scientific_analysis`

Uso em análise acadêmica, tabelas e resultados de pesquisa. Exige maturidade mínima `M4_research_ready`, proveniência adequada e método documentado.

### `public_record`

Publicação de registros desagregados. Exige `M5_publication_ready`, revisão curatorial concluída, licença compatível e ausência de bloqueios de sensibilidade.

### `public_indicator`

Uso em indicadores, gráficos, API ou painel público. Exige definição versionada, denominador estável, cobertura mínima e política de supressão satisfeita.

### `longitudinal_comparison`

Uso para afirmar mudança ao longo do tempo. Exige `M6_longitudinal_ready`, snapshots comparáveis e classificação explícita da origem da mudança.

## Decisão

Cada avaliação poderá produzir, para cada classe:

- `approved`;
- `approved_with_limits`;
- `not_approved`;
- `not_assessed`.

A decisão deve registrar justificativa, limitações, prazo de validade e responsável.

## Critérios transversais

A aptidão considera:

- validade do schema;
- integridade relacional;
- maturidade;
- atualidade;
- força da evidência;
- cobertura;
- sensibilidade;
- licença e direitos;
- risco reputacional;
- comparabilidade;
- aprovação curatorial.

## Restrições automáticas

Não poderão receber aptidão pública:

- registros pendentes ou inconclusivos apresentados como fatos;
- evidências protegidas ou de acesso restrito sem autorização;
- alegações sensíveis sem dupla revisão;
- sistemas de IA inferidos apenas por linguagem promocional;
- fornecedores ou contratos inferidos apenas por detecção técnica;
- resultados com cobertura abaixo do mínimo definido;
- dados cujo licenciamento impeça redistribuição.

## Limitações publicáveis

Quando o uso for `approved_with_limits`, o produto deverá expor as restrições, por exemplo:

- cobertura parcial;
- fonte indireta;
- período incompleto;
- comparabilidade limitada;
- revisão desatualizada;
- ausência de triangulação;
- universo não mensurável com precisão.

## Revogação

A aptidão poderá ser revogada por:

- nova evidência contraditória;
- expiração da revalidação;
- erro de entidade;
- mudança de licença;
- conflito de interesse não declarado;
- migração metodológica incompatível;
- falha de integridade descoberta posteriormente.

A revogação não apagará a decisão anterior; criará novo evento e nova versão de avaliação.
