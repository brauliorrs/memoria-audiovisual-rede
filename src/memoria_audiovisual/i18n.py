from __future__ import annotations

import re


LANGUAGE_OPTIONS = {
    "pt": "Português",
    "es": "Español",
    "en": "English",
}

LANGUAGE_CODES_BY_LABEL = {label: code for code, label in LANGUAGE_OPTIONS.items()}
DEFAULT_LANGUAGE = "pt"

PROJECT_CONTEXT_SIGNALS = {
    "postdoctoral_affiliation": {
        "public_display": False,
        "institutional_target": "Universidade de Valência / Universidad de Valencia / University of Valencia",
        "research_group": "Communication and Media Culture History Research Group",
        "note": "Contexto interno sinalizado, mas oculto da interface pública por decisão editorial.",
    }
}


TRANSLATIONS = {
    "pt": {
        "app_title": "Plataforma aberta de curadoria e acesso à memória audiovisual em rede",
        "app_caption": (
            "O observatório funciona como um organismo agregador mundial em construção, separando explicitamente "
            "agregadores arquivísticos e arquivos ou instituições custodiais para preservar o rigor analítico."
        ),
        "language_selector": "Idioma da interface",
        "language_note": (
            "A interface pública está disponível em três idiomas. Registros, evidências e nomes institucionais "
            "permanecem no idioma da fonte quando isso preserva rastreabilidade científica."
        ),
        "overview_title": "## Visão geral do observatório",
        "overview_caption": (
            "O observatório opera como um organismo agregador mundial em construção. As unidades documentais "
            "permanecem separadas por categoria analítica e por unidade própria, mas esta visão geral permite "
            "compará-las sem misturar seus níveis de análise."
        ),
        "observatory_profile_summary": (
            "O organismo mapeia, valida e compara agregadores e arquivos audiovisuais em escala mundial, "
            "preservando a diferença entre agregadores, arquivos individuais, bancos privados e fontes de radar."
        ),
        "academic_axis_title": "### Eixo acadêmico do projeto",
        "academic_axis_text": (
            "Este observatório integra a formulação de um projeto de pós-doutorado em desenvolvimento.\n\n"
            "A pergunta orientadora é: **como as plataformas digitais reorganizam a circulação territorial e "
            "cultural do audiovisual contemporâneo?**\n\n"
            "As plataformas digitais não eliminam o território; elas reorganizam o território. No audiovisual "
            "contemporâneo, a circulação deixa de depender apenas do lugar físico do arquivo, da cinemateca, da "
            "emissora ou da instituição custodial, e passa a depender de infraestrutura técnica, políticas de "
            "acesso e licenciamento, idioma dos metadados, formatos de indexação, regimes de visibilidade e "
            "dependência de plataformas externas.\n\n"
            "A hipótese de trabalho é que a circulação audiovisual contemporânea é cada vez menos determinada "
            "apenas pela localização física dos acervos e cada vez mais pela capacidade das instituições e "
            "plataformas de tornar esses acervos detectáveis, descritos, interoperáveis e acessíveis em redes "
            "digitais transnacionais."
        ),
        "academic_axis_caption": (
            "No observatório, essa pergunta é operacionalizada por variáveis como hospedagem, indexação, descrição, "
            "idioma, regime de acesso, plataforma, visibilidade pública e escala territorial."
        ),
        "raw_data_note": (
            "Nota linguística: tabelas, evidências de protocolo e nomes de instituições podem permanecer no idioma "
            "original da coleta para preservar auditabilidade."
        ),
        "category_tab": "Categoria: {label}",
        "unit_tab": "Unidade: {label}",
        "documented_case_tab": "Caso registrado: {label}",
    },
    "es": {
        "app_title": "Plataforma abierta de curaduría y acceso a la memoria audiovisual en red",
        "app_caption": (
            "El observatorio funciona como un organismo agregador mundial en construcción, separando explícitamente "
            "agregadores archivísticos y archivos o instituciones custodias para preservar el rigor analítico."
        ),
        "language_selector": "Idioma de la interfaz",
        "language_note": (
            "La interfaz pública está disponible en tres idiomas. Registros, evidencias y nombres institucionales "
            "permanecen en el idioma de la fuente cuando eso preserva la trazabilidad científica."
        ),
        "overview_title": "## Visión general del observatorio",
        "overview_caption": (
            "El observatorio opera como un organismo agregador mundial en construcción. Las unidades documentales "
            "permanecen separadas por categoría analítica y por unidad propia, pero esta visión general permite "
            "compararlas sin mezclar sus niveles de análisis."
        ),
        "observatory_profile_summary": (
            "El organismo mapea, valida y compara agregadores y archivos audiovisuales a escala mundial, "
            "preservando la diferencia entre agregadores, archivos individuales, bancos privados y fuentes de radar."
        ),
        "academic_axis_title": "### Eje académico del proyecto",
        "academic_axis_text": (
            "Este observatorio forma parte de la formulación de un proyecto de posdoctorado en desarrollo.\n\n"
            "La pregunta orientadora es: **¿cómo reorganizan las plataformas digitales la circulación territorial "
            "y cultural del audiovisual contemporáneo?**\n\n"
            "Las plataformas digitales no eliminan el territorio; lo reorganizan. En el audiovisual contemporáneo, "
            "la circulación deja de depender únicamente del lugar físico del archivo, la cinemateca, la emisora o "
            "la institución custodia, y pasa a depender de infraestructura técnica, políticas de acceso y "
            "licenciamiento, idioma de los metadatos, formatos de indexación, regímenes de visibilidad y "
            "dependencia de plataformas externas.\n\n"
            "La hipótesis de trabajo es que la circulación audiovisual contemporánea está cada vez menos "
            "determinada solo por la localización física de los acervos y cada vez más por la capacidad de "
            "instituciones y plataformas para hacer esos acervos detectables, descritos, interoperables y "
            "accesibles en redes digitales transnacionales."
        ),
        "academic_axis_caption": (
            "En el observatorio, esta pregunta se operacionaliza mediante variables como hospedaje, indexación, "
            "descripción, idioma, régimen de acceso, plataforma, visibilidad pública y escala territorial."
        ),
        "raw_data_note": (
            "Nota lingüística: tablas, evidencias de protocolo y nombres institucionales pueden permanecer en el "
            "idioma original de la recolección para preservar la auditabilidad."
        ),
        "category_tab": "Categoría: {label}",
        "unit_tab": "Unidad: {label}",
        "documented_case_tab": "Caso documentado: {label}",
    },
    "en": {
        "app_title": "Open platform for curation and access to networked audiovisual memory",
        "app_caption": (
            "The observatory functions as a world aggregator organism under construction, explicitly separating "
            "archival aggregators from archives or custodial institutions in order to preserve analytical rigor."
        ),
        "language_selector": "Interface language",
        "language_note": (
            "The public interface is available in three languages. Records, evidence and institutional names remain "
            "in the source language whenever this preserves scientific traceability."
        ),
        "overview_title": "## Observatory Overview",
        "overview_caption": (
            "The observatory operates as a world aggregator organism under construction. Documentary units remain "
            "separated by analytical category and by their own unit, while this overview allows comparison without "
            "mixing levels of analysis."
        ),
        "observatory_profile_summary": (
            "The organism maps, validates and compares audiovisual aggregators and archives at a global scale, "
            "preserving the distinction between aggregators, individual archives, private banks and radar sources."
        ),
        "academic_axis_title": "### Academic Axis of the Project",
        "academic_axis_text": (
            "This observatory is part of the formulation of a postdoctoral project in development.\n\n"
            "The guiding question is: **how do digital platforms reorganize the territorial and cultural "
            "circulation of contemporary audiovisual media?**\n\n"
            "Digital platforms do not eliminate territory; they reorganize it. In contemporary audiovisual "
            "circulation, access no longer depends only on the physical location of the archive, cinematheque, "
            "broadcaster or custodial institution, but also on technical infrastructure, access and licensing "
            "policies, metadata language, indexing formats, visibility regimes and dependence on external "
            "platforms.\n\n"
            "The working hypothesis is that contemporary audiovisual circulation is increasingly less determined "
            "only by the physical location of collections and increasingly more by the capacity of institutions "
            "and platforms to make those collections detectable, described, interoperable and accessible in "
            "transnational digital networks."
        ),
        "academic_axis_caption": (
            "In the observatory, this question is operationalized through variables such as hosting, indexing, "
            "description, language, access regime, platform, public visibility and territorial scale."
        ),
        "raw_data_note": (
            "Language note: tables, protocol evidence and institutional names may remain in the original collection "
            "language to preserve auditability."
        ),
        "category_tab": "Category: {label}",
        "unit_tab": "Unit: {label}",
        "documented_case_tab": "Documented Case: {label}",
    },
}


