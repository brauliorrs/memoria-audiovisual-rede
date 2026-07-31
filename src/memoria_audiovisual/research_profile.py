from collections import Counter


RESEARCH_WORKING_TITLE = "Memória Audiovisual em Rede"

RESEARCH_SUBTITLE = (
    "Plataforma aberta para observação comparativa da visibilidade, do acesso e da "
    "circulação digital de acervos audiovisuais"
)

RESEARCH_MAIN_QUESTION = (
    "Sob quais condições infraestruturais, institucionais, técnicas e culturais os acervos "
    "audiovisuais se tornam visíveis, invisíveis, restritos ou instáveis em ambientes digitais?"
)

RESEARCH_PLATFORM_POSITIONING = {
    "função": "plataforma científica aberta",
    "usos": "pesquisa, ensino, pós-doutorado, propostas competitivas, artigos e relatórios",
    "escopo atual": "fechamento europeu e comparação controlada",
    "maturação": "agenda comparativa de longo prazo",
}


RESEARCH_PARAMETER_ROWS = [
    {
        "parâmetro científico": "Pergunta de pesquisa",
        "tradução na plataforma": "a interface explicita visibilidade, invisibilidade, restrição e instabilidade digital como problemas observáveis",
        "evidência atual": "eixo científico, sínteses de visibilidade, regimes de acesso e linha do tempo",
        "estado": "em adaptação",
    },
    {
        "parâmetro científico": "Infraestrutura científica",
        "tradução na plataforma": "o observatório permanece plataforma pública, mas seus dados operam como infraestrutura de pesquisa",
        "evidência atual": "corpora ativos, agregadores, instituições, snapshots e arquivos exportáveis",
        "estado": "implementado",
    },
    {
        "parâmetro científico": "Unidades de análise separadas",
        "tradução na plataforma": "agregadores, arquivos, instituições custodiais e casos fora da base ativa não são misturados",
        "evidência atual": "categorias analíticas, fichas por unidade e matriz de fechamento europeu",
        "estado": "implementado",
    },
    {
        "parâmetro científico": "Observação longitudinal",
        "tradução na plataforma": "cada rodada preserva data, chave de observação, estado da fonte e histórico de mudanças",
        "evidência atual": "linha do tempo das rodadas, histórico por corpus e sinais de possível extinção",
        "estado": "implementado",
    },
    {
        "parâmetro científico": "Regimes de visibilidade",
        "tradução na plataforma": "a plataforma diferencia evidência pública detectável, evidência indireta, restrição e ausência",
        "evidência atual": "sínteses de visibilidade, modalidades e regimes de acesso audiovisual",
        "estado": "implementado",
    },
    {
        "parâmetro científico": "Comparação europeia",
        "tradução na plataforma": "o fechamento Europa se torna base comparativa, não apenas fila operacional de incorporação",
        "evidência atual": "mapeamento europeu ampliado, fila Europa, agregadores avaliados e lacunas auditadas",
        "estado": "em adaptação",
    },
    {
        "parâmetro científico": "Reprodutibilidade",
        "tradução na plataforma": "cada corpus declara rota, limite técnico, completude e critério de seleção",
        "evidência atual": "campos de completude, notas metodológicas, scripts de execução e checks por corpus",
        "estado": "implementado",
    },
    {
        "parâmetro científico": "Índices e indicadores",
        "tradução na plataforma": "indicadores públicos evoluem para medidas comparáveis de visibilidade audiovisual digital",
        "evidência atual": "índice de dados públicos e tabelas por unidade documental",
        "estado": "a desenvolver",
    },
    {
        "parâmetro científico": "Auditoria de encontrabilidade",
        "tradução na plataforma": "rotas oficiais, agregadores e mecanismos de busca são avaliados como condições de detectabilidade",
        "evidência atual": "rotas oficiais analisadas, probes, protocolos europeus e negativas metodológicas",
        "estado": "em adaptação",
    },
    {
        "parâmetro científico": "Ética e governança de dados",
        "tradução na plataforma": "a plataforma prioriza metadados, identificadores, URLs, datas e evidências permitidas",
        "evidência atual": "armazenamento orientado a metadados e documentação de limites de acesso",
        "estado": "a desenvolver",
    },
]


RESEARCH_NEXT_ADJUSTMENT_ROWS = [
    {
        "prioridade": "1",
        "ajuste": "Consolidar um índice de visibilidade audiovisual digital",
        "resultado esperado": "índice calculável por corpus, país, idioma, agregador, regime de acesso e estabilidade da rota",
    },
    {
        "prioridade": "2",
        "ajuste": "Transformar o fechamento Europa em desenho comparativo",
        "resultado esperado": "amostra europeia justificada, com critérios de inclusão, exclusão, negativos e casos extremos",
    },
    {
        "prioridade": "3",
        "ajuste": "Criar camada de auditoria de detectabilidade",
        "resultado esperado": "métricas sobre idioma dos metadados, rotas oficiais, indexação, APIs, links persistentes e agregação",
    },
    {
        "prioridade": "4",
        "ajuste": "Formalizar protocolo de ética, direito e dados",
        "resultado esperado": "separação clara entre metadados observáveis, evidências permitidas, conteúdo protegido e dados pessoais",
    },
    {
        "prioridade": "5",
        "ajuste": "Gerar relatório científico a partir do snapshot",
        "resultado esperado": "evidências preliminares exportáveis para artigos, relatórios metodológicos e propostas futuras",
    },
]


def build_research_parameter_rows():
    return [row.copy() for row in RESEARCH_PARAMETER_ROWS]


def build_research_next_adjustment_rows():
    return [row.copy() for row in RESEARCH_NEXT_ADJUSTMENT_ROWS]


def summarize_research_parameter_status(rows=None):
    rows = RESEARCH_PARAMETER_ROWS if rows is None else rows
    return dict(Counter(row["estado"] for row in rows))
