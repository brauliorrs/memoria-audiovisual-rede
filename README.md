# Memória Audiovisual em Rede

**Plataforma aberta para mapear, monitorar e analisar a presença pública de acervos audiovisuais em plataformas, arquivos, cinematecas e agregadores digitais.**

O projeto combina coleta automatizada, curadoria metodológica, indicadores comparáveis e visualização em Streamlit para estudar como a memória audiovisual circula, aparece, desaparece, torna-se restrita ou permanece pouco visível em ambientes digitais.

A plataforma permanece uma plataforma pública, com usos variados: pesquisa, ensino, pós-doutorado, artigos, relatórios, propostas competitivas e estudos comparativos sobre acervos audiovisuais. Para sustentar esses usos, cada unidade observada precisa preservar rotas, limites, completude, regimes de acesso, sinais de visibilidade, histórico de observação e evidências metodológicas auditáveis.

## Acesso público

A versão pública do observatório está disponível no Streamlit:

[https://memoria-audiovisual-rede-vcxnq9xh7b7uifydhwjxcy.streamlit.app/](https://memoria-audiovisual-rede-vcxnq9xh7b7uifydhwjxcy.streamlit.app/)

Nesta etapa, o foco principal é o fechamento europeu do observatório. A expansão para outros continentes será feita somente depois que a Europa estiver metodologicamente documentada, incluindo unidades incorporadas, unidades protocoladas e negativas justificadas.

## Eixo científico

O observatório é uma plataforma científica aberta para investigações sobre acervos audiovisuais em rede.

Pergunta orientadora:

**Sob quais condições infraestruturais, institucionais, técnicas e culturais os acervos audiovisuais se tornam visíveis, invisíveis, restritos ou instáveis em ambientes digitais?**

As plataformas digitais não eliminam o território; elas reorganizam o território. No audiovisual contemporâneo, a circulação deixa de depender apenas do lugar físico do arquivo, da cinemateca, da emissora ou da instituição custodial, e passa a depender de infraestrutura técnica, políticas de acesso, licenciamento, idioma dos metadados, indexação, geobloqueio, plataformas externas, interoperabilidade e regimes algorítmicos de visibilidade.

A hipótese de trabalho é que a circulação digital da memória audiovisual não é determinada apenas pela localização física ou pela dimensão material dos acervos, mas pela capacidade das instituições e plataformas de tornar esses acervos detectáveis, descritos, interoperáveis, acessíveis e estáveis em redes digitais transnacionais.

## Parâmetros científicos

A plataforma está sendo ajustada para explicitar parâmetros de robustez científica que podem subsidiar pesquisas de diferentes escalas:

- unidades de análise separadas: agregador, arquivo, instituição custodial, corpus, registro, rota e caso fora da base ativa;
- observação longitudinal por snapshots, data de coleta, chave de observação e estado da fonte;
- regimes de visibilidade, acesso, restrição, instabilidade e possível extinção digital;
- completude da coleta, critério de seleção, limite técnico e nota metodológica por corpus;
- comparação europeia controlada, com incorporações, lacunas, negativas justificadas e casos extremos;
- reprodutibilidade por scripts, checks, arquivos exportáveis e contratos de dados;
- base para índices futuros de visibilidade audiovisual digital e auditoria de encontrabilidade.

## Auditoria de infraestrutura digital

A plataforma inclui uma ferramenta reprodutível para observar a camada técnica das superfícies públicas dos arquivos e agregadores. A auditoria registra, por corpus:

- tecnologias e sistemas detectáveis, como CMS e softwares de repositório;
- existência e tipo de APIs ou serviços públicos, incluindo REST, GraphQL, OAI-PMH, OpenAPI e IIIF;
- formatos de metadados, como JSON-LD/Schema.org, Dublin Core, EAD, METS, MODS, MARC, EDM, PBCore e EBUCore;
- protocolos e sinais de interoperabilidade, como IIIF, OAI-PMH, OpenSearch, RSS/Atom, sitemaps e Linked Open Data;
- mecanismos de busca, incluindo formulários HTML e sinais de Solr, Elasticsearch, Algolia ou busca facetada;
- restrições públicas detectáveis, como autenticação, cadastro, assinatura, geobloqueio, direitos condicionados e restrições de indexação;
- evidências textuais públicas de uso de IA, aprendizado de máquina, transcrição automática, reconhecimento de fala, visão computacional ou classificação automatizada na catalogação.

A ferramenta é **heurística**: registra evidências encontradas no HTML, nos metadados e nos cabeçalhos HTTP da rota observada. Ausência de sinal não significa ausência da tecnologia, e uma detecção deve ser validada antes de sustentar afirmações institucionais. A auditoria não contorna login, paywall, robots.txt ou outras barreiras.

Execução completa dos corpora ativos:

```powershell
python scripts/audit_digital_infrastructure.py
```

Execução controlada:

```powershell
python scripts/audit_digital_infrastructure.py --corpus europeana ina bfi
python scripts/audit_digital_infrastructure.py --limit 5 --timeout 30
```

Saídas versionáveis:

- `data/output/digital_infrastructure_audit.csv`;
- `data/output/digital_infrastructure_audit.json`.

O código principal está em `src/memoria_audiovisual/digital_infrastructure_audit.py`, e o executor está em `scripts/audit_digital_infrastructure.py`.

## Escopo atual

O organismo trabalha com corpora ativos e unidades documentadas fora do corpus ativo.

- Corpora ativos materializados: `51`.
- Agregadores ativos: `7`.
- Arquivos e instituições ativos: `44`.
- Fila europeia de fechamento documentada no MVP.
- Snapshot público atual: aproximadamente `277 MB`.
- Interface principal: `app/streamlit_app.py`.

Agregadores ativos:

- `APE`, `EUscreen`, `European Film Gateway`, `Europeana`, `PARES`, `Portal Português de Arquivos` e `American Archive of Public Broadcasting`.

Arquivos e instituições ativos:

- `INA`, `AAMOD`, `ANF`, `AQSHF`, `ARCHIPOP`, `Archivio Luce`, `ASIM`, `Autrefois`, `BArch`, `BBC`, `BFI`, `BNFA`, `BNT`, `CCMA/3Cat`, `CdNA`, `CICLIC`, `CINÉAM`, `Ciné-Archives`, `Cinemateca Portuguesa`, `CINEMATEK`, `Cinémathèque de Bretagne`, `Cinémathèque française`, `Cinémémoire`, `CNA Luxembourg`, `CPSA`, `Crnogorska Kinoteka`, `Czech Television`, `Deutsche Kinemathek`, `DFF`, `DHM`, `DR`, `ECPAD`, `ERT`, `Estonian Film Archive`, `Eye`, `Filmarchiv Austria`, `Filmmuseum Düsseldorf`, `Filmoteca de Catalunya`, `Filmoteca Española`, `Filmoteca Valenciana`, `Filmoteca Vasca`, `IAM`, `Saint-Étienne` e `SFA`.

O `American Archive of Public Broadcasting` aparece como corpus extraeuropeu controlado para comparação metodológica. A abertura sistemática de novos continentes permanece em etapa posterior.

## Regra audiovisual

O recorte do observatório é audiovisual. Arquivos exclusivamente sonoros, documentais ou textuais não entram no corpus ativo, mesmo quando são relevantes para a história dos arquivos.

Critérios centrais:

- fontes gerais podem ser registradas como fontes de pesquisa quando retornam zero evidência audiovisual;
- arquivos explicitamente audiovisuais que retornam zero são tratados como anomalia metodológica relevante;
- bancos privados, publicitários ou comerciais com acesso pago entram apenas como unidades documentadas quando não oferecem catálogo público quantificável;
- registros descritivos, players públicos, objetos digitais e links externos são classificados separadamente;
- nenhum número é apresentado como total do acervo físico quando a rota pública observada não permite essa afirmação.

Essa regra evita confundir existência institucional do acervo com visibilidade pública digital do audiovisual.

## Estratégia de expansão

O crescimento do organismo segue duas etapas:

1. **Agregadores primeiro.** Prioriza agregadores continentais, supranacionais ou nacionais, pois eles permitem mapear grandes superfícies institucionais com maior comparabilidade.
2. **Instituições depois.** Incorpora arquivos, cinematecas e instituições individuais quando há lacunas relevantes, exceções metodológicas ou rotas públicas de coleta suficientemente estáveis.

Cada nova unidade deve ser classificada sem misturar níveis analíticos:

- agregador;
- arquivo ou instituição custodial;
- unidade identificada, mas não incorporada;
- banco privado ou comercial fora do índice estatístico;
- fonte contextual fora do escopo audiovisual.

## Completude da coleta

Nenhum corpus parcial é apresentado como catálogo total.

Cada corpus declara:

- completude da coleta;
- critério de seleção;
- limite técnico;
- nota metodológica;
- tipo de evidência encontrada;
- grau de estabilidade da rota usada.

Assim, registros por termo, páginas coletadas ou vídeos detectados representam uma rodada reprodutível de observação pública, não necessariamente a totalidade do acervo institucional.

## Índice de dados públicos

O índice de dados públicos mede apenas registros audiovisuais materializados no organismo. O denominador é formado por registros coletáveis, descritos ou detectáveis em corpus ativo; ele não tenta estimar o tamanho total de acervos privados, comerciais ou não expostos por catálogo público.

Indicadores atuais do snapshot:

- mundo: `52.444` registros públicos, `25.041` restritos, `67,68%` de dados públicos;
- Europa: `52.416` registros públicos, `25.041` restritos, `67,67%` de dados públicos;
- América do Norte: `28` registros públicos, `0` restritos, `100%` de dados públicos no corpus comparativo ativo.

Bancos de imagens publicitárias ou comerciais não entram no índice quando não há catálogo público quantificável. Eles podem permanecer documentados como negativa metodológica.

## Linha do tempo do organismo

O observatório registra a história das rodadas para acompanhar crescimento, retração e possíveis extinções digitais.

Cada ciclo pode registrar:

- linha do tempo do corpus;
- linha do tempo institucional;
- sinais de possível extinção digital;
- indisponibilidade recorrente;
- perda de evidência audiovisual detectável;
- mudança no regime de acesso público.

O princípio é simples: o observatório não deve apenas mostrar onde há audiovisual, mas também preservar a história de aparecimento, ausência, retração e transformação da visibilidade pública dos acervos.

## Como rodar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Validação rápida antes de publicar:

```powershell
python -m compileall -q app src
python scripts/check_deployment_ready.py
```

## Publicação

O GitHub guarda o código, os dados públicos versionados e a memória técnica do projeto. Para abrir a interface como aplicação web, use Streamlit Cloud.

Configuração sugerida no Streamlit Cloud:

- repositório: `brauliorrs/memoria-audiovisual-rede`;
- branch: `main`;
- arquivo principal: `app/streamlit_app.py`;
- dependências: `requirements.txt`.

GitHub Pages não é suficiente para esta versão porque a interface é uma aplicação Python/Streamlit, não uma página estática.

## Estrutura do repositório

```text
.
├── app/
│   └── streamlit_app.py
├── data/
│   ├── input/
│   └── output/
├── scripts/
│   └── audit_digital_infrastructure.py
├── src/
│   └── memoria_audiovisual/
│       └── digital_infrastructure_audit.py
├── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Status do MVP

O MVP está pronto para publicação experimental controlada. A plataforma já permite apresentar o organismo, navegar por agregadores e instituições, consultar vídeos identificados, examinar regimes de acesso, acompanhar o fechamento europeu e documentar unidades identificadas que ainda não puderam ser incorporadas ao corpus ativo.
