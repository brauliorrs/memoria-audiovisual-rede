from collections import Counter

from memoria_audiovisual.i18n import (
    PHRASE_TRANSLATIONS,
    DEFAULT_LANGUAGE,
    language_code_from_label,
    translate_ui_text,
)


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


_PROFILE_TRANSLATIONS = {
    "en": {
        RESEARCH_SUBTITLE: "Open platform for comparative observation of the visibility, access and digital circulation of audiovisual archives",
        RESEARCH_MAIN_QUESTION: "Under which infrastructural, institutional, technical and cultural conditions do audiovisual archives become visible, invisible, restricted or unstable in digital environments?",
        "Pergunta científica provisória:": "Provisional research question:",
        "função": "function",
        "usos": "uses",
        "escopo atual": "current scope",
        "maturação": "maturation",
        "plataforma científica aberta": "open scientific platform",
        "pesquisa, ensino, pós-doutorado, propostas competitivas, artigos e relatórios": "research, teaching, postdoctoral work, competitive proposals, articles and reports",
        "fechamento europeu e comparação controlada": "European consolidation and controlled comparison",
        "agenda comparativa de longo prazo": "long-term comparative agenda",
        "parâmetro científico": "scientific parameter",
        "tradução na plataforma": "platform implementation",
        "evidência atual": "current evidence",
        "estado": "status",
        "Pergunta de pesquisa": "Research question",
        "Infraestrutura científica": "Scientific infrastructure",
        "Unidades de análise separadas": "Separate units of analysis",
        "Observação longitudinal": "Longitudinal observation",
        "Regimes de visibilidade": "Visibility regimes",
        "Comparação europeia": "European comparison",
        "Reprodutibilidade": "Reproducibility",
        "Índices e indicadores": "Indexes and indicators",
        "Auditoria de encontrabilidade": "Findability audit",
        "Ética e governança de dados": "Data ethics and governance",
        "a interface explicita visibilidade, invisibilidade, restrição e instabilidade digital como problemas observáveis": "the interface presents visibility, invisibility, restriction and digital instability as observable problems",
        "o observatório permanece plataforma pública, mas seus dados operam como infraestrutura de pesquisa": "the observatory remains a public platform while its data operate as research infrastructure",
        "agregadores, arquivos, instituições custodiais e casos fora da base ativa não são misturados": "aggregators, archives, custodial institutions and cases outside the active corpus are not conflated",
        "cada rodada preserva data, chave de observação, estado da fonte e histórico de mudanças": "each cycle preserves date, observation key, source status and change history",
        "a plataforma diferencia evidência pública detectável, evidência indireta, restrição e ausência": "the platform distinguishes detectable public evidence, indirect evidence, restriction and absence",
        "o fechamento Europa se torna base comparativa, não apenas fila operacional de incorporação": "European consolidation becomes a comparative basis rather than merely an operational incorporation queue",
        "cada corpus declara rota, limite técnico, completude e critério de seleção": "each corpus declares its route, technical limit, completeness and selection criterion",
        "indicadores públicos evoluem para medidas comparáveis de visibilidade audiovisual digital": "public indicators evolve into comparable measures of digital audiovisual visibility",
        "rotas oficiais, agregadores e mecanismos de busca são avaliados como condições de detectabilidade": "official routes, aggregators and search mechanisms are evaluated as conditions of detectability",
        "a plataforma prioriza metadados, identificadores, URLs, datas e evidências permitidas": "the platform prioritizes metadata, identifiers, URLs, dates and permitted evidence",
        "eixo científico, sínteses de visibilidade, regimes de acesso e linha do tempo": "scientific axis, visibility summaries, access regimes and timeline",
        "corpora ativos, agregadores, instituições, snapshots e arquivos exportáveis": "active corpora, aggregators, institutions, snapshots and exportable files",
        "categorias analíticas, fichas por unidade e matriz de fechamento europeu": "analytical categories, unit records and European consolidation matrix",
        "linha do tempo das rodadas, histórico por corpus e sinais de possível extinção": "cycle timeline, corpus history and signals of possible disappearance",
        "sínteses de visibilidade, modalidades e regimes de acesso audiovisual": "visibility summaries, modalities and audiovisual access regimes",
        "mapeamento europeu ampliado, fila Europa, agregadores avaliados e lacunas auditadas": "expanded European mapping, Europe queue, evaluated aggregators and audited gaps",
        "campos de completude, notas metodológicas, scripts de execução e checks por corpus": "completeness fields, methodological notes, execution scripts and corpus checks",
        "índice de dados públicos e tabelas por unidade documental": "public data index and tables by documentary unit",
        "rotas oficiais analisadas, probes, protocolos europeus e negativas metodológicas": "analyzed official routes, probes, European protocols and methodological negatives",
        "armazenamento orientado a metadados e documentação de limites de acesso": "metadata-oriented storage and documentation of access limits",
        "implementado": "implemented",
        "em adaptação": "being adapted",
        "a desenvolver": "to be developed",
        "prioridade": "priority",
        "ajuste": "adjustment",
        "resultado esperado": "expected result",
        "Consolidar um índice de visibilidade audiovisual digital": "Consolidate a digital audiovisual visibility index",
        "Transformar o fechamento Europa em desenho comparativo": "Transform European consolidation into a comparative design",
        "Criar camada de auditoria de detectabilidade": "Create a detectability audit layer",
        "Formalizar protocolo de ética, direito e dados": "Formalize an ethics, law and data protocol",
        "Gerar relatório científico a partir do snapshot": "Generate a scientific report from the snapshot",
        "índice calculável por corpus, país, idioma, agregador, regime de acesso e estabilidade da rota": "index calculable by corpus, country, language, aggregator, access regime and route stability",
        "amostra europeia justificada, com critérios de inclusão, exclusão, negativos e casos extremos": "justified European sample with inclusion, exclusion, negative and extreme-case criteria",
        "métricas sobre idioma dos metadados, rotas oficiais, indexação, APIs, links persistentes e agregação": "metrics on metadata language, official routes, indexing, APIs, persistent links and aggregation",
        "separação clara entre metadados observáveis, evidências permitidas, conteúdo protegido e dados pessoais": "clear separation among observable metadata, permitted evidence, protected content and personal data",
        "evidências preliminares exportáveis para artigos, relatórios metodológicos e propostas futuras": "exportable preliminary evidence for articles, methodological reports and future proposals",
    },
    "es": {
        RESEARCH_SUBTITLE: "Plataforma abierta para la observación comparativa de la visibilidad, el acceso y la circulación digital de archivos audiovisuales",
        RESEARCH_MAIN_QUESTION: "¿Bajo qué condiciones infraestructurales, institucionales, técnicas y culturales los archivos audiovisuales se vuelven visibles, invisibles, restringidos o inestables en entornos digitales?",
        "Pergunta científica provisória:": "Pregunta científica provisional:",
        "parâmetro científico": "parámetro científico",
        "tradução na plataforma": "implementación en la plataforma",
        "evidência atual": "evidencia actual",
        "estado": "estado",
        "prioridade": "prioridad",
        "ajuste": "ajuste",
        "resultado esperado": "resultado esperado",
        "implementado": "implementado",
        "em adaptação": "en adaptación",
        "a desenvolver": "por desarrollar",
    },
}