PHRASE_TRANSLATIONS = {
    "es": {
        "Visão geral": "Visión general",
        "Agregadores": "Agregadores",
        "Arquivos": "Archivos",
        "Agregadores arquivísticos": "Agregadores archivísticos",
        "Arquivos e instituições arquivísticas": "Archivos e instituciones archivísticas",
        "Fundamentação": "Fundamentación",
        "Síntese": "Síntesis",
        "Instituições com vídeo": "Instituciones con video",
        "Vídeos e temas": "Videos y temas",
        "Vídeos": "Videos",
        "Territórios": "Territorios",
        "Tabelas": "Tablas",
        "Instituições": "Instituciones",
        "Ficha institucional": "Ficha de la institución",
        "Histórico geral": "Historial general",
        "Sinais de possível extinção": "Señales de posible extinción",
        "Síntese da fila": "Síntesis de la cola",
        "Fontes candidatas": "Fuentes candidatas",
        "Regimes de acesso": "Regímenes de acceso",
        "Modalidades de acesso": "Modalidades de acceso",
        "Critérios de fechamento": "Criterios de cierre",
        "Matriz europeia": "Matriz europea",
        "Fora da base ativa": "Fuera de la base activa",
        "Acesso pago/restrito": "Acceso pago/restringido",
        "Lacunas documentadas": "Lagunas documentadas",
        "Próximas unidades": "Unidades siguientes",
        "Mapa europeu": "Mapa europeo",
        "Síntese do mapeamento": "Síntesis del mapeo",
        "Linha do tempo das rodadas": "Línea de tiempo de las rondas",
        "Resultados por unidade": "Resultados por unidad",
        "Arquivos de referência": "Archivos de referencia",
        "Síntese institucional": "Síntesis institucional",
        "Temas e relações": "Temas y relaciones",
        "Casos documentados": "Casos registrados",
        "Ficha e acesso": "Ficha y acceso",
        "Vídeos detectados": "Videos detectados",
        "Páginas analisadas": "Páginas analizadas",
        "Categoria": "Categoría",
        "Unidade": "Unidad",
        "Caso documentado": "Caso documentado",
        "Instituição": "Institución",
        "Informação": "Información",
        "Domínio": "Dominio",
        "Observação": "Observación",
        "Código": "Código",
        "Repositório": "Repositorio",
        "Conteúdo": "Contenido",
        "Ficha": "Ficha",
        "Fonte": "Fuente",
        "Data": "Fecha",
        "Título": "Título",
        "Assunto": "Asunto",
        "Descrição": "Descripción",
        "Link": "Enlace",
        "Método": "Método",
        "Tipo": "Tipo",
        "Valor": "Valor",
        "Conclusão": "Conclusión",
        "Referência": "Referencia",
        "Evidência": "Evidencia",
        "Nível": "Nivel",
        "Escala": "Escala",
        "Completude": "Completitud",
        "Limite": "Límite",
        "Justificativa": "Justificación",
        "Prioridade": "Prioridad",
        "Decisão": "Decisión",
        "Gatilho": "Disparador",
        "Encaminhamento": "Derivación",
        "Risco": "Riesgo",
        "Modelo": "Modelo",
        "Termos": "Términos",
        "Resultado": "Resultado",
        "Resultados": "Resultados",
        "Ingestão": "Ingesta",
        "Avaliado": "Evaluado",
        "Melhor URL": "Mejor URL",
        "Publicado": "Publicado",
        "Possível": "Posible",
        "Disponível": "Disponible",
        "Restrito": "Restringido",
        "Restrita": "Restringida",
        "Ativo": "Activo",
        "Ativa": "Activa",
        "Técnico": "Técnico",
        "Técnica": "Técnica",
        "Metodológico": "Metodológico",
        "Metodológica": "Metodológica",
        "Íntegro": "Íntegro",
        "Acessível": "Accesible",
        "Instável": "Inestable",
        "Sem site": "Sin sitio",
        "Erro HTTP": "Error HTTP",
        "Indisponíveis": "No disponibles",
        "Disponíveis com vídeos": "Disponibles con videos",
        "Disponíveis sem vídeos": "Disponibles sin videos",
        "Identificada, mas não incluída na base ativa do observatório": (
            "Identificada, pero no incluida en la base activa del observatorio"
        ),
        "não incorporar à base ativa no MVP": "no incorporar a la base activa en el MVP",
        "Ausência de rota de coleta estável no protocolo atual.": (
            "Ausencia de ruta de recolección estable en el protocolo actual."
        ),
        "categoria de acesso": "categoría de acceso",
        "status público": "estado público",
        "decisão metodológica": "decisión metodológica",
        "motivo da não inclusão": "motivo de la no inclusión",
        "rota de coleta tentada": "ruta de recolección intentada",
        "tentativas registradas": "intentos registrados",
        "explicação metodológica": "explicación metodológica",
        "próximo passo": "próximo paso",
        "tipo de rota": "tipo de ruta",
        "URL da rota": "URL de la ruta",
        "status de acesso": "estado de acceso",
        "uso audiovisual possível": "uso audiovisual posible",
        "nota metodológica": "nota metodológica",
        "tipo de conteúdo": "tipo de contenido",
        "sinal observado": "señal observada",
        "valor observado": "valor observado",
        "conteúdo publicado na fonte": "contenido publicado en la fuente",
        "ficha da instituição na fonte": "ficha de la institución en la fuente",
        "site informado na fonte": "sitio informado en la fuente",
        "site externo informado": "sitio externo informado",
        "URL final": "URL final",
        "código do repositório": "código del repositorio",
        "título do vídeo": "título del video",
        "data do vídeo": "fecha del video",
        "assunto do vídeo": "asunto del video",
        "descrição do vídeo": "descripción del video",
        "link do vídeo": "enlace del video",
        "status_técnico": "estado_técnico",
        "Atualizado no último ciclo": "Actualizado en el último ciclo",
        "Pendente no ciclo parcial mais recente": "Pendiente en el ciclo parcial más reciente",
        "Atualização atrasada": "Actualización atrasada",
        "Falha no último ciclo": "Falla en el último ciclo",
        "escala de cobertura": "escala de cobertura",
        "completude da coleta": "completitud de la recolección",
        "limite técnico": "límite técnico",
        "nota de completude": "nota de completitud",
        "última observação registrada": "última observación registrada",
        "status da fonte": "estado de la fuente",
        "chave de observação": "clave de observación",
        "dias desde a última observação": "días desde la última observación",
        "estado de atualização": "estado de actualización",
        "justificativa metodológica": "justificación metodológica",
        "registros públicos": "registros públicos",
        "registros restritos": "registros restringidos",
        "registros avaliados no observatório": "registros evaluados en el observatorio",
        "% público": "% público",
        "% restrito": "% restringido",
        "nota do denominador": "nota del denominador",
        "status no organismo": "estado en el organismo",
        "categoria de restrição": "categoría de restricción",
        "status do volume": "estado del volumen",
        "arquivo-fonte": "archivo-fuente",
        "tipo de sinal": "tipo de señal",
        "etapa de expansão": "etapa de expansión",
        "atualização analítica": "actualización analítica",
        "critério de entrada": "criterio de entrada",
        "regra de expansão": "regla de expansión",
        "modelo de acesso observado": "modelo de acceso observado",
        "status metodológico": "estado metodológico",
        "termos sondados": "términos sondeados",
        "termos com resultado": "términos con resultado",
        "termos bloqueados": "términos bloqueados",
        "recomendação de ingestão": "recomendación de ingesta",
        "avaliado em": "evaluado en",
        "melhor URL de sondagem": "mejor URL de sondeo",
        "modelo observado": "modelo observado",
        "exige nova rota": "exige nueva ruta",
        "estado da avaliação": "estado de la evaluación",
        "evidência observada": "evidencia observada",
        "risco metodológico": "riesgo metodológico",
        "encaminhamento recomendado": "encaminamiento recomendado",
        "decisão de incorporação": "decisión de incorporación",
        "gatilho de revisão": "disparador de revisión",
        "referência oficial": "referencia oficial",
        "nota da referência": "nota de la referencia",
        "viabilidade da rota": "viabilidad de la ruta",
        "Arquivo identificado, mas não incluído na base ativa do observatório.": (
            "Archivo identificado, pero no incluido en la base activa del observatorio."
        ),
        "fora da base ativa": "fuera de la base activa",
        "Situação": "Situación",
        "Escopo": "Alcance",
        "Categoria de acesso": "Categoría de acceso",
        "Bloqueia expansão?": "¿Bloquea la expansión?",
        "Regra": "Regla",
        "Decisão e negativa metodológica": "Decisión y negativa metodológica",
        "Rotas candidatas avaliadas": "Rutas candidatas evaluadas",
        "Tentativas de verificação": "Intentos de verificación",
        "Rodadas registradas": "Rondas registradas",
        "Último escopo": "Último alcance",
        "Unidades avaliadas na última rodada": "Unidades evaluadas en la última ronda",
        "Pendências na última rodada": "Pendencias en la última ronda",
        "Acompanhamento das atualizações": "Seguimiento de las actualizaciones",
        "Atualizadas na última rodada": "Actualizadas en la última ronda",
        "Pendentes na rodada parcial": "Pendientes en la ronda parcial",
        "Atualizações atrasadas": "Actualizaciones atrasadas",
        "Rodada": "Ronda",
        "mais recente:": "más reciente:",
        "sucessos,": "éxitos,",
        "pendências, gerado em": "pendencias, generado en",
        "Ver distribuição dos estados de atualização": "Ver distribución de los estados de actualización",
        "Observações históricas das unidades": "Observaciones históricas de las unidades",
        "Observações históricas institucionais": "Observaciones históricas institucionales",
        "Sinais globais de possível extinção": "Señales globales de posible extinción",
        "Unidades com histórico registrado": "Unidades con historial registrado",
        "Exportar histórico geral das unidades": "Exportar historial general de las unidades",
        "Exporta a linha do tempo combinada das unidades do observatório.": (
            "Exporta la línea de tiempo combinada de las unidades del observatorio."
        ),
        "Este quadro acompanha a saúde temporal do observatório por unidade documental, distinguindo atualizações recentes, pendências de rodadas parciais e atrasos de acompanhamento.": (
            "Este cuadro acompaña la salud temporal del observatorio por unidad documental, distinguiendo "
            "actualizaciones recientes, pendientes de rondas parciales y retrasos de seguimiento."
        ),
        "Índice de dados públicos": "Índice de datos públicos",
        "O índice compara registros audiovisuais disponíveis em superfície pública com registros cujo acesso ao audiovisual exige pagamento, autenticação, cadastro ou licenciamento. Bancos privados/publicitários de imagens não entram no índice; permanecem documentados apenas na auditoria metodológica de acesso pago/restrito.": (
            "El índice compara registros audiovisuales disponibles en superficie pública con registros cuyo acceso "
            "al audiovisual exige pago, autenticación, registro o licenciamiento. Los bancos privados/publicitarios "
            "de imágenes no entran en el índice; permanecen documentados solo en la auditoría metodológica de acceso "
            "pago/restringido."
        ),
        "Índice público World": "Índice público mundial",
        "Índice público Europa": "Índice público europeo",
        "Registros restritos quantificados": "Registros restringidos cuantificados",
        "Unidades restritas no índice": "Unidades restringidas en el índice",
        "Mundo e continentes": "Mundo y continentes",
        "Por unidade documental": "Por unidad documental",
        "Acesso restrito": "Acceso restringido",
        "Linha do tempo e retração pública do audiovisual": "Línea de tiempo y retracción pública del audiovisual",
        "Esta camada reúne a memória histórica das unidades documentais e prepara o observatório para detectar ausências, indisponibilidades recorrentes e perda de evidência pública detectável de audiovisual.": (
            "Esta capa reúne la memoria histórica de las unidades documentales y prepara el observatorio para "
            "detectar ausencias, indisponibilidades recurrentes y pérdida de evidencia pública detectable de "
            "audiovisual."
        ),
        "Cada linha preserva uma observação histórica de uma unidade documental, mantendo explícita sua categoria analítica e escala de cobertura.": (
            "Cada línea preserva una observación histórica de una unidad documental, manteniendo explícitas su "
            "categoría analítica y escala de cobertura."
        ),
        "Os sinais abaixo não afirmam extinção por si só. Eles indicam mudanças que merecem observação longitudinal e interpretação metodológica cuidadosa.": (
            "Las señales siguientes no afirman extinción por sí solas. Indican cambios que merecen observación "
            "longitudinal e interpretación metodológica cuidadosa."
        ),
        "Unidades documentais ativas": "Unidades documentales activas",
        "Instituições no observatório": "Instituciones en el observatorio",
        "Links de vídeo detectados": "Enlaces de video detectados",
        "Vídeos no recorte curatorial": "Videos en el recorte curatorial",
        "Categorias analíticas do observatório": "Categorías analíticas del observatorio",
        "As categorias abaixo delimitam níveis diferentes de observação. Elas são comparáveis, mas não são tratadas como equivalentes do ponto de vista metodológico.": (
            "Las categorías siguientes delimitan niveles distintos de observación. Son comparables, pero no se "
            "tratan como equivalentes desde el punto de vista metodológico."
        ),
        "Estratégia de expansão": "Estrategia de expansión",
        "O organismo cresce primeiro por agregadores continentais e, depois, incorpora arquivos e instituições não cobertos por esses agregadores.": (
            "El organismo crece primero por agregadores continentales y, después, incorpora archivos e instituciones "
            "no cubiertos por esos agregadores."
        ),
        "Fila de expansão do observatório": "Cola de expansión del observatorio",
        "A fila abaixo é gerada por regra pública e reprodutível. Neste momento, ela prioriza o fechamento da Europa antes da abertura sistemática de novos continentes.": (
            "La cola siguiente se genera mediante una regla pública y reproducible. En este momento, prioriza el "
            "cierre de Europa antes de la apertura sistemática de nuevos continentes."
        ),
        "Cada linha mostra uma unidade potencial, a decisão automática aplicada e o próximo passo sugerido pelo protocolo do organismo.": (
            "Cada línea muestra una unidad potencial, la decisión automática aplicada y el próximo paso sugerido por "
            "el protocolo del organismo."
        ),
        "Avaliação metodológica dos agregadores europeus": "Evaluación metodológica de los agregadores europeos",
        "Esta camada não incorpora novas unidades automaticamente. Ela observa a superfície pública de Archives Hub, FranceArchives, PARES e Portal Português de Arquivos para decidir, com evidência registrada, qual fonte pode seguir para validação total e qual exige nova rota de acesso.": (
            "Esta capa no incorpora nuevas unidades automáticamente. Observa la superficie pública de Archives Hub, "
            "FranceArchives, PARES y el Portal Portugués de Archivos para decidir, con evidencia registrada, qué "
            "fuente puede seguir hacia validación total y cuál exige una nueva ruta de acceso."
        ),
        "Os registros preliminares de busca somam os resultados brutos retornados nas verificações dos agregadores. Eles não equivalem a vídeos incorporados ao corpus: indicam apenas volume potencial a validar, deduplicar e classificar.": (
            "Los registros preliminares de búsqueda suman los resultados brutos devueltos en las verificaciones de "
            "los agregadores. No equivalen a videos incorporados al corpus: indican solo volumen potencial que debe "
            "validarse, deduplicarse y clasificarse."
        ),
        "Esta matriz separa decisão metodológica de disponibilidade técnica: uma fonte pode ser relevante para o fechamento europeu e, ainda assim, permanecer fora das unidades ativas até existir uma rota estável de acesso.": (
            "Esta matriz separa la decisión metodológica de la disponibilidad técnica: una fuente puede ser relevante "
            "para el cierre europeo y, aun así, permanecer fuera de las unidades activas hasta que exista una ruta "
            "estable de acceso."
        ),
        "Estas rotas não promovem automaticamente uma fonte a unidade ativa. Elas registram caminhos oficiais ou documentados que podem ser testados antes da incorporação.": (
            "Estas rutas no promueven automáticamente una fuente a unidad activa. Registran caminos oficiales o "
            "documentados que pueden probarse antes de la incorporación."
        ),
        "Este quadro testa SRU e OAI-PMH em modo mínimo, sem promover o Archives Hub a unidade ativa enquanto a rota de acesso não estiver estável.": (
            "Este cuadro prueba SRU y OAI-PMH en modo mínimo, sin promover Archives Hub a unidad activa mientras la "
            "ruta de acceso no sea estable."
        ),
        "Este quadro testa sinais mínimos de viabilidade técnica para FranceArchives sem transferir integralmente o pacote XML e sem transformar a fonte em unidade ativa.": (
            "Este cuadro prueba señales mínimas de viabilidad técnica para FranceArchives sin transferir "
            "íntegramente el paquete XML y sin transformar la fuente en unidad activa."
        ),
        "Fechamento da etapa Europa": "Cierre de la etapa Europa",
        "Este quadro explicita o estado metodológico da etapa Europa. Ele não afirma que todos os arquivos audiovisuais europeus foram identificados; registra o que já opera como unidade ativa, o que está protocolado e o que segue em fila auditável de expansão.": (
            "Este cuadro explicita el estado metodológico de la etapa Europa. No afirma que todos los archivos "
            "audiovisuales europeos hayan sido identificados; registra lo que ya opera como unidad activa, lo que "
            "está protocolado y lo que continúa en una cola auditable de expansión."
        ),
        "Essas unidades foram identificadas e preservadas no observatório, mas não entram na base ativa enquanto a rota de coleta não for estável e reprodutível.": (
            "Estas unidades fueron identificadas y preservadas en el observatorio, pero no entran en la base activa "
            "mientras la ruta de recolección no sea estable y reproducible."
        ),
        "Esta auditoria separa bancos privados pagos, catálogos comerciais de licenciamento e streaming pago/autenticado. Nem todo acesso comercial fica fora da base ativa: quando há registros públicos avaliados no observatório, ele permanece como modalidade analítica própria.": (
            "Esta auditoría separa bancos privados pagos, catálogos comerciales de licenciamiento y streaming "
            "pago/autenticado. No todo acceso comercial queda fuera de la base activa: cuando hay registros públicos "
            "evaluados en el observatorio, permanece como modalidad analítica propia."
        ),
        "Esta auditoria impede que o fechamento europeu seja lido como exaustividade absoluta. Ela documenta unidades cobertas por bases ativas, fontes legadas, radares e candidatos futuros, mantendo o MVP continental aberto à expansão controlada.": (
            "Esta auditoría impide que el cierre europeo sea leído como exhaustividad absoluta. Documenta unidades "
            "cubiertas por bases activas, fuentes heredadas, radares y candidatos futuros, manteniendo el MVP "
            "continental abierto a una expansión controlada."
        ),
        "Mapeamento europeu ampliado": "Mapeo europeo ampliado",
        "Este módulo separa o registro europeu completo da fila operacional de pendências. Ele identifica agregadores, redes, diretórios e arquivos audiovisuais europeus sem chute: agregadores primeiro, diretórios especializados depois, arquivos individuais por expansão controlada. A varredura de fontes oficiais inclui Europeana, FIAF, EFG, EUscreen, FIAT/IFTA, INEDITS, ACE e EBU. A presença no registro não significa incorporação automática; a presença na fila significa análise pendente.": (
            "Este módulo separa el registro europeo completo de la cola operacional de pendientes. Identifica "
            "agregadores, redes, directorios y archivos audiovisuales europeos sin suposiciones: primero "
            "agregadores, después directorios especializados y luego archivos individuales por expansión "
            "controlada. La revisión de fuentes oficiales incluye Europeana, FIAF, EFG, EUscreen, FIAT/IFTA, "
            "INEDITS, ACE y EBU. La presencia en el registro no significa incorporación automática; la presencia "
            "en la cola significa análisis pendiente."
        ),
        "Unidades europeias ativas": "Unidades europeas activas",
        "Candidatos em avaliação": "Candidatos en evaluación",
        "Identificados fora da base ativa": "Identificados fuera de la base activa",
        "Lacunas auditadas": "Lagunas auditadas",
        "Unidades europeias mapeadas": "Unidades europeas mapeadas",
        "Agregador audiovisual europeu": "Agregador audiovisual europeo",
        "Agregadores nacionais europeus": "Agregadores nacionales europeos",
        "Lacunas europeias": "Lagunas europeas",
        "Unidades já incorporadas": "Unidades ya incorporadas",
        "Agregadores avaliados": "Agregadores evaluados",
        "Prontos para validação total": "Listos para validación total",
        "Exigem nova rota de acesso": "Exigen nueva ruta de acceso",
        "Registros preliminares de busca": "Registros preliminares de búsqueda",
        "Rotas oficiais analisadas": "Rutas oficiales analizadas",
        "Verificação metodológica do Archives Hub": "Verificación metodológica de Archives Hub",
        "Verificação metodológica do FranceArchives": "Verificación metodológica de FranceArchives",
        "Ver verificações realizadas": "Ver verificaciones realizadas",
        "Próxima etapa": "Próxima etapa metodológica",
        "Ver posição dessas unidades na fila europeia": "Ver posición de estas unidades en la cola europea",
        "Próximas análises individuais": "Análisis individuales siguientes",
        "Diretórios a expandir": "Directorios por expandir",
        "Ver tabela detalhada de regimes": "Ver tabla detallada de regímenes",
        "Ver tabela detalhada de modalidades": "Ver tabla detallada de modalidades",
        "Comparações entre unidades documentais": "Comparaciones entre unidades documentales",
        "Estes quadros mostram como as unidades diferem não apenas em volume, mas também na forma como o audiovisual se torna publicamente acessível.": (
            "Estos cuadros muestran cómo las unidades difieren no solo en volumen, sino también en la forma en que "
            "el audiovisual se vuelve públicamente accesible."
        ),
        "Linhas representam unidades documentais; colunas representam regimes institucionais de acesso audiovisual detectável.": (
            "Las filas representan unidades documentales; las columnas representan regímenes institucionales de "
            "acceso audiovisual detectable."
        ),
        "Linhas representam unidades documentais; colunas representam modalidades públicas de acesso encontradas nos catálogos.": (
            "Las filas representan unidades documentales; las columnas representan modalidades públicas de acceso "
            "encontradas en los catálogos."
        ),
        "Histórico do observatório": "Histórico del observatorio",
        "Cada linha representa uma rodada do observatório, permitindo acompanhar cadência, escopo e estabilidade das atualizações ao longo do tempo.": (
            "Cada línea representa una ronda del observatorio, lo que permite acompañar cadencia, alcance y "
            "estabilidad de las actualizaciones a lo largo del tiempo."
        ),
        "Este quadro preserva o desempenho de cada unidade documental em cada rodada do observatório.": (
            "Este cuadro preserva el desempeño de cada unidad documental en cada ronda del observatorio."
        ),
        "Estes arquivos preservam a rastreabilidade global do observatório, permitindo auditar rodadas, unidades ativas e resultados históricos.": (
            "Estos archivos preservan la trazabilidad global del observatorio, permitiendo auditar rondas, unidades "
            "activas y resultados históricos."
        ),
        "Unidades na categoria": "Unidades en la categoría",
        "Instituições no recorte": "Instituciones en el recorte",
        "Instituições com links de vídeo": "Instituciones con enlaces de video",
        "Unidades desta categoria": "Unidades de esta categoría",
        "Princípio de separação": "Principio de separación",
        "Instituições da categoria": "Instituciones de la categoría",
        "Vídeos da categoria": "Videos de la categoría",
        "Todas as unidades": "Todas las unidades",
        "Todas as situações": "Todas las situaciones",
        "Todos os temas": "Todos los temas",
        "Todas as modalidades": "Todas las modalidades",
        "Unidade documental": "Unidad documental",
        "Situação metodológica": "Situación metodológica",
        "Buscar instituição, país ou domínio": "Buscar institución, país o dominio",
        "Tema": "Tema",
        "Plataformas": "Plataformas",
        "Continentes": "Continentes",
        "Continente": "Continente",
        "País": "País de la institución",
        "Links de vídeo": "Enlaces de video",
        "Sinais embutidos": "Señales incrustadas",
        "Modalidade de acesso": "Modalidad de acceso",
        "Regime de acesso audiovisual": "Régimen de acceso audiovisual",
        "Tipo de arquivo": "Tipo de archivo",
        "Integridade": "Integridad",
        "Segmento institucional": "Segmento de la institución",
        "Somente com links de vídeo": "Solo con enlaces de video",
        "Busca textual": "Búsqueda textual",
        "Instituição, país, domínio ou código": "Institución, país, dominio o código",
        "Seleção do recorte": "Selección del recorte",
        "Recorte da lista": "Recorte de la lista",
        "Selecione uma instituição": "Seleccione una institución",
        "Tema dos vídeos": "Tema de los videos",
        "Instituições com site informado": "Instituciones con sitio informado",
        "Sites íntegros": "Sitios íntegros",
        "Evidência pública detectável": "Evidencia pública detectable",
        "Evidência indireta": "Evidencia indirecta",
        "Potencial em navegação interna": "Potencial en navegación interna",
        "Sem evidência pública detectável": "Sin evidencia pública detectable",
        "Site indisponível para verificação": "Sitio no disponible para verificación",
        "Condição dos sites institucionais": "Condición de los sitios institucionales",
        "Disponibilidade institucional": "Disponibilidad institucional",
        "Categorias": "Categorías",
        "Subcategorias": "Subcategorías",
        "Visibilidade do audiovisual": "Visibilidad del audiovisual",
        "Regimes de acesso audiovisual detectáveis": "Regímenes de acceso audiovisual detectables",
        "Modalidades de acesso detectadas": "Modalidades de acceso detectadas",
        "Tipo institucional declarado na fonte": "Tipo institucional declarado en la fuente",
        "Temas dos vídeos": "Temas de los videos",
        "Locais de acesso detectados": "Lugares de acceso detectados",
        "Temas por plataforma": "Temas según plataforma",
        "Temas por país": "Temas según país",
        "Temas por tipo de arquivo": "Temas por tipo de archivo",
        "Visibilidade por tipo de arquivo": "Visibilidad por tipo de archivo",
        "Casos indisponíveis": "Casos no disponibles",
        "Casos com site quebrado": "Casos con sitio roto",
        "Casos instáveis": "Casos inestables",
        "Distribuição geográfica das instituições com evidência pública detectável de audiovisual": (
            "Distribución geográfica de las instituciones con evidencia pública detectable de audiovisual"
        ),
        "Sobre o recorte APE": "Sobre el recorte APE",
        "Sobre o recorte": "Sobre el recorte",
        "Ver referência de classificação": "Ver referencia de clasificación",
        "Ver arquivos de referência desta unidade": "Ver archivos de referencia de esta unidad",
        "Temas identificados": "Temas identificados por la curaduría",
        "Locais de acesso": "Lugares de acceso",
        "#### Distribuição temática": "#### Distribución temática",
        "Organização dos vídeos": "Organización de los videos",
        "Ver sínteses do catálogo de vídeos": "Ver síntesis del catálogo de videos",
        "Distribuição por continente": "Distribución por continente",
        "Distribuição por país": "Distribución por país",
        "Filtrar continentes": "Filtrar por continente",
        "#### Consulta das tabelas": "#### Consulta de las tablas",
        "Selecione a tabela": "Seleccione la tabla",
        "Com site informado na fonte": "Con sitio informado en la fuente",
        "Com evidência pública detectável": "Con evidencia pública detectable",
        "Indisponíveis no recorte": "No disponibles en el recorte",
        "Ver tabela completa do recorte": "Ver tabla completa del recorte",
        "Resposta do site": "Respuesta del sitio",
        "Páginas internas": "Páginas internas verificadas",
        "Leitura metodológica": "Lectura metodológica",
        "Fontes e endereços": "Fuentes y direcciones",
        "Abrir": "Abrir",
        "Temas sugeridos": "Temas sugeridos por la clasificación",
        "Páginas verificadas": "Páginas verificadas por la colecta",
        "Links encontrados nessas páginas": "Enlaces encontrados en esas páginas",
        "Sinais embutidos nessas páginas": "Señales incrustadas en esas páginas",
        "Esta aba existe justamente para não apagar a tentativa. A unidade aparece no observatório, mas fica separada das unidades ativas até que a rota de coleta seja estável, reprodutível e comparável.": (
            "Esta pestaña existe precisamente para no borrar el intento. La unidad aparece en el observatorio, pero "
            "permanece separada de las unidades activas hasta que la ruta de recolección sea estable, reproducible "
            "y comparable."
        ),
        "Leitura correta: a não inclusão não prova inexistência de audiovisual. Ela prova apenas que, nesta rodada, o observatório não encontrou uma rota suficientemente estável para coleta com rigor.": (
            "Lectura correcta: la no inclusión no prueba la inexistencia de audiovisual. Solo prueba que, en esta "
            "ronda, el observatorio no encontró una ruta suficientemente estable para una recolección rigurosa."
        ),
        "O painel organiza a leitura do observatório em três camadas: síntese institucional, análise temática e detalhamento dos casos que exigem atenção metodológica.": (
            "El panel organiza la lectura del observatorio en tres capas: síntesis institucional, análisis temático "
            "y detalle de los casos que exigen atención metodológica."
        ),
        "Esta distribuição exclui, por padrão, ruído de plataforma ou incorporação externa.": (
            "Esta distribución excluye, por defecto, ruido de plataforma o incorporación externa."
        ),
        "Dentro de 'quebrado', o observatório distingue erro explícito e página suspeita.": (
            "Dentro de 'roto', el observatorio distingue error explícito y página sospechosa."
        ),
        "Esta aba reúne as instituições em cujos sites a coleta encontrou ao menos um link explícito de vídeo.": (
            "Esta pestaña reúne las instituciones en cuyos sitios la recolección encontró al menos un enlace "
            "explícito de video."
        ),
        "Este catálogo organiza o recorte curatorial de vídeos a partir de metadados básicos e de uma classificação temática baseada em título, assunto e descrição, excluindo por padrão o ruído de plataforma ou incorporação externa.": (
            "Este catálogo organiza el recorte curatorial de videos a partir de metadatos básicos y de una "
            "clasificación temática basada en título, asunto y descripción, excluyendo por defecto el ruido de "
            "plataforma o incorporación externa."
        ),
        "Este quadro considera as instituições nas quais a coleta encontrou ao menos um link explícito de vídeo.": (
            "Este cuadro considera las instituciones en las que la recolección encontró al menos un enlace explícito "
            "de video."
        ),
        "Esta aba reúne as principais tabelas derivadas do recorte e permite exportá-las para pesquisa, redação, revisão metodológica e documentação.": (
            "Esta pestaña reúne las principales tablas derivadas del recorte y permite exportarlas para investigación, "
            "redacción, revisión metodológica y documentación."
        ),
        "Cada linha representa uma unidade institucional do recorte, complementada pela verificação do site externo informado na fonte.": (
            "Cada línea representa una unidad institucional del recorte, complementada por la verificación del sitio "
            "externo informado en la fuente."
        ),
        "Este quadro reúne apenas instituições pertencentes a corpora da mesma categoria analítica, evitando mistura entre agregadores e instituições custodiais.": (
            "Este cuadro reúne solo instituciones pertenecientes a corpus de la misma categoría analítica, evitando "
            "mezclar agregadores e instituciones custodias."
        ),
        "### Linha do tempo e retração pública do audiovisual": "### Línea de tiempo y retracción pública del audiovisual",
        "### Categorias analíticas do observatório": "### Categorías analíticas del observatorio",
        "### Fila de expansão do observatório": "### Cola de expansión del observatorio",
        "### Avaliação metodológica dos agregadores europeus": "### Evaluación metodológica de los agregadores europeos",
        "### Comparações entre unidades documentais": "### Comparaciones entre unidades documentales",
        "#### Tabelas disponíveis para exportação": "#### Tablas disponibles para exportación",
        "#### Matriz de decisão de incorporação": "#### Matriz de decisión de incorporación",
        "A avaliação dos agregadores europeus ainda não está disponível nesta versão do observatório.": (
            "La evaluación de los agregadores europeos aún no está disponible en esta versión del observatorio."
        ),
        "O relatório de fechamento europeu ainda não está disponível nesta versão do observatório.": (
            "El informe de cierre europeo aún no está disponible en esta versión del observatorio."
        ),
        "O mapeamento europeu ampliado ainda não está disponível.": (
            "El mapeo europeo ampliado aún no está disponible."
        ),
        "Instituições com links de vídeo por unidade": "Instituciones con enlaces de video por unidad",
        "Links de vídeo detectados por unidade": "Enlaces de video detectados por unidad",
        "Vídeos no recorte curatorial por unidade": "Videos en el recorte curatorial por unidad",
        "Este observatório investiga a visibilidade pública do audiovisual em ambientes arquivísticos na web. Nesta etapa, a unidade analisada é o **Archives Portal Europe (APE)**, tratado como um portal arquivístico geral, e não como um repositório especializado em audiovisual. **Objetivo** Examinar como o audiovisual se torna publicamente visível, detectável e acessível nos sites institucionais vinculados ao APE, considerando tanto a presença explícita quanto formas mais indiretas de evidência. **Princípio metodológico** A ausência de vídeo detectado não autoriza afirmar, por si só, ausência de acervo audiovisual. No contexto de um portal geral, a não detecção pode indicar pelo menos quatro situações: - o acervo audiovisual pode não existir; - o acervo pode existir, mas não estar digitalizado; - o acervo pode estar digitalizado, mas não público; - o acervo pode estar público, porém pouco visível ou não detectável com a estratégia atual de coleta. Neste observatório, fontes gerais como o APE podem permanecer mapeadas mesmo quando parte de suas instituições retorna zero audiovisual, porque esse zero também é analiticamente informativo para o estudo da visibilidade pública do acervo.": (
            "Este observatorio investiga la visibilidad pública del audiovisual en entornos archivísticos en la web. "
            "En esta etapa, la unidad analizada es el **Archives Portal Europe (APE)**, tratado como un portal "
            "archivístico general y no como un repositorio especializado en audiovisual. **Objetivo** Examinar cómo "
            "el audiovisual se vuelve públicamente visible, detectable y accesible en los sitios institucionales "
            "vinculados al APE, considerando tanto la presencia explícita como formas más indirectas de evidencia. "
            "**Principio metodológico** La ausencia de video detectado no autoriza afirmar, por sí sola, ausencia de "
            "acervo audiovisual. En el contexto de un portal general, la no detección puede indicar al menos cuatro "
            "situaciones: - el acervo audiovisual puede no existir; - el acervo puede existir, pero no estar "
            "digitalizado; - el acervo puede estar digitalizado, pero no ser público; - el acervo puede ser público, "
            "pero poco visible o no detectable con la estrategia actual de recolección. En este observatorio, fuentes "
            "generales como el APE pueden permanecer mapeadas incluso cuando parte de sus instituciones retorna cero "
            "audiovisual, porque ese cero también es analíticamente informativo para el estudio de la visibilidad "
            "pública del acervo."
        ),
        "**Eixo interpretativo** A plataforma observa a circulação audiovisual como um fenômeno territorial, cultural e técnico. O problema não é apenas localizar vídeos, mas compreender quem hospeda, quem indexa, quem descreve, em qual idioma, sob qual regime de acesso, por qual plataforma e em que escala territorial esse audiovisual se torna público. **O que a plataforma afirma com maior segurança** - quando há evidência pública detectável de audiovisual; - quando há apenas evidência pública indireta; - quando não foi encontrada evidência pública detectável de audiovisual; - quando o site não pôde ser verificado. **O que a plataforma evita afirmar** - que a ausência de evidência pública detectável equivale à inexistência de acervo audiovisual; - que a visibilidade pública esgota a complexidade do acervo; - que uma única coleta resolve o problema da descrição e do acesso audiovisual.": (
            "**Eje interpretativo** La plataforma observa la circulación audiovisual como un fenómeno territorial, "
            "cultural y técnico. El problema no es solo localizar videos, sino comprender quién aloja, quién indexa, "
            "quién describe, en qué idioma, bajo qué régimen de acceso, por qué plataforma y en qué escala territorial "
            "ese audiovisual se vuelve público. **Lo que la plataforma afirma con mayor seguridad** - cuando hay "
            "evidencia pública detectable de audiovisual; - cuando hay solo evidencia pública indirecta; - cuando no "
            "se encontró evidencia pública detectable de audiovisual; - cuando el sitio no pudo ser verificado. **Lo "
            "que la plataforma evita afirmar** - que la ausencia de evidencia pública detectable equivale a la "
            "inexistencia de acervo audiovisual; - que la visibilidad pública agota la complejidad del acervo; - que "
            "una única recolección resuelve el problema de la descripción y del acceso audiovisual."
        ),
        "Nenhuma instituição corresponde aos filtros selecionados.": (
            "Ninguna institución corresponde a los filtros seleccionados."
        ),
        "Situação metodológica do audiovisual": "Situación metodológica del audiovisual",
        "O site externo respondeu. Esta instituição pode seguir para curadoria pública.": (
            "El sitio externo respondió. Esta institución puede seguir hacia la curaduría pública."
        ),
        "Ainda não há histórico geral disponível para o observatório.": (
            "Todavía no hay historial general disponible para el observatorio."
        ),
        "Ainda não há sinais globais registrados. Isso é esperado enquanto o organismo acumula mais rodadas históricas para comparação.": (
            "Todavía no hay señales globales registradas. Esto es esperado mientras el organismo acumula más rondas "
            "históricas para comparación."
        ),
        "Ainda não há dados suficientes para comparar regimes de acesso entre unidades.": (
            "Todavía no hay datos suficientes para comparar regímenes de acceso entre unidades."
        ),
        "Ainda não há dados suficientes para comparar modalidades de acesso entre unidades.": (
            "Todavía no hay datos suficientes para comparar modalidades de acceso entre unidades."
        ),
        "Ainda não há unidades disponíveis nesta categoria.": (
            "Todavía no hay unidades disponibles en esta categoría."
        ),
        "Ainda não há instituições disponíveis nesta categoria.": (
            "Todavía no hay instituciones disponibles en esta categoría."
        ),
        "Ainda não há vídeos curatoriais disponíveis nesta categoria.": (
            "Todavía no hay videos curatoriales disponibles en esta categoría."
        ),
        "Neste caso, a unidade continua relevante como fonte geral de pesquisa. O retorno zero indica que, até aqui, não houve evidência pública detectável de audiovisual nas instituições mapeadas por esta coleta.": (
            "En este caso, la unidad continúa siendo relevante como fuente general de investigación. El retorno cero "
            "indica que, hasta aquí, no hubo evidencia pública detectable de audiovisual en las instituciones "
            "mapeadas por esta recolección."
        ),
        "Como esta é uma fonte geral de pesquisa, o retorno zero não invalida a unidade. Ele indica apenas ausência de evidência pública detectável de audiovisual nesta rodada.": (
            "Como esta es una fuente general de investigación, el retorno cero no invalida la unidad. Indica solo "
            "ausencia de evidencia pública detectable de audiovisual en esta ronda."
        ),
        "Nenhum vídeo corresponde ao tema e aos filtros selecionados.": (
            "Ningún video corresponde al tema y a los filtros seleccionados."
        ),
        "Ainda não há distribuição geográfica com links de vídeo detectados.": (
            "Todavía no hay distribución geográfica con enlaces de video detectados."
        ),
        "O site respondeu, mas a página final parece genérica, suspensa ou não confiável. Aqui ele entra dentro da categoria quebrado.": (
            "El sitio respondió, pero la página final parece genérica, suspendida o no confiable. Aquí entra dentro "
            "de la categoría roto."
        ),
        "Nenhum link de vídeo foi localizado automaticamente para esta instituição.": (
            "Ningún enlace de video fue localizado automáticamente para esta institución."
        ),
        "Nenhuma página complementar foi analisada para esta instituição.": (
            "Ninguna página complementaria fue analizada para esta institución."
        ),
        "Nenhuma instituição se enquadra neste recorte; a lista completa foi restaurada.": (
            "Ninguna institución se encuadra en este recorte; la lista completa fue restaurada."
        ),
        "Ainda não há índice por unidade documental disponível.": (
            "Todavía no hay índice por unidad documental disponible."
        ),
        "Ainda não há unidades restritas registradas no índice.": (
            "Todavía no hay unidades restringidas registradas en el índice."
        ),
        "Esta tabela mostra apenas unidades restritas que fazem parte do índice. Bancos privados/publicitários ficam fora deste recorte.": (
            "Esta tabla muestra solo unidades restringidas que forman parte del índice. Los bancos privados/"
            "publicitarios quedan fuera de este recorte."
        ),
        "A matriz de fechamento europeu ainda não está disponível.": (
            "La matriz de cierre europeo aún no está disponible."
        ),
        "Ainda não há unidades europeias documentadas fora da base ativa.": (
            "Todavía no hay unidades europeas documentadas fuera de la base activa."
        ),
        "A auditoria de acesso pago/restrito ainda não está disponível.": (
            "La auditoría de acceso pago/restringido aún no está disponible."
        ),
        "A auditoria de lacunas europeias ainda não está disponível.": (
            "La auditoría de lagunas europeas aún no está disponible."
        ),
        "Ainda não há resultados históricos disponíveis por unidade.": (
            "Todavía no hay resultados históricos disponibles por unidad."
        ),
        "Ainda não há dados suficientes para analisar a visibilidade do audiovisual.": (
            "Todavía no hay datos suficientes para analizar la visibilidad del audiovisual."
        ),
        "Ainda não há dados suficientes para resumir os regimes de acesso audiovisual.": (
            "Todavía no hay datos suficientes para resumir los regímenes de acceso audiovisual."
        ),
        "Ainda não há dados suficientes para resumir as modalidades de acesso.": (
            "Todavía no hay datos suficientes para resumir las modalidades de acceso."
        ),
        "Ainda não há dados suficientes para resumir o tipo institucional declarado na fonte.": (
            "Todavía no hay datos suficientes para resumir el tipo institucional declarado en la fuente."
        ),
        "Ainda não há temas classificados para os vídeos.": (
            "Todavía no hay temas clasificados para los videos."
        ),
        "Nenhum link de vídeo foi detectado ainda.": "Ningún enlace de video fue detectado todavía.",
        "Ainda não há dados suficientes para cruzar temas e plataformas.": (
            "Todavía no hay datos suficientes para cruzar temas y plataformas."
        ),
        "Nenhum caso enquadrado como quebrado foi detectado nesta rodada.": (
            "Ningún caso encuadrado como roto fue detectado en esta ronda."
        ),
        "Nenhum caso instável foi detectado nesta rodada.": (
            "Ningún caso inestable fue detectado en esta ronda."
        ),
        "Ainda não há modalidades de acesso classificadas.": (
            "Todavía no hay modalidades de acceso clasificadas."
        ),
        "O site respondeu com restrição de acesso. Para o projeto, ele entra como não disponível.": (
            "El sitio respondió con restricción de acceso. Para el proyecto, entra como no disponible."
        ),
        "Nenhum vídeo permaneceu no recorte curatorial após a filtragem de ruído fora de escopo.": (
            "Ningún video permaneció en el recorte curatorial después del filtrado de ruido fuera de alcance."
        ),
        "Ainda não há dados suficientes para cruzar temas e países.": (
            "Todavía no hay datos suficientes para cruzar temas y países."
        ),
        "Ainda não há dados suficientes para cruzar temas e tipos institucionais.": (
            "Todavía no hay datos suficientes para cruzar temas y tipos institucionales."
        ),
        "Ainda não há dados suficientes para cruzar visibilidade e tipos institucionais.": (
            "Todavía no hay datos suficientes para cruzar visibilidad y tipos institucionales."
        ),
        "A fonte não informa um site externo para esta instituição.": (
            "La fuente no informa un sitio externo para esta institución."
        ),
        "O site institucional não respondeu de forma confiável. Para o projeto, esta instituição entra como não disponível.": (
            "El sitio institucional no respondió de forma confiable. Para el proyecto, esta institución entra como no "
            "disponible."
        ),
        "Ainda não há linha do tempo disponível para este recorte.": (
            "Todavía no hay línea de tiempo disponible para este recorte."
        ),
        "Ainda não há sinais registrados nesta rodada. Isso pode significar estabilidade ou ausência de histórico suficiente para comparação.": (
            "Todavía no hay señales registradas en esta ronda. Esto puede significar estabilidad o ausencia de "
            "historial suficiente para comparación."
        ),
        "Ainda não há linha do tempo institucional disponível para este recorte.": (
            "Todavía no hay línea de tiempo institucional disponible para este recorte."
        ),
        "Vídeos localizados na instituição": "Videos localizados en la institución",
        "Categoria:": "Categoría:",
        "Subcategoria:": "Subcategoría:",
        "Domínio:": "Dominio:",
        "Situação da verificação:": "Situación de la verificación:",
        "Links de vídeo:": "Enlaces de video:",
        "Sinais embutidos:": "Señales incrustadas:",
        "Tipo de arquivo:": "Tipo de archivo:",
        "Plataformas detectadas:": "Plataformas identificadas:",
        ": ainda sem dados para exportação.": ": todavía sin datos para exportación.",
        "Etapa 1": "Etapa 1",
        "Etapa 2": "Etapa 2",
        "da expansão.": "de la expansión.",
        "Regra audiovisual desta categoria:": "Regla audiovisual de esta categoría:",
        "Critério de entrada nesta etapa:": "Criterio de entrada en esta etapa:",
        "Categoria analítica:": "Categoría analítica:",
        "Etapa de expansão:": "Etapa de expansión:",
        "Unidade do observatório:": "Unidad del observatorio:",
        "Política de expansão aplicável:": "Política de expansión aplicable:",
        "Regra audiovisual do recorte:": "Regla audiovisual del recorte:",
        "Leitura metodológica de retorno zero:": "Lectura metodológica de retorno cero:",
        "Fonte-base com status de": "Fuente base con estado de",
        "Fonte-base sem data pública de status declarada nos metadados.": (
            "Fuente base sin fecha pública de estado declarada en los metadatos."
        ),
        "Camada analítica atualizada em": "Capa analítica actualizada en",
        "Metadados da rodada gerados em": "Metadatos de la ronda generados en",
        "Nenhum relatório de": "Ningún informe de",
        "O relatório de": "El informe de",
        "está disponível nesta versão do observatório.": "está disponible en esta versión del observatorio.",
        "está disponível, mas não trouxe instituições para análise.": (
            "está disponible, pero no trajo instituciones para análisis."
        ),
        "não trouxe identificadores institucionais suficientes para navegação.": (
            "no trajo identificadores institucionales suficientes para navegación."
        ),
        "As verificações registram respostas dos sites, bloqueios por JS/cookies, problemas de TLS e contagens preliminares. Total de verificações bloqueadas:": (
            "Las verificaciones registran respuestas de los sitios, bloqueos por JS/cookies, problemas de TLS y "
            "conteos preliminares. Total de verificaciones bloqueadas:"
        ),
        "Esta categoria reúne apenas unidades classificadas como": (
            "Esta categoría reúne solo unidades clasificadas como"
        ),
        "O observatório permite trabalhar com todas elas em conjunto, mas sempre preservando o mesmo nível analítico:": (
            "El observatorio permite trabajar con todas ellas en conjunto, pero siempre preservando el mismo nivel "
            "analítico:"
        ),
        "Este recorte toma o **": "Este recorte toma el **",
        "** como unidade especializada em audiovisual.": "** como unidad especializada en audiovisual.",
        "Diferentemente do APE, que funciona como portal geral de arquivos, aqui o audiovisual tende a ocupar uma posição institucional central.": (
            "A diferencia del APE, que funciona como portal general de archivos, aquí el audiovisual tiende a ocupar "
            "una posición institucional central."
        ),
        "Examinar como um arquivo explicitamente audiovisual organiza a presença pública de seus vídeos, coleções, descrições e mediações digitais.": (
            "Examinar cómo un archivo explícitamente audiovisual organiza la presencia pública de sus videos, "
            "colecciones, descripciones y mediaciones digitales."
        ),
        "Neste recorte, a questão central já não é apenas a existência de evidência pública detectável, mas a forma como um arquivo especializado apresenta, contextualiza e distribui seu audiovisual na web institucional.": (
            "En este recorte, la cuestión central ya no es solo la existencia de evidencia pública detectable, sino "
            "la forma en que un archivo especializado presenta, contextualiza y distribuye su audiovisual en la web "
            "institucional."
        ),
        "Nenhum link de vídeo foi localizado ainda no recorte": (
            "Ningún enlace de video fue localizado todavía en el recorte"
        ),
        "Tema selecionado:": "Tema seleccionado:",
        "vídeos no recorte atual.": "videos en el recorte actual.",
        "Instituições analisadas em": "Instituciones analizadas en",
        "Problema registrado na verificação:": "Problema registrado en la verificación:",
        "Plataforma:": "Plataforma de acceso:",
        "Tema sugerido:": "Tema sugerido por la clasificación:",
        "Modalidade de acesso:": "Modalidad de acceso:",
        "Data de publicação:": "Fecha de publicación:",
        "Abrir site institucional": "Abrir sitio institucional",
        "Infraestruturas que reúnem descrições, metadados e links de múltiplas instituições arquivísticas.": (
            "Infraestructuras que reúnen descripciones, metadatos y enlaces de múltiples instituciones archivísticas."
        ),
        "Nesta categoria, a unidade analítica central é o conjunto de instituições agregadas pela plataforma, e não a plataforma como se fosse um único arquivo.": (
            "En esta categoría, la unidad analítica central es el conjunto de instituciones agregadas por la "
            "plataforma, y no la plataforma como si fuera un único archivo."
        ),
        "Entram primeiro na expansão do observatório, porque ampliam cobertura de forma mais rápida, comparável e metodologicamente sólida.": (
            "Entran primero en la expansión del observatorio, porque amplían la cobertura de forma más rápida, "
            "comparable y metodológicamente sólida."
        ),
        "Agregadores continentais, supranacionais ou de grande escala que reúnam múltiplas instituições arquivísticas e permitam extração comparável.": (
            "Agregadores continentales, supranacionales o de gran escala que reúnan múltiples instituciones "
            "archivísticas y permitan extracción comparable."
        ),
        "instituições agregadas": "instituciones agregadas",
        "Podem integrar o observatório mesmo quando retornam zero arquivos audiovisuais, desde que funcionem como fonte comparável de pesquisa para localizar ou testar a presença pública do audiovisual.": (
            "Pueden integrar el observatorio incluso cuando retornan cero archivos audiovisuales, siempre que "
            "funcionen como fuente comparable de investigación para localizar o probar la presencia pública del "
            "audiovisual."
        ),
        "Arquivos e instituições custodiais tomados como unidade própria de observação, com autonomia institucional e superfície pública específica.": (
            "Archivos e instituciones custodias tomados como unidad propia de observación, con autonomía "
            "institucional y superficie pública específica."
        ),
        "Nesta categoria, a unidade analítica é o próprio arquivo ou instituição arquivística, tratada como corpus autônomo.": (
            "En esta categoría, la unidad analítica es el propio archivo o institución archivística, tratada como "
            "corpus autónomo."
        ),
        "Entram após os agregadores, preenchendo lacunas e incorporando instituições que não estejam cobertas pelas infraestruturas agregadoras.": (
            "Entran después de los agregadores, llenando lagunas e incorporando instituciones que no estén cubiertas "
            "por las infraestructuras agregadoras."
        ),
        "Instituições individuais não cobertas pelos agregadores priorizados, ou instituições estratégicas para contraste metodológico.": (
            "Instituciones individuales no cubiertas por los agregadores priorizados, o instituciones estratégicas "
            "para contraste metodológico."
        ),
        "arquivos-corpus": "archivos-corpus",
        "Entram prioritariamente quando não estiverem cobertos pelos agregadores já mapeados e quando ajudarem a aprofundar a observação do audiovisual.": (
            "Entran prioritariamente cuando no estén cubiertos por los agregadores ya mapeados y cuando ayuden a "
            "profundizar la observación del audiovisual."
        ),
        "Sim": "Sí",
        "Não": "No",
        "Abrir vídeo": "Abrir video",
        "Exportar": "Exportar",
        "Ainda não há": "Todavía no hay",
        "Nenhum": "Ningún",
        "Nenhuma": "Ninguna",
    },
    "en": {
        "Visão geral": "Overview",
        "Agregadores": "Aggregators",
        "Arquivos": "Archives",
        "Agregadores arquivísticos": "Archival Aggregators",
        "Arquivos e instituições arquivísticas": "Archives and Archival Institutions",
        "Fundamentação": "Rationale",
        "Síntese": "Summary",
        "Instituições com vídeo": "Institutions with Video",
        "Vídeos e temas": "Videos and Themes",
        "Vídeos": "Videos",
        "Territórios": "Territories",
        "Tabelas": "Tables",
        "Instituições": "Institutions",
        "Ficha institucional": "Institution Record",
        "Histórico geral": "General History",
        "Sinais de possível extinção": "Signals of Possible Extinction",
        "Síntese da fila": "Queue Summary",
        "Fontes candidatas": "Candidate Sources",
        "Regimes de acesso": "Access Regimes",
        "Modalidades de acesso": "Access Modalities",
        "Critérios de fechamento": "Closure Criteria",
        "Matriz europeia": "European Matrix",
        "Fora da base ativa": "Outside the Active Base",
        "Acesso pago/restrito": "Paid/Restricted Access",
        "Lacunas documentadas": "Documented Gaps",
        "Próximas unidades": "Next Units",
        "Mapa europeu": "European Map",
        "Síntese do mapeamento": "Mapping Summary",
        "Linha do tempo das rodadas": "Round Timeline",
        "Resultados por unidade": "Results by Unit",
        "Arquivos de referência": "Reference Files",
        "Síntese institucional": "Institutional Summary",
        "Temas e relações": "Themes and Relations",
        "Casos documentados": "Documented Cases",
        "Ficha e acesso": "Record and Access",
        "Vídeos detectados": "Detected Videos",
        "Páginas analisadas": "Analyzed Pages",
        "Categoria": "Category",
        "Unidade": "Unit",
        "Caso documentado": "Documented Case",
        "Instituição": "Institution",
        "Informação": "Information",
        "Domínio": "Domain",
        "Observação": "Observation",
        "Código": "Code",
        "Repositório": "Repository",
        "Conteúdo": "Content",
        "Ficha": "Record",
        "Fonte": "Source",
        "Data": "Date",
        "Título": "Title",
        "Assunto": "Subject",
        "Descrição": "Description",
        "Link": "Link",
        "Método": "Method",
        "Tipo": "Type",
        "Valor": "Value",
        "Conclusão": "Conclusion",
        "Referência": "Reference",
        "Evidência": "Evidence",
        "Nível": "Level",
        "Escala": "Scale",
        "Completude": "Completeness",
        "Limite": "Limit",
        "Justificativa": "Justification",
        "Prioridade": "Priority",
        "Decisão": "Decision",
        "Gatilho": "Trigger",
        "Encaminhamento": "Routing",
        "Risco": "Risk",
        "Modelo": "Model",
        "Termos": "Terms",
        "Resultado": "Result",
        "Resultados": "Results",
        "Ingestão": "Ingestion",
        "Avaliado": "Evaluated",
        "Melhor URL": "Best URL",
        "Publicado": "Published",
        "Possível": "Possible",
        "Disponível": "Available",
        "Restrito": "Restricted",
        "Restrita": "Restricted",
        "Ativo": "Active",
        "Ativa": "Active",
        "Técnico": "Technical",
        "Técnica": "Technical",
        "Metodológico": "Methodological",
        "Metodológica": "Methodological",
        "Íntegro": "Intact",
        "Acessível": "Accessible",
        "Instável": "Unstable",
        "Sem site": "No site",
        "Erro HTTP": "HTTP error",
        "Indisponíveis": "Unavailable",
        "Disponíveis com vídeos": "Available with videos",
        "Disponíveis sem vídeos": "Available without videos",
        "Identificada, mas não incluída na base ativa do observatório": (
            "Identified, but not included in the observatory's active base"
        ),
        "não incorporar à base ativa no MVP": "do not incorporate into the active base in the MVP",
        "Ausência de rota de coleta estável no protocolo atual.": (
            "Absence of a stable collection route in the current protocol."
        ),
        "categoria de acesso": "access category",
        "status público": "public status",
        "decisão metodológica": "methodological decision",
        "motivo da não inclusão": "reason for non-inclusion",
        "rota de coleta tentada": "collection route attempted",
        "tentativas registradas": "recorded attempts",
        "explicação metodológica": "methodological explanation",
        "próximo passo": "next step",
        "tipo de rota": "route type",
        "URL da rota": "route URL",
        "status de acesso": "access status",
        "uso audiovisual possível": "possible audiovisual use",
        "nota metodológica": "methodological note",
        "tipo de conteúdo": "content type",
        "sinal observado": "observed signal",
        "valor observado": "observed value",
        "conteúdo publicado na fonte": "content published in the source",
        "ficha da instituição na fonte": "institution record in the source",
        "site informado na fonte": "site listed in the source",
        "site externo informado": "external site listed",
        "URL final": "final URL",
        "código do repositório": "repository code",
        "título do vídeo": "video title",
        "data do vídeo": "video date",
        "assunto do vídeo": "video subject",
        "descrição do vídeo": "video description",
        "link do vídeo": "video link",
        "status_técnico": "technical_status",
        "Atualizado no último ciclo": "Updated in the latest cycle",
        "Pendente no ciclo parcial mais recente": "Pending in the most recent partial cycle",
        "Atualização atrasada": "Delayed update",
        "Falha no último ciclo": "Failure in the latest cycle",
        "escala de cobertura": "coverage scale",
        "completude da coleta": "collection completeness",
        "limite técnico": "technical limit",
        "nota de completude": "completeness note",
        "última observação registrada": "latest recorded observation",
        "status da fonte": "source status",
        "chave de observação": "observation key",
        "dias desde a última observação": "days since latest observation",
        "estado de atualização": "update state",
        "justificativa metodológica": "methodological justification",
        "registros públicos": "public records",
        "registros restritos": "restricted records",
        "registros avaliados no observatório": "records evaluated in the observatory",
        "% público": "% public",
        "% restrito": "% restricted",
        "nota do denominador": "denominator note",
        "status no organismo": "status in the organism",
        "categoria de restrição": "restriction category",
        "status do volume": "volume status",
        "arquivo-fonte": "source file",
        "tipo de sinal": "signal type",
        "etapa de expansão": "expansion stage",
        "atualização analítica": "analytical update",
        "critério de entrada": "entry criterion",
        "regra de expansão": "expansion rule",
        "modelo de acesso observado": "observed access model",
        "status metodológico": "methodological status",
        "termos sondados": "terms probed",
        "termos com resultado": "terms with results",
        "termos bloqueados": "blocked terms",
        "recomendação de ingestão": "ingestion recommendation",
        "avaliado em": "evaluated on",
        "melhor URL de sondagem": "best probing URL",
        "modelo observado": "observed model",
        "exige nova rota": "requires new route",
        "estado da avaliação": "evaluation state",
        "evidência observada": "observed evidence",
        "risco metodológico": "methodological risk",
        "encaminhamento recomendado": "recommended routing",
        "decisão de incorporação": "incorporation decision",
        "gatilho de revisão": "review trigger",
        "referência oficial": "official reference",
        "nota da referência": "reference note",
        "viabilidade da rota": "route viability",
        "Arquivo identificado, mas não incluído na base ativa do observatório.": (
            "Archive identified, but not included in the observatory's active base."
        ),
        "fora da base ativa": "outside the active base",
        "Situação": "Status",
        "Escopo": "Scope",
        "Categoria de acesso": "Access Category",
        "Bloqueia expansão?": "Blocks expansion?",
        "Regra": "Rule",
        "Decisão e negativa metodológica": "Decision and Methodological Negative",
        "Rotas candidatas avaliadas": "Candidate Routes Evaluated",
        "Tentativas de verificação": "Verification Attempts",
        "Rodadas registradas": "Registered Rounds",
        "Último escopo": "Latest Scope",
        "Unidades avaliadas na última rodada": "Units evaluated in the latest round",
        "Pendências na última rodada": "Pending items in the latest round",
        "Acompanhamento das atualizações": "Update Monitoring",
        "Atualizadas na última rodada": "Updated in the latest round",
        "Pendentes na rodada parcial": "Pending in the partial round",
        "Atualizações atrasadas": "Delayed Updates",
        "Rodada": "Round",
        "mais recente:": "most recent:",
        "sucessos,": "successes,",
        "pendências, gerado em": "pending items, generated on",
        "Ver distribuição dos estados de atualização": "View Distribution of Update States",
        "Observações históricas das unidades": "Historical Unit Observations",
        "Observações históricas institucionais": "Institutional Historical Observations",
        "Sinais globais de possível extinção": "Global Signals of Possible Extinction",
        "Unidades com histórico registrado": "Units with Registered History",
        "Exportar histórico geral das unidades": "Export General Unit History",
        "Exporta a linha do tempo combinada das unidades do observatório.": (
            "Exports the combined timeline of the observatory units."
        ),
        "Este quadro acompanha a saúde temporal do observatório por unidade documental, distinguindo atualizações recentes, pendências de rodadas parciais e atrasos de acompanhamento.": (
            "This panel tracks the temporal health of the observatory by documentary unit, distinguishing recent "
            "updates, pending items from partial rounds and monitoring delays."
        ),
        "Índice de dados públicos": "Public Data Index",
        "O índice compara registros audiovisuais disponíveis em superfície pública com registros cujo acesso ao audiovisual exige pagamento, autenticação, cadastro ou licenciamento. Bancos privados/publicitários de imagens não entram no índice; permanecem documentados apenas na auditoria metodológica de acesso pago/restrito.": (
            "The index compares audiovisual records available on public surfaces with records whose audiovisual "
            "access requires payment, authentication, registration or licensing. Private/advertising image banks are "
            "not included in the index; they remain documented only in the methodological audit of paid/restricted "
            "access."
        ),
        "Índice público World": "World Public Index",
        "Índice público Europa": "Europe Public Index",
        "Registros restritos quantificados": "Quantified Restricted Records",
        "Unidades restritas no índice": "Restricted Units in the Index",
        "Mundo e continentes": "World and Continents",
        "Por unidade documental": "By Documentary Unit",
        "Acesso restrito": "Restricted Access",
        "Linha do tempo e retração pública do audiovisual": "Timeline and Public Retraction of Audiovisual Access",
        "Esta camada reúne a memória histórica das unidades documentais e prepara o observatório para detectar ausências, indisponibilidades recorrentes e perda de evidência pública detectável de audiovisual.": (
            "This layer brings together the historical memory of documentary units and prepares the observatory to "
            "detect absences, recurring unavailability and loss of detectable public audiovisual evidence."
        ),
        "Cada linha preserva uma observação histórica de uma unidade documental, mantendo explícita sua categoria analítica e escala de cobertura.": (
            "Each row preserves a historical observation of a documentary unit, keeping its analytical category and "
            "coverage scale explicit."
        ),
        "Os sinais abaixo não afirmam extinção por si só. Eles indicam mudanças que merecem observação longitudinal e interpretação metodológica cuidadosa.": (
            "The signals below do not claim extinction by themselves. They indicate changes that deserve "
            "longitudinal observation and careful methodological interpretation."
        ),
        "Unidades documentais ativas": "Active Documentary Units",
        "Instituições no observatório": "Institutions in the Observatory",
        "Links de vídeo detectados": "Detected Video Links",
        "Vídeos no recorte curatorial": "Videos in the Curatorial Scope",
        "Categorias analíticas do observatório": "Analytical Categories of the Observatory",
        "As categorias abaixo delimitam níveis diferentes de observação. Elas são comparáveis, mas não são tratadas como equivalentes do ponto de vista metodológico.": (
            "The categories below define different levels of observation. They are comparable, but they are not "
            "treated as methodologically equivalent."
        ),
        "Estratégia de expansão": "Expansion Strategy",
        "O organismo cresce primeiro por agregadores continentais e, depois, incorpora arquivos e instituições não cobertos por esses agregadores.": (
            "The organism grows first through continental aggregators and then incorporates archives and institutions "
            "not covered by those aggregators."
        ),
        "Fila de expansão do observatório": "Observatory Expansion Queue",
        "A fila abaixo é gerada por regra pública e reprodutível. Neste momento, ela prioriza o fechamento da Europa antes da abertura sistemática de novos continentes.": (
            "The queue below is generated by a public and reproducible rule. At this stage, it prioritizes the "
            "closure of Europe before the systematic opening of new continents."
        ),
        "Cada linha mostra uma unidade potencial, a decisão automática aplicada e o próximo passo sugerido pelo protocolo do organismo.": (
            "Each row shows a potential unit, the automatic decision applied and the next step suggested by the "
            "organism's protocol."
        ),
        "Avaliação metodológica dos agregadores europeus": "Methodological Evaluation of European Aggregators",
        "Esta camada não incorpora novas unidades automaticamente. Ela observa a superfície pública de Archives Hub, FranceArchives, PARES e Portal Português de Arquivos para decidir, com evidência registrada, qual fonte pode seguir para validação total e qual exige nova rota de acesso.": (
            "This layer does not incorporate new units automatically. It observes the public surface of Archives Hub, "
            "FranceArchives, PARES and the Portuguese Archives Portal in order to decide, with recorded evidence, "
            "which source can move to full validation and which one requires a new access route."
        ),
        "Os registros preliminares de busca somam os resultados brutos retornados nas verificações dos agregadores. Eles não equivalem a vídeos incorporados ao corpus: indicam apenas volume potencial a validar, deduplicar e classificar.": (
            "The preliminary search records add up the raw results returned by aggregator checks. They do not equal "
            "videos incorporated into the corpus: they indicate only potential volume to validate, deduplicate and "
            "classify."
        ),
        "Esta matriz separa decisão metodológica de disponibilidade técnica: uma fonte pode ser relevante para o fechamento europeu e, ainda assim, permanecer fora das unidades ativas até existir uma rota estável de acesso.": (
            "This matrix separates methodological decision from technical availability: a source may be relevant to "
            "the European closure and still remain outside the active units until a stable access route exists."
        ),
        "Estas rotas não promovem automaticamente uma fonte a unidade ativa. Elas registram caminhos oficiais ou documentados que podem ser testados antes da incorporação.": (
            "These routes do not automatically promote a source to active-unit status. They record official or "
            "documented paths that can be tested before incorporation."
        ),
        "Este quadro testa SRU e OAI-PMH em modo mínimo, sem promover o Archives Hub a unidade ativa enquanto a rota de acesso não estiver estável.": (
            "This panel tests SRU and OAI-PMH in minimal mode, without promoting Archives Hub to active-unit status "
            "while the access route remains unstable."
        ),
        "Este quadro testa sinais mínimos de viabilidade técnica para FranceArchives sem transferir integralmente o pacote XML e sem transformar a fonte em unidade ativa.": (
            "This panel tests minimal signs of technical viability for FranceArchives without fully transferring the "
            "XML package and without turning the source into an active unit."
        ),
        "Fechamento da etapa Europa": "Closure of the Europe Stage",
        "Este quadro explicita o estado metodológico da etapa Europa. Ele não afirma que todos os arquivos audiovisuais europeus foram identificados; registra o que já opera como unidade ativa, o que está protocolado e o que segue em fila auditável de expansão.": (
            "This panel makes the methodological status of the Europe stage explicit. It does not claim that all "
            "European audiovisual archives have been identified; it records what already operates as an active unit, "
            "what has been protocolled and what remains in an auditable expansion queue."
        ),
        "Essas unidades foram identificadas e preservadas no observatório, mas não entram na base ativa enquanto a rota de coleta não for estável e reprodutível.": (
            "These units were identified and preserved in the observatory, but they do not enter the active base "
            "until the collection route is stable and reproducible."
        ),
        "Esta auditoria separa bancos privados pagos, catálogos comerciais de licenciamento e streaming pago/autenticado. Nem todo acesso comercial fica fora da base ativa: quando há registros públicos avaliados no observatório, ele permanece como modalidade analítica própria.": (
            "This audit separates paid private banks, commercial licensing catalogues and paid/authenticated "
            "streaming. Not every commercial access case remains outside the active base: when public records are "
            "evaluated in the observatory, it remains as its own analytical modality."
        ),
        "Esta auditoria impede que o fechamento europeu seja lido como exaustividade absoluta. Ela documenta unidades cobertas por bases ativas, fontes legadas, radares e candidatos futuros, mantendo o MVP continental aberto à expansão controlada.": (
            "This audit prevents the European closure from being read as absolute exhaustiveness. It documents units "
            "covered by active bases, legacy sources, radars and future candidates, keeping the continental MVP open "
            "to controlled expansion."
        ),
        "Mapeamento europeu ampliado": "Expanded European Mapping",
        "Este módulo separa o registro europeu completo da fila operacional de pendências. Ele identifica agregadores, redes, diretórios e arquivos audiovisuais europeus sem chute: agregadores primeiro, diretórios especializados depois, arquivos individuais por expansão controlada. A varredura de fontes oficiais inclui Europeana, FIAF, EFG, EUscreen, FIAT/IFTA, INEDITS, ACE e EBU. A presença no registro não significa incorporação automática; a presença na fila significa análise pendente.": (
            "This module separates the full European registry from the operational pending queue. It identifies "
            "European aggregators, networks, directories and audiovisual archives without guesswork: aggregators "
            "first, then specialized directories, then individual archives through controlled expansion. The sweep of "
            "official sources includes Europeana, FIAF, EFG, EUscreen, FIAT/IFTA, INEDITS, ACE and EBU. Presence in "
            "the registry does not mean automatic incorporation; presence in the queue means pending analysis."
        ),
        "Unidades europeias ativas": "Active European Units",
        "Candidatos em avaliação": "Candidates under Evaluation",
        "Identificados fora da base ativa": "Identified outside the active base",
        "Lacunas auditadas": "Audited Gaps",
        "Unidades europeias mapeadas": "Mapped European Units",
        "Agregador audiovisual europeu": "European Audiovisual Aggregator",
        "Agregadores nacionais europeus": "European National Aggregators",
        "Lacunas europeias": "European Gaps",
        "Unidades já incorporadas": "Already Incorporated Units",
        "Agregadores avaliados": "Evaluated Aggregators",
        "Prontos para validação total": "Ready for Full Validation",
        "Exigem nova rota de acesso": "Require a New Access Route",
        "Registros preliminares de busca": "Preliminary Search Records",
        "Rotas oficiais analisadas": "Official Routes Analyzed",
        "Verificação metodológica do Archives Hub": "Methodological Verification of Archives Hub",
        "Verificação metodológica do FranceArchives": "Methodological Verification of FranceArchives",
        "Ver verificações realizadas": "View Completed Verifications",
        "Próxima etapa": "Next Stage",
        "Ver posição dessas unidades na fila europeia": "View These Units in the European Queue",
        "Próximas análises individuais": "Next Individual Analyses",
        "Diretórios a expandir": "Directories to Expand",
        "Ver tabela detalhada de regimes": "View Detailed Regime Table",
        "Ver tabela detalhada de modalidades": "View Detailed Modality Table",
        "Comparações entre unidades documentais": "Comparisons Across Documentary Units",
        "Estes quadros mostram como as unidades diferem não apenas em volume, mas também na forma como o audiovisual se torna publicamente acessível.": (
            "These panels show how units differ not only in volume, but also in the way audiovisual material becomes "
            "publicly accessible."
        ),
        "Linhas representam unidades documentais; colunas representam regimes institucionais de acesso audiovisual detectável.": (
            "Rows represent documentary units; columns represent detectable institutional regimes of audiovisual "
            "access."
        ),
        "Linhas representam unidades documentais; colunas representam modalidades públicas de acesso encontradas nos catálogos.": (
            "Rows represent documentary units; columns represent public access modalities found in the catalogues."
        ),
        "Histórico do observatório": "Observatory History",
        "Cada linha representa uma rodada do observatório, permitindo acompanhar cadência, escopo e estabilidade das atualizações ao longo do tempo.": (
            "Each row represents one observatory round, making it possible to follow cadence, scope and update "
            "stability over time."
        ),
        "Este quadro preserva o desempenho de cada unidade documental em cada rodada do observatório.": (
            "This panel preserves the performance of each documentary unit in each observatory round."
        ),
        "Estes arquivos preservam a rastreabilidade global do observatório, permitindo auditar rodadas, unidades ativas e resultados históricos.": (
            "These files preserve the observatory's global traceability, allowing rounds, active units and historical "
            "results to be audited."
        ),
        "Unidades na categoria": "Units in the Category",
        "Instituições no recorte": "Institutions in the Scope",
        "Instituições com links de vídeo": "Institutions with Video Links",
        "Unidades desta categoria": "Units in this Category",
        "Princípio de separação": "Separation Principle",
        "Instituições da categoria": "Institutions in the Category",
        "Vídeos da categoria": "Videos in the Category",
        "Todas as unidades": "All units",
        "Todas as situações": "All statuses",
        "Todos os temas": "All themes",
        "Todas as modalidades": "All modalities",
        "Unidade documental": "Documentary Unit",
        "Situação metodológica": "Methodological Status",
        "Buscar instituição, país ou domínio": "Search institution, country or domain",
        "Tema": "Theme",
        "Plataformas": "Platforms",
        "Continentes": "Continents",
        "Continente": "Continent",
        "País": "Country",
        "Links de vídeo": "Video links",
        "Sinais embutidos": "Embedded signals",
        "Modalidade de acesso": "Access Modality",
        "Regime de acesso audiovisual": "Audiovisual Access Regime",
        "Tipo de arquivo": "Archive Type",
        "Integridade": "Integrity",
        "Segmento institucional": "Institutional Segment",
        "Somente com links de vídeo": "Only with video links",
        "Busca textual": "Text search",
        "Instituição, país, domínio ou código": "Institution, country, domain or code",
        "Seleção do recorte": "Scope Selection",
        "Recorte da lista": "List Scope",
        "Selecione uma instituição": "Select an institution",
        "Tema dos vídeos": "Video Theme",
        "Instituições com site informado": "Institutions with listed website",
        "Sites íntegros": "Intact Sites",
        "Evidência pública detectável": "Detectable Public Evidence",
        "Evidência indireta": "Indirect Evidence",
        "Potencial em navegação interna": "Potential in Internal Navigation",
        "Sem evidência pública detectável": "No detectable public evidence",
        "Site indisponível para verificação": "Site unavailable for verification",
        "Condição dos sites institucionais": "Institutional Site Condition",
        "Disponibilidade institucional": "Institutional Availability",
        "Categorias": "Categories",
        "Subcategorias": "Subcategories",
        "Visibilidade do audiovisual": "Audiovisual Visibility",
        "Regimes de acesso audiovisual detectáveis": "Detectable Audiovisual Access Regimes",
        "Modalidades de acesso detectadas": "Detected Access Modalities",
        "Tipo institucional declarado na fonte": "Institutional Type Declared in the Source",
        "Temas dos vídeos": "Video Themes",
        "Locais de acesso detectados": "Detected Access Locations",
        "Temas por plataforma": "Themes by Platform",
        "Temas por país": "Themes by Country",
        "Temas por tipo de arquivo": "Themes by Archive Type",
        "Visibilidade por tipo de arquivo": "Visibility by Archive Type",
        "Casos indisponíveis": "Unavailable Cases",
        "Casos com site quebrado": "Cases with Broken Site",
        "Casos instáveis": "Unstable Cases",
        "Distribuição geográfica das instituições com evidência pública detectável de audiovisual": (
            "Geographic Distribution of Institutions with Detectable Public Audiovisual Evidence"
        ),
        "Sobre o recorte APE": "About the APE Scope",
        "Sobre o recorte": "About the Scope",
        "Ver referência de classificação": "View Classification Reference",
        "Ver arquivos de referência desta unidade": "View Reference Files for This Unit",
        "Temas identificados": "Identified Themes",
        "Locais de acesso": "Access Locations",
        "#### Distribuição temática": "#### Thematic Distribution",
        "Organização dos vídeos": "Video Organization",
        "Ver sínteses do catálogo de vídeos": "View Video Catalogue Summaries",
        "Distribuição por continente": "Distribution by Continent",
        "Distribuição por país": "Distribution by Country",
        "Filtrar continentes": "Filter continents",
        "#### Consulta das tabelas": "#### Table Query",
        "Selecione a tabela": "Select the table",
        "Com site informado na fonte": "With site listed in the source",
        "Com evidência pública detectável": "With detectable public evidence",
        "Indisponíveis no recorte": "Unavailable in the scope",
        "Ver tabela completa do recorte": "View Complete Scope Table",
        "Resposta do site": "Site response",
        "Páginas internas": "Internal pages",
        "Leitura metodológica": "Methodological Reading",
        "Fontes e endereços": "Sources and Addresses",
        "Abrir": "Open",
        "Temas sugeridos": "Suggested Themes",
        "Páginas verificadas": "Verified Pages",
        "Links encontrados nessas páginas": "Links found on these pages",
        "Sinais embutidos nessas páginas": "Embedded signals on these pages",
        "Esta aba existe justamente para não apagar a tentativa. A unidade aparece no observatório, mas fica separada das unidades ativas até que a rota de coleta seja estável, reprodutível e comparável.": (
            "This tab exists precisely so the attempt is not erased. The unit appears in the observatory, but remains "
            "separate from active units until the collection route is stable, reproducible and comparable."
        ),
        "Leitura correta: a não inclusão não prova inexistência de audiovisual. Ela prova apenas que, nesta rodada, o observatório não encontrou uma rota suficientemente estável para coleta com rigor.": (
            "Correct reading: non-inclusion does not prove the absence of audiovisual material. It only proves that, "
            "in this round, the observatory did not find a sufficiently stable route for rigorous collection."
        ),
        "O painel organiza a leitura do observatório em três camadas: síntese institucional, análise temática e detalhamento dos casos que exigem atenção metodológica.": (
            "The panel organizes the observatory reading into three layers: institutional synthesis, thematic "
            "analysis and detailed cases requiring methodological attention."
        ),
        "Esta distribuição exclui, por padrão, ruído de plataforma ou incorporação externa.": (
            "This distribution excludes platform noise or external embeds by default."
        ),
        "Dentro de 'quebrado', o observatório distingue erro explícito e página suspeita.": (
            "Within 'broken', the observatory distinguishes explicit errors from suspicious pages."
        ),
        "Esta aba reúne as instituições em cujos sites a coleta encontrou ao menos um link explícito de vídeo.": (
            "This tab brings together institutions whose sites contained at least one explicit video link in the "
            "collection process."
        ),
        "Este catálogo organiza o recorte curatorial de vídeos a partir de metadados básicos e de uma classificação temática baseada em título, assunto e descrição, excluindo por padrão o ruído de plataforma ou incorporação externa.": (
            "This catalogue organizes the curatorial video scope using basic metadata and thematic classification "
            "based on title, subject and description, excluding platform noise or external embeds by default."
        ),
        "Este quadro considera as instituições nas quais a coleta encontrou ao menos um link explícito de vídeo.": (
            "This panel considers institutions in which the collection found at least one explicit video link."
        ),
        "Esta aba reúne as principais tabelas derivadas do recorte e permite exportá-las para pesquisa, redação, revisão metodológica e documentação.": (
            "This tab brings together the main tables derived from the scope and allows them to be exported for "
            "research, writing, methodological review and documentation."
        ),
        "Cada linha representa uma unidade institucional do recorte, complementada pela verificação do site externo informado na fonte.": (
            "Each row represents one institutional unit in the scope, complemented by verification of the external "
            "site listed in the source."
        ),
        "Este quadro reúne apenas instituições pertencentes a corpora da mesma categoria analítica, evitando mistura entre agregadores e instituições custodiais.": (
            "This panel includes only institutions belonging to corpora in the same analytical category, avoiding "
            "mixing aggregators with custodial institutions."
        ),
        "### Linha do tempo e retração pública do audiovisual": "### Timeline and Public Retraction of Audiovisual Access",
        "### Categorias analíticas do observatório": "### Analytical Categories of the Observatory",
        "### Fila de expansão do observatório": "### Observatory Expansion Queue",
        "### Avaliação metodológica dos agregadores europeus": "### Methodological Evaluation of European Aggregators",
        "### Comparações entre unidades documentais": "### Comparisons Across Documentary Units",
        "#### Tabelas disponíveis para exportação": "#### Tables Available for Export",
        "#### Matriz de decisão de incorporação": "#### Incorporation Decision Matrix",
        "A avaliação dos agregadores europeus ainda não está disponível nesta versão do observatório.": (
            "The evaluation of European aggregators is not yet available in this version of the observatory."
        ),
        "O relatório de fechamento europeu ainda não está disponível nesta versão do observatório.": (
            "The European closure report is not yet available in this version of the observatory."
        ),
        "O mapeamento europeu ampliado ainda não está disponível.": (
            "The expanded European mapping is not yet available."
        ),
        "Instituições com links de vídeo por unidade": "Institutions with video links by unit",
        "Links de vídeo detectados por unidade": "Detected video links by unit",
        "Vídeos no recorte curatorial por unidade": "Videos in the curatorial scope by unit",
        "Este observatório investiga a visibilidade pública do audiovisual em ambientes arquivísticos na web. Nesta etapa, a unidade analisada é o **Archives Portal Europe (APE)**, tratado como um portal arquivístico geral, e não como um repositório especializado em audiovisual. **Objetivo** Examinar como o audiovisual se torna publicamente visível, detectável e acessível nos sites institucionais vinculados ao APE, considerando tanto a presença explícita quanto formas mais indiretas de evidência. **Princípio metodológico** A ausência de vídeo detectado não autoriza afirmar, por si só, ausência de acervo audiovisual. No contexto de um portal geral, a não detecção pode indicar pelo menos quatro situações: - o acervo audiovisual pode não existir; - o acervo pode existir, mas não estar digitalizado; - o acervo pode estar digitalizado, mas não público; - o acervo pode estar público, porém pouco visível ou não detectável com a estratégia atual de coleta. Neste observatório, fontes gerais como o APE podem permanecer mapeadas mesmo quando parte de suas instituições retorna zero audiovisual, porque esse zero também é analiticamente informativo para o estudo da visibilidade pública do acervo.": (
            "This observatory investigates the public visibility of audiovisual material in archival environments on "
            "the web. At this stage, the unit under analysis is the **Archives Portal Europe (APE)**, treated as a "
            "general archival portal rather than a specialized audiovisual repository. **Objective** To examine how "
            "audiovisual material becomes publicly visible, detectable and accessible on institutional sites linked "
            "to APE, considering both explicit presence and more indirect forms of evidence. **Methodological "
            "principle** The absence of detected video does not, by itself, authorize the claim that no audiovisual "
            "collection exists. In the context of a general portal, non-detection may indicate at least four "
            "situations: - the audiovisual collection may not exist; - the collection may exist but not be digitized; "
            "- the collection may be digitized but not public; - the collection may be public but poorly visible or "
            "not detectable with the current collection strategy. In this observatory, general sources such as APE "
            "may remain mapped even when part of their institutions return zero audiovisual material, because that "
            "zero is also analytically informative for the study of the public visibility of collections."
        ),
        "**Eixo interpretativo** A plataforma observa a circulação audiovisual como um fenômeno territorial, cultural e técnico. O problema não é apenas localizar vídeos, mas compreender quem hospeda, quem indexa, quem descreve, em qual idioma, sob qual regime de acesso, por qual plataforma e em que escala territorial esse audiovisual se torna público. **O que a plataforma afirma com maior segurança** - quando há evidência pública detectável de audiovisual; - quando há apenas evidência pública indireta; - quando não foi encontrada evidência pública detectável de audiovisual; - quando o site não pôde ser verificado. **O que a plataforma evita afirmar** - que a ausência de evidência pública detectável equivale à inexistência de acervo audiovisual; - que a visibilidade pública esgota a complexidade do acervo; - que uma única coleta resolve o problema da descrição e do acesso audiovisual.": (
            "**Interpretive Axis** The platform observes audiovisual circulation as a territorial, cultural and "
            "technical phenomenon. The problem is not only to locate videos, but to understand who hosts, who "
            "indexes, who describes, in which language, under which access regime, through which platform and at "
            "what territorial scale that audiovisual material becomes public. **What the platform can state with "
            "greater confidence** - when there is detectable public audiovisual evidence; - when there is only "
            "indirect public evidence; - when no detectable public audiovisual evidence was found; - when the site "
            "could not be verified. **What the platform avoids claiming** - that the absence of detectable public "
            "evidence equals the inexistence of an audiovisual collection; - that public visibility exhausts the "
            "complexity of the collection; - that a single collection round resolves the problem of audiovisual "
            "description and access."
        ),
        "Nenhuma instituição corresponde aos filtros selecionados.": (
            "No institution matches the selected filters."
        ),
        "Situação metodológica do audiovisual": "Methodological status of the audiovisual material",
        "O site externo respondeu. Esta instituição pode seguir para curadoria pública.": (
            "The external site responded. This institution can proceed to public curation."
        ),
        "Ainda não há histórico geral disponível para o observatório.": (
            "No general history is available for the observatory yet."
        ),
        "Ainda não há sinais globais registrados. Isso é esperado enquanto o organismo acumula mais rodadas históricas para comparação.": (
            "No global signals have been recorded yet. This is expected while the organism accumulates more "
            "historical rounds for comparison."
        ),
        "Ainda não há dados suficientes para comparar regimes de acesso entre unidades.": (
            "There is not enough data yet to compare access regimes across units."
        ),
        "Ainda não há dados suficientes para comparar modalidades de acesso entre unidades.": (
            "There is not enough data yet to compare access modalities across units."
        ),
        "Ainda não há unidades disponíveis nesta categoria.": "There are no units available in this category yet.",
        "Ainda não há instituições disponíveis nesta categoria.": (
            "There are no institutions available in this category yet."
        ),
        "Ainda não há vídeos curatoriais disponíveis nesta categoria.": (
            "There are no curatorial videos available in this category yet."
        ),
        "Neste caso, a unidade continua relevante como fonte geral de pesquisa. O retorno zero indica que, até aqui, não houve evidência pública detectável de audiovisual nas instituições mapeadas por esta coleta.": (
            "In this case, the unit remains relevant as a general research source. The zero return indicates that, "
            "so far, there was no detectable public audiovisual evidence in the institutions mapped by this "
            "collection."
        ),
        "Como esta é uma fonte geral de pesquisa, o retorno zero não invalida a unidade. Ele indica apenas ausência de evidência pública detectável de audiovisual nesta rodada.": (
            "Because this is a general research source, the zero return does not invalidate the unit. It indicates "
            "only the absence of detectable public audiovisual evidence in this round."
        ),
        "Nenhum vídeo corresponde ao tema e aos filtros selecionados.": (
            "No video matches the selected theme and filters."
        ),
        "Ainda não há distribuição geográfica com links de vídeo detectados.": (
            "There is no geographic distribution with detected video links yet."
        ),
        "O site respondeu, mas a página final parece genérica, suspensa ou não confiável. Aqui ele entra dentro da categoria quebrado.": (
            "The site responded, but the final page appears generic, suspended or unreliable. Here it falls under "
            "the broken category."
        ),
        "Nenhum link de vídeo foi localizado automaticamente para esta instituição.": (
            "No video link was automatically located for this institution."
        ),
        "Nenhuma página complementar foi analisada para esta instituição.": (
            "No complementary page was analyzed for this institution."
        ),
        "Nenhuma instituição se enquadra neste recorte; a lista completa foi restaurada.": (
            "No institution fits this scope; the complete list has been restored."
        ),
        "Ainda não há índice por unidade documental disponível.": (
            "There is no index by documentary unit available yet."
        ),
        "Ainda não há unidades restritas registradas no índice.": (
            "There are no restricted units registered in the index yet."
        ),
        "Esta tabela mostra apenas unidades restritas que fazem parte do índice. Bancos privados/publicitários ficam fora deste recorte.": (
            "This table shows only restricted units that are part of the index. Private/advertising banks remain "
            "outside this scope."
        ),
        "A matriz de fechamento europeu ainda não está disponível.": (
            "The European closure matrix is not yet available."
        ),
        "Ainda não há unidades europeias documentadas fora da base ativa.": (
            "There are no European units documented outside the active base yet."
        ),
        "A auditoria de acesso pago/restrito ainda não está disponível.": (
            "The paid/restricted access audit is not yet available."
        ),
        "A auditoria de lacunas europeias ainda não está disponível.": (
            "The European gaps audit is not yet available."
        ),
        "Ainda não há resultados históricos disponíveis por unidade.": (
            "There are no historical results available by unit yet."
        ),
        "Ainda não há dados suficientes para analisar a visibilidade do audiovisual.": (
            "There is not enough data yet to analyze audiovisual visibility."
        ),
        "Ainda não há dados suficientes para resumir os regimes de acesso audiovisual.": (
            "There is not enough data yet to summarize audiovisual access regimes."
        ),
        "Ainda não há dados suficientes para resumir as modalidades de acesso.": (
            "There is not enough data yet to summarize access modalities."
        ),
        "Ainda não há dados suficientes para resumir o tipo institucional declarado na fonte.": (
            "There is not enough data yet to summarize the institutional type declared in the source."
        ),
        "Ainda não há temas classificados para os vídeos.": "There are no classified video themes yet.",
        "Nenhum link de vídeo foi detectado ainda.": "No video link has been detected yet.",
        "Ainda não há dados suficientes para cruzar temas e plataformas.": (
            "There is not enough data yet to cross themes and platforms."
        ),
        "Nenhum caso enquadrado como quebrado foi detectado nesta rodada.": (
            "No case classified as broken was detected in this round."
        ),
        "Nenhum caso instável foi detectado nesta rodada.": "No unstable case was detected in this round.",
        "Ainda não há modalidades de acesso classificadas.": (
            "There are no classified access modalities yet."
        ),
        "O site respondeu com restrição de acesso. Para o projeto, ele entra como não disponível.": (
            "The site responded with access restrictions. For the project, it is classified as unavailable."
        ),
        "Nenhum vídeo permaneceu no recorte curatorial após a filtragem de ruído fora de escopo.": (
            "No video remained in the curatorial scope after filtering out-of-scope noise."
        ),
        "Ainda não há dados suficientes para cruzar temas e países.": (
            "There is not enough data yet to cross themes and countries."
        ),
        "Ainda não há dados suficientes para cruzar temas e tipos institucionais.": (
            "There is not enough data yet to cross themes and institutional types."
        ),
        "Ainda não há dados suficientes para cruzar visibilidade e tipos institucionais.": (
            "There is not enough data yet to cross visibility and institutional types."
        ),
        "A fonte não informa um site externo para esta instituição.": (
            "The source does not provide an external site for this institution."
        ),
        "O site institucional não respondeu de forma confiável. Para o projeto, esta instituição entra como não disponível.": (
            "The institutional site did not respond reliably. For the project, this institution is classified as "
            "unavailable."
        ),
        "Ainda não há linha do tempo disponível para este recorte.": (
            "There is no timeline available for this scope yet."
        ),
        "Ainda não há sinais registrados nesta rodada. Isso pode significar estabilidade ou ausência de histórico suficiente para comparação.": (
            "No signals were recorded in this round. This may indicate stability or insufficient history for "
            "comparison."
        ),
        "Ainda não há linha do tempo institucional disponível para este recorte.": (
            "There is no institutional timeline available for this scope yet."
        ),
        "Vídeos localizados na instituição": "Videos located in the institution",
        "Categoria:": "Category:",
        "Subcategoria:": "Subcategory:",
        "Domínio:": "Domain:",
        "Situação da verificação:": "Verification status:",
        "Links de vídeo:": "Video links:",
        "Sinais embutidos:": "Embedded signals:",
        "Tipo de arquivo:": "Archive type:",
        "Plataformas detectadas:": "Detected platforms:",
        ": ainda sem dados para exportação.": ": still no data available for export.",
        "Etapa 1": "Stage 1",
        "Etapa 2": "Stage 2",
        "da expansão.": "of the expansion.",
        "Regra audiovisual desta categoria:": "Audiovisual rule for this category:",
        "Critério de entrada nesta etapa:": "Entry criterion at this stage:",
        "Categoria analítica:": "Analytical category:",
        "Etapa de expansão:": "Expansion stage:",
        "Unidade do observatório:": "Observatory unit:",
        "Política de expansão aplicável:": "Applicable expansion policy:",
        "Regra audiovisual do recorte:": "Audiovisual rule for the scope:",
        "Leitura metodológica de retorno zero:": "Methodological reading of zero return:",
        "Fonte-base com status de": "Base source with status of",
        "Fonte-base sem data pública de status declarada nos metadados.": (
            "Base source with no public status date declared in the metadata."
        ),
        "Camada analítica atualizada em": "Analytical layer updated on",
        "Metadados da rodada gerados em": "Round metadata generated on",
        "Nenhum relatório de": "No report for",
        "O relatório de": "The report for",
        "está disponível nesta versão do observatório.": "is available in this version of the observatory.",
        "está disponível, mas não trouxe instituições para análise.": (
            "is available, but did not return institutions for analysis."
        ),
        "não trouxe identificadores institucionais suficientes para navegação.": (
            "did not return enough institutional identifiers for navigation."
        ),
        "As verificações registram respostas dos sites, bloqueios por JS/cookies, problemas de TLS e contagens preliminares. Total de verificações bloqueadas:": (
            "The checks record site responses, JS/cookie blocks, TLS problems and preliminary counts. Total blocked "
            "checks:"
        ),
        "Esta categoria reúne apenas unidades classificadas como": "This category includes only units classified as",
        "O observatório permite trabalhar com todas elas em conjunto, mas sempre preservando o mesmo nível analítico:": (
            "The observatory allows them to be examined together, while always preserving the same analytical level:"
        ),
        "Este recorte toma o **": "This scope takes **",
        "** como unidade especializada em audiovisual.": "** as a specialized audiovisual unit.",
        "Diferentemente do APE, que funciona como portal geral de arquivos, aqui o audiovisual tende a ocupar uma posição institucional central.": (
            "Unlike APE, which functions as a general archival portal, audiovisual material tends to occupy a central "
            "institutional position here."
        ),
        "Examinar como um arquivo explicitamente audiovisual organiza a presença pública de seus vídeos, coleções, descrições e mediações digitais.": (
            "To examine how an explicitly audiovisual archive organizes the public presence of its videos, "
            "collections, descriptions and digital mediations."
        ),
        "Neste recorte, a questão central já não é apenas a existência de evidência pública detectável, mas a forma como um arquivo especializado apresenta, contextualiza e distribui seu audiovisual na web institucional.": (
            "In this scope, the central question is no longer only the existence of detectable public evidence, but "
            "how a specialized archive presents, contextualizes and distributes its audiovisual material on the "
            "institutional web."
        ),
        "Nenhum link de vídeo foi localizado ainda no recorte": "No video link has yet been located in the scope",
        "Tema selecionado:": "Selected theme:",
        "vídeos no recorte atual.": "videos in the current scope.",
        "Instituições analisadas em": "Institutions analyzed in",
        "Problema registrado na verificação:": "Problem recorded in the verification:",
        "Plataforma:": "Platform:",
        "Tema sugerido:": "Suggested theme:",
        "Modalidade de acesso:": "Access modality:",
        "Data de publicação:": "Publication date:",
        "Abrir site institucional": "Open institutional site",
        "Infraestruturas que reúnem descrições, metadados e links de múltiplas instituições arquivísticas.": (
            "Infrastructures that bring together descriptions, metadata and links from multiple archival institutions."
        ),
        "Nesta categoria, a unidade analítica central é o conjunto de instituições agregadas pela plataforma, e não a plataforma como se fosse um único arquivo.": (
            "In this category, the central analytical unit is the set of institutions aggregated by the platform, not "
            "the platform as if it were a single archive."
        ),
        "Entram primeiro na expansão do observatório, porque ampliam cobertura de forma mais rápida, comparável e metodologicamente sólida.": (
            "They enter the observatory expansion first because they expand coverage more quickly, comparably and "
            "methodologically solidly."
        ),
        "Agregadores continentais, supranacionais ou de grande escala que reúnam múltiplas instituições arquivísticas e permitam extração comparável.": (
            "Continental, supranational or large-scale aggregators that bring together multiple archival "
            "institutions and allow comparable extraction."
        ),
        "instituições agregadas": "aggregated institutions",
        "Podem integrar o observatório mesmo quando retornam zero arquivos audiovisuais, desde que funcionem como fonte comparável de pesquisa para localizar ou testar a presença pública do audiovisual.": (
            "They may be part of the observatory even when they return zero audiovisual files, provided they function "
            "as a comparable research source for locating or testing the public presence of audiovisual material."
        ),
        "Arquivos e instituições custodiais tomados como unidade própria de observação, com autonomia institucional e superfície pública específica.": (
            "Archives and custodial institutions taken as their own unit of observation, with institutional autonomy "
            "and a specific public surface."
        ),
        "Nesta categoria, a unidade analítica é o próprio arquivo ou instituição arquivística, tratada como corpus autônomo.": (
            "In this category, the analytical unit is the archive or archival institution itself, treated as an "
            "autonomous corpus."
        ),
        "Entram após os agregadores, preenchendo lacunas e incorporando instituições que não estejam cobertas pelas infraestruturas agregadoras.": (
            "They enter after the aggregators, filling gaps and incorporating institutions not covered by aggregator "
            "infrastructures."
        ),
        "Instituições individuais não cobertas pelos agregadores priorizados, ou instituições estratégicas para contraste metodológico.": (
            "Individual institutions not covered by prioritized aggregators, or strategic institutions for "
            "methodological contrast."
        ),
        "arquivos-corpus": "archive-corpora",
        "Entram prioritariamente quando não estiverem cobertos pelos agregadores já mapeados e quando ajudarem a aprofundar a observação do audiovisual.": (
            "They enter as a priority when they are not covered by already mapped aggregators and when they help "
            "deepen the observation of audiovisual material."
        ),
        "Sim": "Yes",
        "Não": "No",
        "Abrir vídeo": "Open video",
        "Exportar": "Export",
        "Ainda não há": "There is not yet",
        "Nenhum": "No",
        "Nenhuma": "No",
    },
}


