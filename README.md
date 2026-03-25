# Plataforma aberta de curadoria e acesso a memoria audiovisual em rede

Projeto focado no Archives Portal Europe (APE) para:

- identificar instituicoes com conteudo publicado no portal;
- capturar a `Webpage` externa de cada instituicao a partir da ficha do APE;
- verificar a integridade desses sites;
- detectar links de video e sinais de midia embutida;
- organizar os resultados em relatorios e em uma interface Streamlit.

## Escopo atual

- Coleta das instituicoes com conteudo publicado no Archives Portal Europe.
- Leitura da ficha de cada instituicao no APE para obter `Country`, `Webpage` e `Type of archive`.
- Verificacao de integridade do site institucional externo.
- Deteccao de links para plataformas de video e sinais de midia embutida.
- Geracao de relatorios em CSV, JSON, TXT e XLSX.
- Interface Streamlit com visao geral e pagina individual por instituicao.

## Estrutura

```text
.
|-- app/
|   `-- streamlit_app.py
|-- data/
|   |-- input/
|   `-- output/
|-- scripts/
|   `-- run_pipeline.py
|-- src/
|   `-- memoria_audiovisual/
|       |-- __init__.py
|       |-- ape.py
|       |-- config.py
|       |-- crawler.py
|       |-- excel_export.py
|       |-- geography.py
|       |-- pipeline.py
|       `-- reporting.py
|-- pyproject.toml
+-- requirements.txt
```

## Como executar localmente

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install
.\.venv\Scripts\python.exe scripts\run_pipeline.py
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

## Saidas esperadas

Os arquivos gerados ficam em `data/output/`:

- `ape_instituicoes.csv`
- `ape_resumo_instituicoes.csv`
- `ape_links_video.csv`
- `ape_paginas_internas.csv`
- `ape_relatorio.json`
- `ape_relatorio.txt`
- `ape_relatorio.xlsx`

## Fluxo de produto

1. A pipeline coleta as instituicoes listadas no APE com conteudo publicado.
2. A ficha de cada instituicao no APE e lida para localizar a `Webpage` externa.
3. O site institucional externo e testado e classificado por integridade.
4. Quando o site responde, a coleta tenta localizar links de video e paginas internas relacionadas.
5. A app Streamlit oferece:
   - visao geral da integridade dos sites;
   - lista das instituicoes com links de video detectados;
   - organizacao geografica;
   - pagina individual por instituicao.

## Proximo passo sugerido

Expandir a coleta da lista `instituicoes com conteudo publicado` para o universo completo de instituicoes representadas no APE.
