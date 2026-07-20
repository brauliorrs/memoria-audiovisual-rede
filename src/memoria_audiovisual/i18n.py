from __future__ import annotations


LANGUAGE_OPTIONS = {
    "pt": "Português",
    "es": "Español",
    "en": "English",
}

LANGUAGE_CODES_BY_LABEL = {label: code for code, label in LANGUAGE_OPTIONS.items()}
DEFAULT_LANGUAGE = "pt"


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
            "Este observatório integra a formulação de um projeto de pós-doutorado a ser submetido à Universidade "
            "de Valência, no âmbito do **Communication and Media Culture History Research Group**.\n\n"
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
        "documented_case_tab": "Caso documentado: {label}",
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
            "Este observatorio forma parte de la formulación de un proyecto de posdoctorado que será presentado "
            "a la Universidad de Valencia, en el ámbito del **Communication and Media Culture History Research "
            "Group**.\n\n"
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
            "This observatory is part of the formulation of a postdoctoral project to be submitted to the "
            "University of Valencia, within the **Communication and Media Culture History Research Group**.\n\n"
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
        "Territórios": "Territorios",
        "Tabelas": "Tablas",
        "Instituições": "Instituciones",
        "Ficha institucional": "Ficha institucional",
        "Categoria": "Categoría",
        "Unidade": "Unidad",
        "Caso documentado": "Caso documentado",
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
        "Índice público Europa": "Índice público Europa",
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
        "Modalidade de acesso": "Modalidad de acceso",
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
        "Temas por plataforma": "Temas por plataforma",
        "Temas por país": "Temas por país",
        "Temas por tipo de arquivo": "Temas por tipo de archivo",
        "Visibilidade por tipo de arquivo": "Visibilidad por tipo de archivo",
        "Casos indisponíveis": "Casos no disponibles",
        "Casos com site quebrado": "Casos con sitio roto",
        "Casos instáveis": "Casos inestables",
        "Distribuição geográfica das instituições com evidência pública detectável de audiovisual": (
            "Distribución geográfica de las instituciones con evidencia pública detectable de audiovisual"
        ),
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
        "Territórios": "Territories",
        "Tabelas": "Tables",
        "Instituições": "Institutions",
        "Ficha institucional": "Institution Record",
        "Categoria": "Category",
        "Unidade": "Unit",
        "Caso documentado": "Documented Case",
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
        "Modalidade de acesso": "Access Modality",
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


def translate_ui_text(value, language: str = DEFAULT_LANGUAGE):
    if not isinstance(value, str) or language == DEFAULT_LANGUAGE:
        return value
    replacements = PHRASE_TRANSLATIONS.get(language, {})
    if value in replacements:
        return replacements[value]

    compact_value = _compact_text(value)
    compact_replacements = {_compact_text(source): target for source, target in replacements.items()}
    if compact_value in compact_replacements:
        return compact_replacements[compact_value]

    translated = value
    for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    return translated


__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_OPTIONS",
    "language_code_from_label",
    "t",
    "translate_ui_text",
]
