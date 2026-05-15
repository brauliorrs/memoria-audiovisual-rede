# Plataforma aberta de curadoria e acesso à memória audiovisual em rede

Projeto focado, nesta etapa, no fechamento europeu do observatório a partir do Archives Portal Europe (APE), do EUscreen, do PARES e do Institut national de l'audiovisuel (INA) para:

- identificar instituições com conteúdo publicado no portal;
- capturar a `Webpage` externa de cada instituição a partir da ficha do APE;
- verificar a integridade desses sites;
- detectar links de vídeo e sinais de mídia embutida;
- enriquecer links de vídeo com título, assunto, descrição curta e data publicada, quando disponível;
- organizar os resultados em relatórios e em uma interface Streamlit.

Ao mesmo tempo, o projeto se assume como um **organismo agregador mundial em construção**:

- mapeia primeiro agregadores arquivísticos;
- incorpora depois arquivos e instituições não cobertos por esses agregadores;
- mantém linhas do tempo para que o crescimento, a retração e possíveis extinções digitais fiquem historicamente rastreáveis.
- executa um ciclo mensal automatizado para atualizar os corpora ativos do organismo.

## Eixo acadêmico

O observatório integra a formulação de um projeto de pós-doutorado a ser submetido à Universidade de Valência, no âmbito do **Communication and Media Culture History Research Group**.

A pergunta orientadora é: **como as plataformas digitais reorganizam a circulação territorial e cultural do audiovisual contemporâneo?**

As plataformas digitais não eliminam o território; elas reorganizam o território. No audiovisual contemporâneo, a circulação deixa de depender apenas do lugar físico do arquivo, da cinemateca, da emissora ou da instituição custodial, e passa a depender de uma combinação entre infraestrutura técnica, políticas de acesso e licenciamento, idioma dos metadados, formatos de indexação, regimes de visibilidade e dependência de plataformas externas.

A hipótese de trabalho é que a circulação audiovisual contemporânea é cada vez menos determinada apenas pela localização física dos acervos e cada vez mais pela capacidade das instituições e plataformas de tornar esses acervos detectáveis, descritos, interoperáveis e acessíveis em redes digitais transnacionais.

No observatório, essa pergunta é operacionalizada por variáveis como hospedagem, indexação, descrição, idioma, regime de acesso, plataforma, visibilidade pública e escala territorial.

## Escopo atual

- `Corpus 1` — `APE`: agregador arquivístico continental europeu, composto por arquivos gerais com conteúdo publicado no Archives Portal Europe.
- `Corpus 2` — `EUscreen`: agregador audiovisual europeu, usado para observar circulação transnacional em uma plataforma temática especializada.
- `Corpus 3` — `PARES`: agregador nacional espanhol em modo experimental, incorporado após avaliação técnica da busca pública. Neste corpus, o resultado detectado pode ser `registro descritivo recuperado` ou `objeto digital detectado`.
- `Corpus 4` — `INA`: corpus especializado em audiovisual, estruturado a partir do Institut national de l'audiovisuel.
- Verificação de integridade do site institucional externo de cada corpus.
- Detecção de links para plataformas de vídeo e sinais de mídia embutida.
- Enriquecimento de links de vídeo com metadados básicos da página do vídeo.
- Geração de relatórios em CSV, JSON, TXT e XLSX para cada corpus.
- Interface Streamlit organizada por corpus, com abas próprias para `APE`, `EUscreen`, `PARES` e `INA`, além de uma visão geral comparativa do observatório.

## Estratégia de expansão

O crescimento do observatório segue uma regra metodológica explícita:

1. `Etapa 1` — incorporar primeiro **agregadores continentais ou supranacionais**.
2. `Etapa 2` — incorporar depois **arquivos e instituições não cobertos por esses agregadores**.

Essa política busca:

- ampliar cobertura de forma mais rápida;
- manter comparabilidade entre unidades do mesmo tipo;
- evitar misturar, sem mediação, agregadores e instituições custodiais;
- fortalecer o rigor científico da expansão do acervo.

Regra audiovisual:

