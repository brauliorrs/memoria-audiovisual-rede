# Plataforma aberta de curadoria e acesso a memoria audiovisual em rede

Projeto inicial para mapear links institucionais da IASA, detectar presenca de video em plataformas parceiras e publicar relatorios exploratorios em uma interface Streamlit.

## Escopo atual

- Coleta da categoria `National archives` da IASA.
- Verifica a integridade do link institucional de cada arquivo listado.
- Visita sites parceiros com Playwright quando o link responde.
- Detecta links para plataformas de video e sinais de midia embutida.
- Gera relatorios em CSV, JSON, TXT e XLSX.
- Exibe uma visao geral e uma pagina por arquivo na app Streamlit.
- Organiza geograficamente os arquivos por pais e continente.
- Extrai automaticamente a rede de membros da CCAAA.
- Verifica a existencia de links de video nos sites dos membros e observadores da CCAAA.
- Inclui pipeline basico para GitHub Actions.

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
|       |-- config.py
|       |-- crawler.py
|       |-- excel_export.py
|       |-- pipeline.py
|       `-- reporting.py
|-- .github/
|   `-- workflows/
|       `-- pipeline.yml
|-- pyproject.toml
+-- requirements.txt
```

## Como executar localmente

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
playwright install
python scripts\run_pipeline.py
streamlit run app\streamlit_app.py
```

## Saidas esperadas

Os arquivos gerados ficam em `data/output/`:

- `iasa_v32_resumo_instituicoes.csv`
- `iasa_v32_links_video.csv`
- `iasa_v32_paginas_internas.csv`
- `iasa_v32_relatorio.json`
- `iasa_v32_relatorio.txt`
- `iasa_v32_relatorio.xlsx`
- `ccaaa_membros.csv`
- `ccaaa_membros.json`
- `ccaaa_resumo_sites.csv`
- `ccaaa_links_video.csv`
- `ccaaa_paginas_internas.csv`
- `ccaaa_relatorio.json`
- `ccaaa_relatorio.txt`

O arquivo `iasa_v32_resumo_instituicoes.csv` passa a incluir:

- `integrity_status`: `integro`, `acessivel`, `restrito`, `quebrado` ou `instavel`
- `slug`: identificador para abrir a pagina individual do arquivo

## Fluxo de produto

1. A pipeline coleta os arquivos listados na IASA.
2. Cada link institucional e testado e classificado por integridade.
3. Quando o link funciona, a coleta tenta localizar links de video e paginas internas relacionadas.
4. A app Streamlit oferece:
   - Visao geral da integridade dos links.
   - Pagina dedicada por arquivo com os links de video detectados.
   - Organizacao geografica dos arquivos com conteudo audiovisual.
   - Aba da rede CCAAA com status dos sites e links audiovisuais detectados.

## Proximos passos sugeridos

1. Publicar o repositorio no GitHub.
2. Configurar deploy da app Streamlit.
3. Adicionar persistencia em banco e historico de execucoes.
4. Expandir para novas categorias e novas estrategias de deteccao.
