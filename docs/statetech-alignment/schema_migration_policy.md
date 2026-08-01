# Política de migração de schemas

## Objetivo

Garantir que a evolução do modelo de dados não apague estados anteriores nem produza falsas mudanças históricas.

## Versionamento

Os schemas seguem versionamento semântico:

- `major`: mudança incompatível de significado, estrutura ou cardinalidade;
- `minor`: inclusão compatível de campos ou valores controlados;
- `patch`: correção documental ou restrição sem alteração substantiva.

## Tipos de migração

- `additive`: inclui campo opcional ou nova entidade;
- `transformative`: converte representação mantendo equivalência;
- `semantic`: altera definição ou alcance de variável;
- `split`: divide variável ou entidade em múltiplas unidades;
- `merge`: combina variáveis ou entidades;
- `deprecation`: retira campo gradualmente;
- `corrective`: corrige erro do modelo anterior.

## Requisitos

Toda migração deve registrar:

- `migration_id`;
- schema de origem e destino;
- tipo de migração;
- campos afetados;
- regra de transformação;
- reversibilidade;
- perdas conhecidas;
- impacto na comparabilidade;
- agente responsável;
- data de aprovação;
- evidência de revisão.

## Preservação

- dados originais permanecem associados ao schema de origem;
- a versão migrada é um novo artefato derivado;
- nenhum snapshot fechado é alterado;
- hashes dos artefatos anterior e posterior são preservados;
- migração não é classificada como mudança empírica.

## Compatibilidade longitudinal

Cada variável migrada deve receber uma classificação:

- `fully_comparable`;
- `comparable_with_mapping`;
- `partially_comparable`;
- `not_comparable`.

Quando houver mapeamento, este deve ser versionado e publicado junto da comparação.

## Mudanças semânticas

Alterações de definição exigem versão major. Exemplos:

- mudança do conceito de API aberta;
- ampliação do que conta como fornecedor;
- alteração da unidade de análise de instituição para serviço;
- revisão do significado de risco alto.

## Campos descontinuados

Campos descontinuados passam por:

1. marcação como `deprecated`;
2. período de coexistência;
3. documentação do substituto;
4. migração dos registros quando possível;
5. retirada apenas em versão major.

## Produto futuro

```text
data/migrations/{migration_id}/migration_manifest.json
data/migrations/{migration_id}/field_mapping.csv
```
