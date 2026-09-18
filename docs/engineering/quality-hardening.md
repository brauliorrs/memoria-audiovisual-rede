# Quality Hardening antes da Onda 2B

## Objetivo

Transformar as práticas de revisão já adotadas no projeto em verificações
reprodutíveis do próprio repositório, sem alterar lógica científica, IDs,
schemas, freezes, artefatos históricos ou decisões curatoriais.

## Escopo desta etapa

- ferramentas de desenvolvimento versionadas no `pyproject.toml`;
- Ruff para erros fatais em todo o pacote canônico e regras de estilo no recorte 2A;
- Ruff formatter em modo `--check`, sem reformatação automática do legado;
- mypy gradual apenas nos módulos introduzidos pela Onda 2A;
- coverage com branch coverage sobre os módulos 2A;
- linha de base observada de 90,7% e piso de CI fixado em 90%;
- permissões `contents: read` explícitas nos workflows;
- GitHub Actions fixadas por SHA imutável, com versão documentada em comentário;
- cache de dependências do pip nos workflows;
- cancelamento de execuções obsoletas apenas no workflow rápido de Quality Checks.

## Regras de não regressão

1. Ferramentas de qualidade não podem alterar resultados científicos.
2. Não se reescreve código histórico em massa para satisfazer formatter/linter.
3. Não se reduz ou remove teste para obter CI verde.
4. O piso de cobertura é 90%, derivado da linha de base observada de 90,7%;
   qualquer redução abaixo desse piso faz o CI falhar.
5. Type checking será expandido progressivamente conforme cada onda entra na
   `main`.

## Proteção da main

O repositório deve exigir PR e Quality Checks bem-sucedido antes de merge. Essa
proteção é configuração administrativa do GitHub e deve ser aplicada somente
depois de o novo workflow estar verde, para evitar bloquear a própria migração.
