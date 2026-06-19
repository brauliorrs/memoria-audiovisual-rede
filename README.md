# Memória Audiovisual em Rede

**Observatório digital para mapear, monitorar e analisar a presença pública de acervos audiovisuais em plataformas, arquivos e agregadores digitais.**

Este projeto combina coleta automatizada, curadoria metodológica, geração de indicadores e visualização em Streamlit para estudar como acervos audiovisuais circulam em ambientes digitais, especialmente quando dependem de plataformas, agregadores, catálogos públicos, APIs, metadados e sistemas institucionais de acesso.

O objetivo não é apenas localizar vídeos ou registros audiovisuais, mas compreender como a memória audiovisual se torna visível, acessível, indexável, instável ou ausente nas redes digitais contemporâneas.

---

## Resumo executivo

O **Memória Audiovisual em Rede** é um observatório em Python voltado à análise da circulação digital de acervos audiovisuais.

O projeto coleta e organiza dados de agregadores e instituições arquivísticas, verifica integridade de sites, identifica sinais audiovisuais, detecta links de vídeo, registra limitações técnicas e produz saídas analíticas em formatos abertos.

**Entrega principal:** pipeline de observação + relatórios estruturados + dashboard Streamlit
**Stack:** Python, pandas, Streamlit, Playwright, CSV, JSON, XLSX
**Uso:** pesquisa acadêmica, memória audiovisual, comunicação digital, políticas de acesso e análise de plataformas
**Status:** MVP em desenvolvimento, com corpora ativos e expansão metodológica controlada

---

## Problema

Grande parte dos acervos audiovisuais públicos não circula apenas por arquivos físicos ou catálogos institucionais. Sua visibilidade passa a depender de fatores como:

* existência de páginas públicas;
* qualidade dos metadados;
* idioma da descrição;
* presença ou ausência de player;
* uso de plataformas externas;
* estabilidade de sites institucionais;
* indexação em agregadores;
* políticas de acesso e licenciamento;
* rotas técnicas de coleta, busca ou API.

Isso cria um problema de pesquisa: **a memória audiovisual pode existir institucionalmente, mas permanecer pouco visível ou pouco acessível digitalmente.**

---

## Pergunta orientadora

**Como as plataformas digitais reorganizam a circulação territorial e cultural do audiovisual contemporâneo?**

A hipótese de trabalho é que a circulação audiovisual contemporânea é cada vez menos determinada apenas pela localização física dos acervos e cada vez mais pela capacidade das instituições e plataformas de tornar esses acervos detectáveis, descritos, interoperáveis e acessíveis em redes digitais transnacionais.

---

## Solução

O projeto propõe um observatório digital que:

1. identifica agregadores, arquivos e instituições com potencial audiovisual;
2. executa coletas controladas em fontes públicas;
3. separa agregadores, arquivos custodiais e unidades apenas protocoladas;
4. registra sinais de acesso, visibilidade, instabilidade e ausência;
5. gera relatórios técnicos e analíticos;
6. mantém linhas do tempo dos corpora e das instituições;
7. disponibiliza os dados em uma interface Streamlit.

---

## Escopo atual

O observatório trabalha com corpora ativos e unidades protocoladas.

### Corpora ativos

