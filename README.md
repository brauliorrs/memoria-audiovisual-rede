# Plataforma aberta de curadoria e acesso à memória audiovisual em rede

Projeto focado, nesta etapa, no Archives Portal Europe (APE) para:

- identificar instituições com conteúdo publicado no portal;
- capturar a `Webpage` externa de cada instituição a partir da ficha do APE;
- verificar a integridade desses sites;
- detectar links de vídeo e sinais de mídia embutida;
- enriquecer links de vídeo com título, assunto, descrição curta e data publicada, quando disponível;
- organizar os resultados em relatórios e em uma interface Streamlit.

## Escopo atual

- Coleta das instituições com conteúdo publicado no Archives Portal Europe.
- Leitura da ficha de cada instituição no APE para obter `Country`, `Webpage` e `Type of archive`.
- Verificação de integridade do site institucional externo.
- Detecção de links para plataformas de vídeo e sinais de mídia embutida.
- Enriquecimento de links de vídeo com metadados básicos da página do vídeo.
- Geração de relatórios em CSV, JSON, TXT e XLSX.
- Interface Streamlit com visão geral e página individual por instituição.

## Estrutura

```text
.
|-- app/
|   `-- streamlit_app.py
|-- data/
|   |-- input/
|   `-- output/
|-- scripts/
|   |-- build_ape_analytics.py
|   |-- check_ape_outputs.py
|   `-- run_pipeline.py
|-- src/
|   `-- memoria_audiovisual/
|       |-- analysis.py
|       |-- __init__.py
|       |-- ape.py
|       |-- ape_exports.py
|       |-- config.py
|       |-- crawler.py
|       |-- dashboard_data.py
|       |-- excel_export.py
|       |-- geography.py
|       |-- output_files.py
|       |-- pipeline.py
|       |-- snapshot_metadata.py
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
.\.venv\Scripts\python.exe scripts\build_ape_analytics.py
.\.venv\Scripts\python.exe scripts\check_ape_outputs.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

## Saídas esperadas

Os arquivos gerados ficam em `data/output/`:

- `ape_instituicoes.csv`
- `ape_resumo_instituicoes.csv`
- `ape_links_video.csv`
- `ape_paginas_internas.csv`
- `ape_resumo_instituicoes_analitico.csv`
- `ape_catalogo_videos_analitico.csv`
- `ape_resumo_disponibilidade.csv`
- `ape_subcategorias_disponibilidade.csv`
- `ape_resumo_visibilidade.csv`
- `ape_resumo_temas.csv`
- `ape_tema_pais.csv`
- `ape_resumo_tipos_arquivo.csv`
- `ape_tema_plataforma.csv`
- `ape_tema_tipo_arquivo.csv`
- `ape_visibilidade_tipo_arquivo.csv`
- `ape_snapshot_metadata.json`
- `ape_relatorio.json`
- `ape_relatorio.txt`
- `ape_relatorio.xlsx`

## Fluxo de produto

1. A pipeline coleta as instituições listadas no APE com conteúdo publicado.
2. A ficha de cada instituição no APE é lida para localizar `Country`, `Webpage` e `Type of archive`.
3. O site institucional externo é testado e classificado por integridade.
4. Quando o site responde, a coleta tenta localizar links de vídeo e páginas internas relacionadas.
5. Cada link de vídeo detectado pode ser enriquecido com título, assunto, descrição curta e data publicada.
6. A pipeline também gera saídas analíticas reaproveitáveis, com visibilidade metodológica do audiovisual e classificação temática dos vídeos detectados.
7. A app Streamlit oferece:
   - visão geral da integridade dos sites;
   - lista das instituições com links de vídeo detectados;
   - organização geográfica;
   - cruzamentos analíticos por tema, país e tipo de arquivo;
   - página individual por instituição.
8. Quando os CSVs analíticos já existem em `data/output/`, a app prioriza essas saídas prontas e usa cálculo local apenas como fallback.
9. A preparação dos dataframes do dashboard fica concentrada em `src/memoria_audiovisual/dashboard_data.py`, para reduzir lógica duplicada na interface.
10. Os nomes das saídas do APE ficam centralizados em `src/memoria_audiovisual/output_files.py`, para manter pipeline e interface sincronizadas.

## Qualidade do repositório

- `ape_snapshot_metadata.json` registra a data de corte da fonte, a atualização da camada analítica, as contagens principais e o inventário dos arquivos gerados.
- `python scripts/build_ape_analytics.py` reconstrói a camada analítica do APE a partir dos CSVs brutos já existentes em `data/output/`, sem rerodar a coleta.
- `python -m unittest discover -s tests -v` cobre a camada de carregamento do dashboard e o contrato dos arquivos de saída.
- O workflow `.github/workflows/quality.yml` executa compilação básica e testes automatizados em push para `main` e em pull requests.
- O workflow `.github/workflows/pipeline.yml` permanece dedicado à execução da coleta e publicação dos artefatos do APE.

## Próximo passo sugerido

Fechar a etapa APE com geografia consistente e metadados de vídeo confiáveis antes de expandir para outras redes e portais internacionais.
