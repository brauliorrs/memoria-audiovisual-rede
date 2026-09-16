# Alinhamento dos manifestos de dependências

## Problema reproduzido

`pyproject.toml` declara `jsonschema>=4.23` como dependência direta do projeto e o código importa `jsonschema` diretamente em `src/memoria_audiovisual/statetech/validation.py`. Até esta correção, `requirements.txt` não declarava `jsonschema`.

Uma instalação baseada apenas em `requirements.txt` podia obter `jsonschema` incidentalmente pela cadeia `streamlit -> altair -> jsonschema`, mas essa dependência transitiva não representa o contrato direto do projeto nem impõe o piso `>=4.23` definido em `pyproject.toml`.

## Correção

- `requirements.txt` passa a declarar `jsonschema==4.26.0` diretamente;
- `scripts/check_dependency_manifests.py` verifica, sem dependências externas, que toda dependência direta de `pyproject.toml` também aparece em `requirements.txt`;
- `tests/test_dependency_manifest_alignment.py` cobre a mesma invariável na suíte unitária;
- o workflow `Quality Checks` executa a verificação antes da instalação das dependências.

A verificação é deliberadamente unidirecional: `requirements.txt` pode conter dependências adicionais de runtime/deploy, mas não pode omitir dependências diretas do projeto.