def _register_profile_translations():
    for language, replacements in _PROFILE_TRANSLATIONS.items():
        PHRASE_TRANSLATIONS.setdefault(language, {}).update(replacements)


_register_profile_translations()


def _active_language():
    """Resolve the current Streamlit interface language without coupling callers to Streamlit."""
    try:
        import streamlit as st

        selected = st.session_state.get("interface_language")
        if selected in PHRASE_TRANSLATIONS:
            return selected
        if isinstance(selected, str):
            return language_code_from_label(selected)
    except Exception:
        pass
    return DEFAULT_LANGUAGE


def _localize_rows(rows, language=None):
    language = language or _active_language()
    if language == DEFAULT_LANGUAGE:
        return [row.copy() for row in rows]
    return [
        {
            translate_ui_text(key, language): translate_ui_text(value, language)
            if isinstance(value, str)
            else value
            for key, value in row.items()
        }
        for row in rows
    ]


def build_research_parameter_rows(language=None):
    return _localize_rows(RESEARCH_PARAMETER_ROWS, language)


def build_research_next_adjustment_rows(language=None):
    return _localize_rows(RESEARCH_NEXT_ADJUSTMENT_ROWS, language)


def summarize_research_parameter_status(rows=None):
    rows = RESEARCH_PARAMETER_ROWS if rows is None else rows
    return dict(Counter(row["estado"] for row in rows))