| Corpus    | Fonte                                                    | Tipo                                               |
| --------- | -------------------------------------------------------- | -------------------------------------------------- |
| APE       | Archives Portal Europe                                   | Agregador arquivístico europeu                     |
| EUscreen  | EUscreen                                                 | Agregador audiovisual europeu                      |
| EFG       | European Film Gateway                                    | Agregador audiovisual especializado em cinema      |
| Europeana | Europeana                                                | Agregador cultural europeu com recorte audiovisual |
| PARES     | Portal de Archivos Españoles                             | Agregador nacional espanhol                        |
| PPA       | Portal Português de Arquivos                             | Agregador nacional português                       |
| INA       | Institut national de l'audiovisuel                       | Instituição audiovisual                            |
| ARCHIPOP  | ARCHIPOP                                                 | Arquivo audiovisual institucional                  |
| AAMOD     | Archivio Audiovisivo del Movimento Operaio e Democratico | Arquivo audiovisual institucional                  |
| SFA       | Slovenski filmski arhiv                                  | Arquivo fílmico institucional                      |
| ANF       | Arhiva Națională de Filme / Cinemateca Română            | Arquivo fílmico institucional                      |
| AQSHF     | Albanian National Film Archive                           | Arquivo fílmico institucional                      |
| AAPB      | American Archive of Public Broadcasting                  | Agregador audiovisual norte-americano              |

### Unidades protocoladas ou monitoradas

Algumas fontes são mantidas no radar metodológico, mas ainda não entram como corpus ativo por ausência de rota pública estável, ausência de evidência audiovisual coletável ou inadequação ao recorte atual.

Entre elas:

* ArchiveGrid
* Archives Hub
* FranceArchives
* Iberarchivos
* Ad Libitum Workshop
* FilmArchives Online
* EFG1914
* VICTOR-E
* ACE
* INEDITS
* EBU
* European Audiovisual Observatory
* Archivportal-D

---

## Estratégia metodológica

A expansão do observatório segue uma regra em duas etapas:

1. **Agregadores primeiro**
   Prioriza agregadores continentais, supranacionais ou nacionais, pois eles permitem mapear grandes superfícies institucionais com maior comparabilidade.

2. **Instituições depois**
   Incorpora arquivos e instituições individuais quando há lacunas relevantes, exceções metodológicas ou rotas públicas de coleta suficientemente estáveis.

Essa separação evita misturar, sem mediação, agregadores e instituições custodiais.

---

## Regra audiovisual

A presença ou ausência de audiovisual é interpretada metodologicamente.

* Fontes gerais podem entrar como fontes de pesquisa mesmo quando retornam zero evidência audiovisual.
* Arquivos explicitamente audiovisuais que retornam zero são tratados como anomalia relevante.
* Fontes apenas documentais, sem evidência de imagem em movimento, ficam fora do corpus audiovisual ativo.
* Registros descritivos, players públicos, objetos digitais e links externos são classificados separadamente.

O objetivo é não confundir **existência institucional do acervo** com **visibilidade pública digital do audiovisual**.

---

## Completude da coleta

Nenhum corpus parcial é apresentado como catálogo total.

Cada corpus declara:

* completude da coleta;
* critério de seleção;
* limite técnico;
* nota metodológica;
* tipo de evidência encontrada;
* grau de estabilidade da rota usada.

Assim, números como registros por termo, páginas coletadas ou vídeos detectados representam uma rodada reprodutível de observação pública, não necessariamente o total do acervo.

---

## Linha do tempo e memória das rodadas

O observatório registra a história das coletas para preservar não apenas o estado atual, mas também transformações e perdas de visibilidade.

Cada atualização pode registrar:

* linha do tempo do corpus;
* linha do tempo institucional;
* sinais de possível extinção digital;
* indisponibilidade recorrente;
* desaparecimento de registros;
* perda de evidência audiovisual detectável.

Esse princípio é central: o observatório não deve apenas mostrar onde há audiovisual, mas também documentar aparecimentos, ausências, retrações e mudanças na visibilidade pública dos acervos.

---

## Arquitetura do projeto