def language_code_from_label(label: str | None) -> str:
    return LANGUAGE_CODES_BY_LABEL.get(str(label or ""), DEFAULT_LANGUAGE)


def t(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    language = language if language in TRANSLATIONS else DEFAULT_LANGUAGE
    text = TRANSLATIONS.get(language, {}).get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**kwargs) if kwargs else text


def _compact_text(value: str) -> str:
    return " ".join(str(value).split())


def _lower_initial(value: str) -> str:
    return value[:1].lower() + value[1:] if value else value


def _expand_replacements(replacements: dict[str, str]) -> dict[str, str]:
    expanded = dict(replacements)
    for source, target in replacements.items():
        if source[:1].isupper():
            expanded.setdefault(_lower_initial(source), _lower_initial(target))
    return expanded


def _replace_phrase(value: str, source: str, target: str) -> str:
    pattern = re.escape(source)
    if source[:1].isalnum():
        pattern = rf"(?<!\w){pattern}"
    if source[-1:].isalnum():
        pattern = rf"{pattern}(?!\w)"
    return re.sub(pattern, target, value)


def translate_ui_text(value, language: str = DEFAULT_LANGUAGE):
    if not isinstance(value, str) or language == DEFAULT_LANGUAGE:
        return value
    replacements = _expand_replacements(PHRASE_TRANSLATIONS.get(language, {}))
    if value in replacements:
        return replacements[value]

    compact_value = _compact_text(value)
    compact_replacements = {_compact_text(source): target for source, target in replacements.items()}
    if compact_value in compact_replacements:
        return compact_replacements[compact_value]

    translated = value
    for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        translated = _replace_phrase(translated, source, target)
    return translated


__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_OPTIONS",
    "language_code_from_label",
    "t",
    "translate_ui_text",
]