- fontes gerais podem entrar como **fontes de pesquisa** mesmo quando retornam `zero` audiovisual;
- nesses casos, o retorno zero não elimina a fonte do organismo, mas passa a compor a análise sobre visibilidade, digitalização e acesso público;
- arquivos explicitamente audiovisuais que retornem `zero` demandam leitura metodológica mais forte e aparecem como anomalia relevante.

No estado atual:

- `APE` está enquadrado como `agregador arquivístico`;
- `EUscreen` está enquadrado como `agregador audiovisual europeu`;
- `PARES` está enquadrado como `agregador nacional europeu em modo experimental`;
- `INA` está enquadrado como `arquivo/instituição arquivística`;
- a interface permite trabalhar com o todo, por categoria analítica e por corpus individual, sem fundir esses níveis de análise.

## Linha do tempo e possíveis extinções

Cada atualização do organismo registra uma memória histórica da rodada:

- linha do tempo do corpus;
- linha do tempo institucional;
- quadro de sinais de possível extinção.

Isso permite identificar, entre outras situações:

- arquivos ou instituições que desaparecem de uma fonte em rodadas posteriores;
- indisponibilidade digital reincidente;
- perda de evidência pública detectável de audiovisual.

O princípio é simples: o observatório não deve apenas mostrar o estado atual do acervo, mas também preservar sua história de aparecimento, retração, ausência e transformação.

## Ciclo mensal do organismo

O organismo opera com uma cadência mensal de atualização dos corpora ativos.

Esse ciclo:

- roda primeiro os corpora ativos, respeitando a separação entre agregadores e arquivos;
- atualiza os metadados de cada rodada;
- regrava as linhas do tempo do corpus e das instituições;
- produz um manifesto do ciclo mensal do organismo;
- valida o resultado antes de disponibilizar os artefatos.

Scripts principais:

- `python scripts/run_observatory_cycle.py`
- `python scripts/run_observatory_cycle.py --corpus ina`
- `python scripts/evaluate_european_aggregators.py`
- `python scripts/check_observatory_cycle.py`

Artefatos globais do organismo:

- `data/output/observatorio_ciclo_mensal.json`
- `data/output/observatorio_corpora_ativos.csv`
- `data/output/observatorio_linha_do_tempo_ciclos.csv`
- `data/output/observatorio_resultados_ciclos.csv`
- `data/output/observatorio_candidatos_descoberta.csv`
- `data/output/observatorio_fila_expansao.csv`
- `data/output/observatorio_resumo_fila_expansao.csv`
- `data/output/observatorio_rotas_acesso_agregadores_europa.csv`
- `data/output/observatorio_avaliacao_agregadores_europa.csv`
- `data/output/observatorio_probes_agregadores_europa.csv`
- `data/output/observatorio_protocolos_agregadores_europa.csv`
- `data/output/observatorio_resumo_agregadores_europa.csv`

## Fila automática de expansão

O organismo também materializa uma fila automática de expansão, regenerada a cada ciclo mensal.

Essa fila:

- registra unidades já incorporadas;
- preserva uma linha de base de candidatos metodologicamente aderentes;
- aplica decisão automática por regra pública;
- prioriza o fechamento da Europa antes da abertura sistemática de outros continentes;
- trata o `APE` como base agregadora continental europeia;
- considera agregadores audiovisuais europeus, como `EUscreen`, como prioridade de fechamento regional;
- preserva instituições europeias relevantes como lacunas ou exceções da base Europa, quando não forem suficientemente cobertas pelo agregador;
- reserva instituições da `Etapa 2` para o momento posterior à cobertura agregadora.

Decisões automáticas atuais:

