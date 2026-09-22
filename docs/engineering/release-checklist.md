# Checklist de release

Use este checklist para qualquer `vX.Y.Z`.

## 1. Preparar o candidato

- [ ] A versão pretendida está definida no `pyproject.toml`.
- [ ] O `CHANGELOG.md` descreve as mudanças desde a release anterior.
- [ ] O SHA candidato da `main` foi registrado.
- [ ] Não existe mudança científica congelada que esteja sendo reclassificada apenas
      por causa da release de software.
- [ ] Alterações de schema possuem `schema_version` próprio quando necessário.
- [ ] O snapshot científico, quando houver, possui identificador próprio.

## 2. Verificar qualidade

No commit exato candidato:

- [ ] `Quality Checks` terminou com `success`.
- [ ] manifesto de dependências está alinhado;
- [ ] Ruff passou;
- [ ] formatter check passou;
- [ ] mypy passou no escopo tipado;
- [ ] cobertura permaneceu no piso configurado ou acima dele;
- [ ] suíte completa de testes passou;
- [ ] testes específicos dos contratos relevantes passaram;
- [ ] `check_deployment_ready.py` aprovou o snapshot de implantação.

Se a release modificar o pipeline de coleta:

- [ ] a execução controlada do `Pipeline APE` foi verificada;
- [ ] falhas causadas por dependências externas foram distinguidas de regressões de
      software.

## 3. Verificar governança

- [ ] O estado da branch protection da `main` foi verificado ou a exceção foi
      explicitamente registrada.
- [ ] O candidato entrou por PR, salvo exceção documentada.
- [ ] Não há PR ou commit posterior que torne o SHA candidato obsoleto.
- [ ] A versão do pacote, changelog e release notes concordam entre si.

## 4. Publicar

- [ ] Converter `[Unreleased]` em `[X.Y.Z] - YYYY-MM-DD`.
- [ ] Executar novamente os gates após qualquer mudança feita para preparar a release.
- [ ] Criar tag `vX.Y.Z` apontando para o SHA aprovado.
- [ ] Confirmar que a tag resolve para o commit esperado.
- [ ] Criar a GitHub Release a partir da tag.
- [ ] Registrar nas release notes: escopo, mudanças, compatibilidade, limitações,
      commit e relação com snapshots/protocolos científicos aplicáveis.

## 5. Pós-release

- [ ] Confirmar que a GitHub Release está acessível e aponta para a tag correta.
- [ ] Confirmar que a aplicação pública continua operacional quando aplicável.
- [ ] Atualizar a memória de desenvolvimento com versão, SHA, gates e próxima ação.
- [ ] Abrir novamente a seção `[Unreleased]` para o próximo ciclo.