```text
.
├── app/
│   └── streamlit_app.py
├── data/
│   ├── input/
│   └── output/
├── scripts/
│   ├── run_observatory_cycle.py
│   ├── run_pipeline.py
│   ├── run_euscreen_pipeline.py
│   ├── run_european_film_gateway_pipeline.py
│   ├── run_europeana_pipeline.py
│   ├── run_pares_pipeline.py
│   ├── run_ppa_pipeline.py
│   ├── run_ina_pipeline.py
│   ├── run_archipop_pipeline.py
│   ├── run_aamod_pipeline.py
│   ├── run_sfa_pipeline.py
│   ├── run_anf_pipeline.py
│   ├── run_aqshf_pipeline.py
│   ├── run_aapb_pipeline.py
│   └── check_observatory_cycle.py
├── src/
│   └── memoria_audiovisual/
│       ├── analysis.py
│       ├── analysis_exports.py
│       ├── ape.py
│       ├── corpora.py
│       ├── crawler.py
│       ├── dashboard_data.py
│       ├── efg.py
│       ├── europeana.py
│       ├── euscreen.py
│       ├── geography.py
│       ├── organism.py
│       ├── output_files.py
│       ├── pipeline.py
│       ├── reporting.py
│       ├── snapshot_metadata.py
│       └── timeline.py
├── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Fluxo de funcionamento

```text
Fontes públicas
      ↓
Coleta e sondagem técnica
      ↓
Classificação metodológica
      ↓
Detecção de sinais audiovisuais
      ↓
Enriquecimento de metadados
      ↓
Geração de relatórios
      ↓
Snapshot em data/output/
      ↓
Dashboard Streamlit
      ↓
Linha do tempo do observatório
```

---

## Saídas geradas

Os resultados são materializados principalmente em `data/output/`.

O projeto gera arquivos como:

* CSVs analíticos;
* JSONs estruturados;
* relatórios TXT;
* planilhas XLSX;
* dossiês em Markdown;
* linhas do tempo;
* manifestos de ciclo;
* filas de expansão;
* protocolos de negativa;
* relatórios de fechamento regional.

Exemplos de arquivos globais:

```text
data/output/observatorio_ciclo_mensal.json
data/output/observatorio_corpora_ativos.csv
data/output/observatorio_linha_do_tempo_ciclos.csv
data/output/observatorio_resultados_ciclos.csv
data/output/observatorio_fechamento_europa.csv
data/output/observatorio_fila_expansao.csv
data/output/observatorio_unidades_identificadas_nao_incorporadas.csv
```

Cada corpus segue convenções próprias de prefixo, como:

```text
ape_*
euscreen_*
efg_*
europeana_*
pares_*
ppa_*
ina_*
archipop_*
aamod_*
sfa_*
anf_*
aqshf_*
aapb_*
```

---

## Como executar localmente

### 1. Criar ambiente virtual

No Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

### 2. Instalar dependências do Playwright

```powershell
.\.venv\Scripts\python.exe -m playwright install
```

### 3. Executar ciclo geral do observatório

```powershell
.\.venv\Scripts\python.exe scripts\run_observatory_cycle.py
```

### 4. Executar um corpus específico

```powershell
.\.venv\Scripts\python.exe scripts\run_observatory_cycle.py --corpus ina
```

Também é possível executar mais de um corpus:

```powershell
.\.venv\Scripts\python.exe scripts\run_observatory_cycle.py --corpus european-film-gateway --corpus europeana
```

### 5. Validar resultados

```powershell
.\.venv\Scripts\python.exe scripts\check_observatory_cycle.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### 6. Abrir o dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

---

## Deploy do MVP

A implantação recomendada para o MVP é uma aplicação Streamlit que lê snapshots já materializados em `data/output/`.

O deploy público não deve executar crawlers na inicialização. A coleta e a validação metodológica devem ocorrer localmente ou em workflow agendado. A interface pública deve apenas carregar os arquivos já validados.

Configuração recomendada:

| Item              | Valor                                   |
| ----------------- | --------------------------------------- |
| Branch            | `main`                                  |
| Arquivo principal | `app/streamlit_app.py`                  |
| Python            | `3.11` ou superior compatível           |
| Dependências      | `requirements.txt`                      |
| Dados públicos    | `data/output/`                          |
| Configuração      | `.streamlit/config.toml`, se disponível |