- `ja_incorporado`
- `fechamento_europa_agregador_audiovisual`
- `fechamento_europa_agregador_nacional`
- `prioridade_imediata_etapa_1`
- `lacuna_ou_excecao_na_base_europa`
- `monitoramento_estrategico`
- `aguarda_etapa_2`
- `coberto_por_agregador_ativo`
- `fora_do_recorte_atual`

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
|   |-- build_euscreen_analytics.py
|   |-- build_ina_analytics.py
|   |-- build_pares_analytics.py
|   |-- check_ape_outputs.py
|   |-- check_euscreen_outputs.py
|   |-- check_ina_outputs.py
|   |-- check_observatory_cycle.py
|   |-- check_pares_outputs.py
|   |-- evaluate_european_aggregators.py
|   |-- run_euscreen_pipeline.py
|   |-- run_ina_pipeline.py
|   |-- run_observatory_cycle.py
|   |-- run_pares_pipeline.py
|   `-- run_pipeline.py
|-- src/
|   `-- memoria_audiovisual/
|       |-- analysis_exports.py
|       |-- analysis.py
|       |-- __init__.py
|       |-- ape.py
|       |-- ape_exports.py
|       |-- config.py
|       |-- corpora.py
|       |-- crawler.py
|       |-- dashboard_data.py
|       |-- excel_export.py
|       |-- european_aggregators.py
|       |-- euscreen.py
|       |-- euscreen_exports.py
|       |-- geography.py
|       |-- ina.py
|       |-- ina_exports.py
|       |-- output_files.py
|       |-- pares.py
|       |-- pares_exports.py
|       |-- pipeline.py
|       |-- snapshot_metadata.py
|       |-- organism.py
|       |-- timeline.py
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
.\.venv\Scripts\python.exe scripts\run_euscreen_pipeline.py
.\\.venv\Scripts\python.exe scripts\run_pares_pipeline.py
.\\.venv\Scripts\python.exe scripts\run_ina_pipeline.py
.\.venv\Scripts\python.exe scripts\build_ape_analytics.py
.\\.venv\Scripts\python.exe scripts\build_euscreen_analytics.py
.\\.venv\Scripts\python.exe scripts\build_pares_analytics.py
.\\.venv\Scripts\python.exe scripts\build_ina_analytics.py
.\.venv\Scripts\python.exe scripts\check_ape_outputs.py
.\\.venv\Scripts\python.exe scripts\check_euscreen_outputs.py
.\\.venv\Scripts\python.exe scripts\check_pares_outputs.py
.\\.venv\Scripts\python.exe scripts\check_ina_outputs.py
.\.venv\Scripts\python.exe scripts\evaluate_european_aggregators.py
.\.venv\Scripts\python.exe scripts\run_observatory_cycle.py
.\.venv\Scripts\python.exe scripts\check_observatory_cycle.py
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
- `ape_resumo_modalidades_acesso.csv`
- `ape_resumo_regimes_acesso.csv`
- `ape_resumo_temas.csv`
- `ape_tema_pais.csv`
- `ape_resumo_tipos_arquivo.csv`
- `ape_tema_plataforma.csv`
- `ape_tema_tipo_arquivo.csv`
- `ape_visibilidade_tipo_arquivo.csv`
- `ape_linha_do_tempo_corpus.csv`
- `ape_linha_do_tempo_instituicoes.csv`
- `ape_sinais_possivel_extincao.csv`
- `ape_snapshot_metadata.json`
- `ape_relatorio.json`
- `ape_relatorio.txt`
- `ape_relatorio.xlsx`

O `EUscreen`, o `PARES` e o `INA` seguem a mesma convenção de nomes, trocando o prefixo `ape_` por `euscreen_`, `pares_` ou `ina_`, por exemplo:

- `euscreen_instituicoes.csv`
- `euscreen_resumo_instituicoes.csv`
- `euscreen_links_video.csv`
- `euscreen_paginas_internas.csv`
- `euscreen_resumo_instituicoes_analitico.csv`
- `euscreen_catalogo_videos_analitico.csv`
- `euscreen_resumo_modalidades_acesso.csv`
- `euscreen_resumo_regimes_acesso.csv`
- `euscreen_linha_do_tempo_corpus.csv`
- `euscreen_linha_do_tempo_instituicoes.csv`
- `euscreen_sinais_possivel_extincao.csv`
- `euscreen_snapshot_metadata.json`
- `euscreen_relatorio.xlsx`

- `pares_instituicoes.csv`
- `pares_resumo_instituicoes.csv`
- `pares_links_video.csv`
- `pares_paginas_internas.csv`
- `pares_resumo_instituicoes_analitico.csv`
- `pares_catalogo_videos_analitico.csv`
- `pares_resumo_modalidades_acesso.csv`
- `pares_resumo_regimes_acesso.csv`
- `pares_linha_do_tempo_corpus.csv`
- `pares_linha_do_tempo_instituicoes.csv`
- `pares_sinais_possivel_extincao.csv`
- `pares_snapshot_metadata.json`
- `pares_relatorio.xlsx`

- `ina_instituicoes.csv`
- `ina_resumo_instituicoes.csv`
- `ina_links_video.csv`
- `ina_paginas_internas.csv`
- `ina_resumo_instituicoes_analitico.csv`
- `ina_catalogo_videos_analitico.csv`
- `ina_resumo_modalidades_acesso.csv`
- `ina_resumo_regimes_acesso.csv`
- `ina_linha_do_tempo_corpus.csv`
- `ina_linha_do_tempo_instituicoes.csv`
- `ina_sinais_possivel_extincao.csv`
- `ina_snapshot_metadata.json`
- `ina_relatorio.xlsx`

## Fluxo de produto

1. A pipeline coleta as instituições listadas no APE com conteúdo publicado.
2. A ficha de cada instituição no APE é lida para localizar `Country`, `Webpage` e `Type of archive`.
3. O site institucional externo é testado e classificado por integridade.
4. Quando o site responde, a coleta tenta localizar links de vídeo e páginas internas relacionadas.
5. Cada link de vídeo detectado pode ser enriquecido com título, assunto, descrição curta e data publicada.
6. A pipeline também gera saídas analíticas reaproveitáveis, com visibilidade metodológica do audiovisual e classificação temática dos vídeos detectados.
7. Essa camada analítica também passa a distinguir modalidades de acesso detectadas e regimes institucionais de acesso audiovisual detectável.
8. A app Streamlit oferece:
   - visão geral comparativa do observatório;
   - abas próprias para cada corpus, preservando sua autonomia analítica;
   - visão geral da integridade dos sites;
   - lista das instituições com links de vídeo detectados;
   - organização geográfica;
   - cruzamentos analíticos por tema, país, tipo de arquivo e regime de acesso;
   - página individual por instituição;
   - quadros históricos para acompanhar a linha do tempo das fontes e dos sinais de possível extinção.
9. Quando os CSVs analíticos já existem em `data/output/`, a app prioriza essas saídas prontas e usa cálculo local apenas como fallback.
10. A preparação dos dataframes do dashboard fica concentrada em `src/memoria_audiovisual/dashboard_data.py`, para reduzir lógica duplicada na interface.
11. Os nomes das saídas do APE, do EUscreen, do PARES e do INA ficam centralizados em `src/memoria_audiovisual/output_files.py`, para manter pipeline e interface sincronizadas.
12. O ciclo mensal do organismo fica centralizado em `scripts/run_observatory_cycle.py`, com manifesto global em `data/output/observatorio_ciclo_mensal.json`.
13. A avaliação europeia materializa rotas oficiais candidatas e uma matriz de protocolos para diferenciar agregadores prontos para pipeline experimental, fontes que exigem rota técnica estável e fontes que permanecem em monitoramento.

## Qualidade do repositório

- `ape_snapshot_metadata.json` registra a data de corte da fonte, a atualização da camada analítica, as contagens principais e o inventário dos arquivos gerados.
- `python scripts/build_ape_analytics.py` reconstrói a camada analítica do APE a partir dos CSVs brutos já existentes em `data/output/`, sem rerodar a coleta.
- `python -m unittest discover -s tests -v` cobre a camada de carregamento do dashboard e o contrato dos arquivos de saída.
- O workflow `.github/workflows/quality.yml` executa compilação básica e testes automatizados em push para `main` e em pull requests.
- O workflow `.github/workflows/pipeline.yml` permanece dedicado à execução da coleta e publicação dos artefatos do APE.
- O workflow `.github/workflows/organism-monthly.yml` executa o ciclo mensal automatizado do organismo.

## Próximo passo sugerido

Validar o corpus experimental `PARES` em mais rodadas e usar a matriz de protocolos para resolver `Archives Hub` e `FranceArchives` antes de abrir sistematicamente a América do Sul.