Antes do deploy, recomenda-se executar:

```powershell
.\.venv\Scripts\python.exe scripts\check_deployment_ready.py
.\.venv\Scripts\python.exe scripts\check_observatory_cycle.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

---

## Interface Streamlit

A interface Streamlit organiza o observatório em:

* visão geral comparativa;
* abas por corpus;
* indicadores de disponibilidade;
* tabelas analíticas;
* relatórios de coleta;
* linhas do tempo;
* unidades protocoladas;
* fila de expansão;
* protocolos de negativa metodológica.

O dashboard é a camada pública de leitura do observatório, enquanto a coleta permanece controlada pelo pipeline.

---

## Ciclo mensal do organismo

O projeto opera com uma lógica de atualização mensal.

O ciclo mensal:

1. executa corpora ativos;
2. atualiza metadados de rodada;
3. regrava linhas do tempo;
4. atualiza sinais de possível extinção;
5. regenera fila de expansão;
6. produz manifesto do ciclo;
7. valida os artefatos;
8. atualiza o snapshot público.

Script principal:

```powershell
.\.venv\Scripts\python.exe scripts\run_observatory_cycle.py
```

---

## Eixo acadêmico

O observatório integra uma agenda de pesquisa sobre comunicação, memória audiovisual, circulação digital e plataformas.

A pergunta central é:

> Como as plataformas digitais reorganizam a circulação territorial e cultural do audiovisual contemporâneo?

O projeto parte da premissa de que as plataformas digitais não eliminam o território: elas reorganizam o território. A circulação passa a depender de infraestruturas técnicas, políticas de acesso, metadados, idiomas, regimes de visibilidade e interoperabilidade entre instituições, agregadores e plataformas.

---

## O que este projeto demonstra

Este repositório evidencia competências em:

* engenharia de dados aplicada à pesquisa;
* desenho de pipelines reprodutíveis;
* scraping responsável e coleta controlada;
* análise de acervos digitais;
* organização de corpora;
* modelagem metodológica;
* dashboards com Streamlit;
* documentação científica;
* curadoria de dados públicos;
* automação de ciclos recorrentes;
* integração entre comunicação, audiovisual, patrimônio e tecnologia.

---

## Roadmap

### Concluído ou em funcionamento

* Estrutura modular em Python
* Corpora europeus ativos
* Incorporação inicial de corpus extraeuropeu
* Geração de relatórios em múltiplos formatos
* Dashboard Streamlit
* Ciclo mensal do organismo
* Protocolos para unidades não incorporadas
* Fila automática de expansão

### Próximas etapas

* Publicar MVP em Streamlit Community Cloud
* Consolidar documentação metodológica por corpus
* Ampliar cobertura extraeuropeia de forma controlada
* Incorporar indicadores comparativos por região
* Criar versão pública do dossiê metodológico
* Preparar base para artigo, relatório técnico ou projeto de pós-doutorado

---

## Limitações

O observatório trabalha com dados publicamente acessíveis e respeita os limites técnicos e institucionais das fontes.

Algumas limitações importantes:

* ausência de API pública em determinadas fontes;
* páginas instáveis ou indisponíveis;
* resultados limitados por busca pública;
* metadados incompletos;
* ausência de player público;
* evidência audiovisual apenas descritiva;
* diferenças entre acervo existente, acervo digitalizado e acervo publicamente acessível.

Essas limitações não são tratadas como falhas externas apenas, mas como parte do próprio objeto de pesquisa.

---

## Licença

Consulte o arquivo `LICENSE` deste repositório.

---

## Autor

**Bráulio Roberto Rangel da Silva**

Pesquisador e desenvolvedor com atuação em dados públicos, automação, observatórios digitais, comunicação, audiovisual e pesquisa aplicada.

GitHub: [@brauliorrs](https://github.com/brauliorrs)
