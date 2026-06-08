from .config import (
    AAPB_FAQ_URL,
    AAMOD_HOME_URL,
    APE_CONTENT_PDF_URL,
    ARCHIPOP_FILMS_URL,
    EUSCREEN_COLLECTIONS_URL,
    EUROPEAN_FILM_GATEWAY_HOME_URL,
    EUROPEANA_HOME_URL,
    INA_INSTITUTION_URL,
    PARES_HOME_URL,
    PPA_HOME_URL,
    SFA_HOME_URL,
)
from .output_files import (
    AAPB_OUTPUT_FILES,
    AAMOD_OUTPUT_FILES,
    APE_OUTPUT_FILES,
    ARCHIPOP_OUTPUT_FILES,
    EUSCREEN_OUTPUT_FILES,
    EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
    EUROPEANA_OUTPUT_FILES,
    INA_OUTPUT_FILES,
    PARES_OUTPUT_FILES,
    PPA_OUTPUT_FILES,
    SFA_OUTPUT_FILES,
    list_aapb_output_filenames,
    list_aamod_output_filenames,
    list_ape_output_filenames,
    list_archipop_output_filenames,
    list_euscreen_output_filenames,
    list_european_film_gateway_output_filenames,
    list_europeana_output_filenames,
    list_ina_output_filenames,
    list_pares_output_filenames,
    list_ppa_output_filenames,
    list_sfa_output_filenames,
)


OBSERVATORY_PROFILE = {
    "label": "Memória Audiovisual em Rede",
    "role": "organismo agregador mundial em construção",
    "refresh_cadence": "mensal",
    "description": (
        "O observatório se comporta como um organismo em crescimento e articula, em uma "
        "mesma infraestrutura analítica, agregadores "
        "arquivísticos e arquivos ou instituições custodiais, mantendo essas unidades "
        "separadas para comparação rigorosa."
    ),
    "expansion_strategy": (
        "A expansão começa pelos agregadores continentais ou supranacionais e, depois, "
        "incorpora arquivos e instituições não cobertos por esses agregadores."
    ),
    "audiovisual_rule": (
        "O foco do observatório é o audiovisual. Fontes gerais continuam relevantes como "
        "base de pesquisa, mas só contam positivamente quando apresentam evidência pública "
        "detectável de audiovisual com imagem em movimento; sinais sem imagem em movimento "
        "ficam fora do escopo."
    ),
}


CORPUS_CATEGORIES = {
    "aggregator": {
        "code": "aggregator",
        "label": "Agregadores arquivísticos",
        "short_label": "Agregadores",
        "expansion_priority": 1,
        "expansion_stage_label": "Etapa 1",
        "description": (
            "Infraestruturas que reúnem descrições, metadados e links de múltiplas "
            "instituições arquivísticas."
        ),
        "method_note": (
            "Nesta categoria, a unidade analítica central é o conjunto de instituições "
            "agregadas pela plataforma, e não a plataforma como se fosse um único arquivo."
        ),
        "expansion_rule": (
            "Entram primeiro na expansão do observatório, porque ampliam cobertura de forma "
            "mais rápida, comparável e metodologicamente sólida."
        ),
        "inclusion_criterion": (
            "Agregadores continentais, supranacionais ou de grande escala que reúnam múltiplas "
            "instituições arquivísticas e permitam extração comparável."
        ),
        "selection_scope_label": "instituições agregadas",
        "audiovisual_entry_rule": (
            "Podem integrar o observatório mesmo quando retornam zero arquivos audiovisuais, "
            "desde que funcionem como fonte comparável de pesquisa para localizar ou testar "
            "a presença pública do audiovisual."
        ),
    },
    "institution": {
        "code": "institution",
        "label": "Arquivos e instituições arquivísticas",
        "short_label": "Arquivos",
        "expansion_priority": 2,
        "expansion_stage_label": "Etapa 2",
        "description": (
            "Arquivos e instituições custodiais tomados como unidade própria de observação, com "
            "autonomia institucional e superfície pública específica."
        ),
        "method_note": (
            "Nesta categoria, a unidade analítica é o próprio arquivo ou instituição arquivística, "
            "tratada como corpus autônomo."
        ),
        "expansion_rule": (
            "Entram após os agregadores, preenchendo lacunas e incorporando instituições "
            "que não estejam cobertas pelas infraestruturas agregadoras."
        ),
        "inclusion_criterion": (
            "Instituições individuais não cobertas pelos agregadores priorizados, ou "
            "instituições estratégicas para contraste metodológico."
        ),
        "selection_scope_label": "arquivos-corpus",
        "audiovisual_entry_rule": (
            "Entram prioritariamente quando não estiverem cobertos pelos agregadores já "
            "mapeados e quando ajudarem a aprofundar a observação do audiovisual."
        ),
    },
}


CORPORA = {
    "ape": {
        "code": "ape",
        "label": "Archives Portal Europe",
        "short_label": "APE",
        "category_code": "aggregator",
        "expansion_priority": 1,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador continental",
        "scope": "portal geral de arquivos",
        "methodological_unit": "instituições agregadas pelo portal",
        "ape_relationship": "o próprio APE, tratado como agregador arquivístico",
        "expansion_rationale": (
            "Funciona como base de expansão de grande escala e como linha de base para "
            "comparar instituições agregadas."
        ),
        "observatory_role": "fonte agregadora continental para o observatório mundial",
        "audiovisual_scope_note": (
            "É uma fonte geral de pesquisa. A presença de audiovisual precisa ser "
            "demonstrada empiricamente nas instituições agregadas."
        ),
        "zero_result_policy": (
            "Pode permanecer no observatório mesmo quando instituições específicas retornam "
            "zero audiovisual, porque isso também informa a pesquisa sobre visibilidade, "
            "digitalização e acesso público."
        ),
        "source_url": APE_CONTENT_PDF_URL,
        "output_files": APE_OUTPUT_FILES,
        "list_output_filenames": list_ape_output_filenames,
        "detail_url_field": "ape_detail_url",
        "content_flag_field": "content_available_in_ape",
        "detail_url_label": "ficha da instituição no APE",
        "content_flag_label": "conteúdo publicado no APE",
        "website_label": "webpage no APE",
        "run_script": "python scripts/run_pipeline.py",
        "build_script": "python scripts/build_ape_analytics.py",
        "check_script": "python scripts/check_ape_outputs.py",
        "run_script_path": "scripts/run_pipeline.py",
        "build_script_path": "scripts/build_ape_analytics.py",
        "check_script_path": "scripts/check_ape_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "ina": {
        "code": "ina",
        "label": "Institut national de l'audiovisuel",
        "short_label": "INA",
        "category_code": "institution",
        "expansion_priority": 2,
        "entity_level": "instituição custodial",
        "coverage_level": "instituição individual",
        "scope": "arquivo especializado em audiovisual",
        "methodological_unit": "instituição arquivística especializada",
        "ape_relationship": (
            "referenciado em descrições do APE, mas tratado aqui como corpus "
            "institucional autônomo"
        ),
        "expansion_rationale": (
            "Entra como instituição estratégica para contraste analítico, sem ser tomada "
            "como equivalente a um agregador."
        ),
        "observatory_role": "arquivo-corpus incorporado fora dos agregadores",
        "audiovisual_scope_note": (
            "É uma unidade institucional voltada ao audiovisual, usada para contraste "
            "com agregadores gerais."
        ),
        "zero_result_policy": (
            "Se retornasse zero audiovisual, isso exigiria revisão metodológica mais forte, "
            "porque aqui o audiovisual é central à identidade institucional."
        ),
        "source_url": INA_INSTITUTION_URL,
        "output_files": INA_OUTPUT_FILES,
        "list_output_filenames": list_ina_output_filenames,
        "detail_url_field": "ina_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "página institucional do INA na fonte",
        "content_flag_label": "conteúdo institucional publicado na fonte",
        "website_label": "site institucional informado na fonte",
        "run_script": "python scripts/run_ina_pipeline.py",
        "build_script": "python scripts/build_ina_analytics.py",
        "check_script": "python scripts/check_ina_outputs.py",
        "run_script_path": "scripts/run_ina_pipeline.py",
        "build_script_path": "scripts/build_ina_analytics.py",
        "check_script_path": "scripts/check_ina_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "archipop": {
        "code": "archipop",
        "label": "ARCHIPOP",
        "short_label": "ARCHIPOP",
        "category_code": "institution",
        "expansion_priority": 3,
        "entity_level": "instituição custodial",
        "coverage_level": "instituição individual europeia",
        "scope": "arquivo regional de filmes amadores e arquivos audiovisuais privados",
        "methodological_unit": "fichas públicas do catálogo Les Films",
        "ape_relationship": (
            "identificado na varredura europeia via INEDITS e tratado como corpus institucional "
            "autônomo, não como agregador"
        ),
        "expansion_rationale": (
            "É o primeiro repositório individual da fila europeia implantado após o fechamento "
            "da varredura, com plataforma pública de filmes, metadados e player incorporado."
        ),
        "observatory_role": "arquivo-corpus europeu incorporado por validação individual",
        "audiovisual_scope_note": (
            "É um arquivo explicitamente audiovisual. A rota pública Les Films expõe fichas de filmes "
            "amadores e familiares com metadados, descrições e players incorporados."
        ),
        "zero_result_policy": (
            "Se retornar zero audiovisual, isso indica mudança de rota, bloqueio técnico ou alteração "
            "estrutural da plataforma, pois o audiovisual é central ao corpus."
        ),
        "source_url": ARCHIPOP_FILMS_URL,
        "output_files": ARCHIPOP_OUTPUT_FILES,
        "list_output_filenames": list_archipop_output_filenames,
        "detail_url_field": "archipop_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "página institucional do ARCHIPOP",
        "content_flag_label": "conteúdo audiovisual publicado na fonte",
        "website_label": "catálogo Les Films",
        "run_script": "python scripts/run_archipop_pipeline.py",
        "build_script": "python scripts/run_archipop_pipeline.py",
        "check_script": "python scripts/check_archipop_outputs.py",
        "run_script_path": "scripts/run_archipop_pipeline.py",
        "build_script_path": "scripts/run_archipop_pipeline.py",
        "check_script_path": "scripts/check_archipop_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "aamod": {
        "code": "aamod",
        "label": "Archivio Audiovisivo del movimento operaio e democratico",
        "short_label": "AAMOD",
        "category_code": "institution",
        "expansion_priority": 3,
        "entity_level": "instituição custodial",
        "coverage_level": "instituição individual europeia",
        "scope": "arquivo italiano audiovisual e filmoteca/videoteca institucional",
        "methodological_unit": "superfície oficial do site, vídeos incorporados e fichas públicas WordPress",
        "ape_relationship": (
            "identificado na varredura europeia via European Film Gateway e tratado como "
            "corpus institucional autônomo"
        ),
        "expansion_rationale": (
            "Entra após validação individual da fila europeia. O catálogo digital xDams é declarado "
            "pela instituição, mas não respondeu de forma estável; por isso o MVP usa apenas rotas "
            "oficiais públicas reproduzíveis."
        ),
        "observatory_role": "arquivo-corpus europeu incorporado por validação individual",
        "audiovisual_scope_note": (
            "É um arquivo explicitamente audiovisual. A coleta registra vídeos incorporados no site "
            "oficial e fichas públicas de filmes, sem baixar mídia e sem inferir cobertura total do catálogo."
        ),
        "zero_result_policy": (
            "Se retornar zero audiovisual, isso indica mudança de rota, bloqueio técnico ou alteração "
            "estrutural da superfície pública, pois o audiovisual é central ao corpus."
        ),
        "source_url": AAMOD_HOME_URL,
        "output_files": AAMOD_OUTPUT_FILES,
        "list_output_filenames": list_aamod_output_filenames,
        "detail_url_field": "aamod_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "página institucional do AAMOD",
        "content_flag_label": "conteúdo audiovisual publicado na fonte",
        "website_label": "site institucional do AAMOD",
        "run_script": "python scripts/run_aamod_pipeline.py",
        "build_script": "python scripts/run_aamod_pipeline.py",
        "check_script": "python scripts/check_aamod_outputs.py",
        "run_script_path": "scripts/run_aamod_pipeline.py",
        "build_script_path": "scripts/run_aamod_pipeline.py",
        "check_script_path": "scripts/check_aamod_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "sfa": {
        "code": "sfa",
        "label": "Arhiv Republike Slovenije - Slovenski filmski arhiv",
        "short_label": "SFA",
        "category_code": "institution",
        "expansion_priority": 3,
        "entity_level": "instituição custodial",
        "coverage_level": "instituição individual europeia",
        "scope": "arquivo nacional esloveno especializado em patrimônio fílmico",
        "methodological_unit": "fundo SI AS 1086 e fichas públicas de filmes no VAČ",
        "ape_relationship": (
            "identificado na varredura europeia via FIAF e relacionado ao Arhiv Republike Slovenije "
            "presente no APE, mas tratado como corpus institucional audiovisual autônomo"
        ),
        "expansion_rationale": (
            "Entra após validação individual da fila europeia. A rota antiga arhiv.gov.si é instável, "
            "mas a página oficial atual no GOV.SI e as fichas públicas do VAČ permitem materializar "
            "metadados filmográficos reproduzíveis."
        ),
        "observatory_role": "arquivo-corpus europeu incorporado por validação individual",
        "audiovisual_scope_note": (
            "É um arquivo explicitamente fílmico/audiovisual. A coleta registra metadados públicos de "
            "filmes no VAČ, sem baixar mídia e sem pressupor player público nas fichas."
        ),
        "zero_result_policy": (
            "Se retornar zero registros, isso indica mudança de rota, bloqueio técnico ou alteração "
            "estrutural da superfície pública, pois o fundo SI AS 1086 é explicitamente filmográfico."
        ),
        "source_url": SFA_HOME_URL,
        "output_files": SFA_OUTPUT_FILES,
        "list_output_filenames": list_sfa_output_filenames,
        "detail_url_field": "sfa_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "página institucional do Slovenski filmski arhiv",
        "content_flag_label": "metadados audiovisuais publicados na fonte",
        "website_label": "catálogo VAČ",
        "run_script": "python scripts/run_sfa_pipeline.py",
        "build_script": "python scripts/run_sfa_pipeline.py",
        "check_script": "python scripts/check_sfa_outputs.py",
        "run_script_path": "scripts/run_sfa_pipeline.py",
        "build_script_path": "scripts/run_sfa_pipeline.py",
        "check_script_path": "scripts/check_sfa_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "euscreen": {
        "code": "euscreen",
        "label": "EUscreen",
        "short_label": "EUscreen",
        "category_code": "aggregator",
        "expansion_priority": 2,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador audiovisual europeu",
        "scope": "agregador temático audiovisual",
        "methodological_unit": "catálogo audiovisual agregado pela plataforma",
        "ape_relationship": (
            "complementa o APE no fechamento europeu, mas opera como agregador "
            "temático audiovisual, não como portal geral de arquivos"
        ),
        "expansion_rationale": (
            "Entra como fechamento europeu prioritário porque reúne audiovisual de "
            "múltiplas instituições e permite observar circulação transnacional em plataforma especializada."
        ),
        "observatory_role": "agregador audiovisual europeu incorporado ao organismo",
        "audiovisual_scope_note": (
            "É uma fonte agregadora especializada em audiovisual, usada para contrastar "
            "com o APE e aprofundar a circulação cultural transnacional do audiovisual europeu."
        ),
        "zero_result_policy": (
            "Se retornasse zero audiovisual, isso indicaria falha metodológica ou mudança estrutural "
            "na superfície pública do agregador, pois o audiovisual é central à plataforma."
        ),
        "source_url": EUSCREEN_COLLECTIONS_URL,
        "output_files": EUSCREEN_OUTPUT_FILES,
        "list_output_filenames": list_euscreen_output_filenames,
        "detail_url_field": "euscreen_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "página de coleções do EUscreen",
        "content_flag_label": "conteúdo audiovisual publicado na fonte",
        "website_label": "site institucional informado na fonte",
        "run_script": "python scripts/run_euscreen_pipeline.py",
        "build_script": "python scripts/build_euscreen_analytics.py",
        "check_script": "python scripts/check_euscreen_outputs.py",
        "run_script_path": "scripts/run_euscreen_pipeline.py",
        "build_script_path": "scripts/build_euscreen_analytics.py",
        "check_script_path": "scripts/check_euscreen_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "european-film-gateway": {
        "code": "european-film-gateway",
        "label": "European Film Gateway",
        "short_label": "EFG",
        "category_code": "aggregator",
        "expansion_priority": 3,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador audiovisual europeu",
        "scope": "agregador temático cinematográfico e audiovisual",
        "methodological_unit": "registros audiovisuais agregados pela plataforma",
        "ape_relationship": (
            "complementa o APE no fechamento europeu como agregador temático de cinema, "
            "sem ser tratado como arquivo custodial individual"
        ),
        "expansion_rationale": (
            "Entra antes da expansão continental porque é um agregador europeu especializado "
            "em patrimônio fílmico e audiovisual, com relevância direta para o recorte do observatório."
        ),
        "observatory_role": "agregador audiovisual europeu incorporado em modo cauteloso",
        "audiovisual_scope_note": (
            "É uma fonte especializada em cinema e audiovisual. Falhas de acesso público são "
            "registradas como instabilidade técnica, não como ausência de acervo."
        ),
        "zero_result_policy": (
            "Se retornar zero audiovisual, o resultado exige nota metodológica forte, porque "
            "a identidade pública do agregador é audiovisual."
        ),
        "source_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
        "output_files": EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
        "list_output_filenames": list_european_film_gateway_output_filenames,
        "detail_url_field": "efg_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "portal European Film Gateway",
        "content_flag_label": "conteúdo audiovisual publicado na fonte",
        "website_label": "site do agregador",
        "run_script": "python scripts/run_european_film_gateway_pipeline.py",
        "build_script": "python scripts/build_european_film_gateway_analytics.py",
        "check_script": "python scripts/check_european_film_gateway_outputs.py",
        "run_script_path": "scripts/run_european_film_gateway_pipeline.py",
        "build_script_path": "scripts/build_european_film_gateway_analytics.py",
        "check_script_path": "scripts/check_european_film_gateway_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "europeana": {
        "code": "europeana",
        "label": "Europeana",
        "short_label": "Europeana",
        "category_code": "aggregator",
        "expansion_priority": 4,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador cultural europeu",
        "scope": "agregador cultural digital com recorte audiovisual",
        "methodological_unit": "registros de mídia e metadados culturais filtrados por sinais audiovisuais",
        "ape_relationship": (
            "complementa o APE como agregador europeu amplo, mas exige separação explícita "
            "entre patrimônio cultural geral e recorte audiovisual."
        ),
        "expansion_rationale": (
            "Entra antes da expansão continental porque opera em escala europeia e oferece "
            "superfície pública de busca por mídia, além de documentação de APIs."
        ),
        "observatory_role": "agregador cultural europeu incorporado com recorte audiovisual",
        "audiovisual_scope_note": (
            "É uma fonte geral de patrimônio cultural. O audiovisual só conta quando há "
            "sinal público detectável em buscas filtradas por mídia ou metadados de item."
        ),
        "zero_result_policy": (
            "Retorno zero não equivale a ausência de audiovisual europeu, mas a limite de "
            "visibilidade, indexação, API ou filtragem da plataforma."
        ),
        "source_url": EUROPEANA_HOME_URL,
        "output_files": EUROPEANA_OUTPUT_FILES,
        "list_output_filenames": list_europeana_output_filenames,
        "detail_url_field": "europeana_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "portal Europeana",
        "content_flag_label": "conteúdo audiovisual detectável na fonte",
        "website_label": "site do agregador",
        "run_script": "python scripts/run_europeana_pipeline.py",
        "build_script": "python scripts/build_europeana_analytics.py",
        "check_script": "python scripts/check_europeana_outputs.py",
        "run_script_path": "scripts/run_europeana_pipeline.py",
        "build_script_path": "scripts/build_europeana_analytics.py",
        "check_script_path": "scripts/check_europeana_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "pares": {
        "code": "pares",
        "label": "PARES",
        "short_label": "PARES",
        "category_code": "aggregator",
        "expansion_priority": 5,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional europeu",
        "scope": "portal geral de arquivos",
        "methodological_unit": "registros recuperados pela busca pública do agregador",
        "ape_relationship": (
            "complementa o APE no fechamento europeu como agregador nacional espanhol, "
            "sem ser tratado como instituição custodial individual"
        ),
        "expansion_rationale": (
            "Entra como corpus nacional incorporado após validação técnica da busca pública "
            "e detecção de resultados para termos audiovisuais."
        ),
        "observatory_role": "agregador nacional europeu incorporado ao organismo",
        "audiovisual_scope_note": (
            "É uma fonte geral de pesquisa. A presença audiovisual é inferida inicialmente por "
            "termos de busca e por sinais de objeto digitalizado, exigindo curadoria posterior."
        ),
        "zero_result_policy": (
            "Se retornar zero audiovisual, permanece como evidência sobre limites de visibilidade "
            "da fonte geral, sem equivaler a ausência de acervo audiovisual espanhol."
        ),
        "source_url": PARES_HOME_URL,
        "output_files": PARES_OUTPUT_FILES,
        "list_output_filenames": list_pares_output_filenames,
        "detail_url_field": "pares_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "portal PARES",
        "content_flag_label": "resultado audiovisual detectável na fonte",
        "website_label": "site do agregador",
        "run_script": "python scripts/run_pares_pipeline.py",
        "build_script": "python scripts/build_pares_analytics.py",
        "check_script": "python scripts/check_pares_outputs.py",
        "run_script_path": "scripts/run_pares_pipeline.py",
        "build_script_path": "scripts/build_pares_analytics.py",
        "check_script_path": "scripts/check_pares_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "portal-portugues-arquivos": {
        "code": "portal-portugues-arquivos",
        "label": "Portal Português de Arquivos",
        "short_label": "PPA",
        "category_code": "aggregator",
        "expansion_priority": 6,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional europeu",
        "scope": "portal geral de arquivos",
        "methodological_unit": "registros recuperados pela busca pública do agregador",
        "ape_relationship": (
            "complementa o APE no fechamento europeu como agregador nacional português, "
            "sem ser tratado como instituição custodial individual"
        ),
        "expansion_rationale": (
            "Entra como corpus nacional incorporado após validação total da busca pública "
            "e detecção de resultados para termos audiovisuais."
        ),
        "observatory_role": "agregador nacional europeu incorporado ao organismo",
        "audiovisual_scope_note": (
            "É uma fonte geral de pesquisa. A presença audiovisual é inferida por termos de "
            "busca, descrições e ligações às fontes originais, sem equivaler automaticamente "
            "à reprodução pública de vídeo."
        ),
        "zero_result_policy": (
            "Se retornar zero audiovisual, permanece como evidência sobre limites de visibilidade "
            "da fonte geral, sem equivaler a ausência de acervo audiovisual português."
        ),
        "source_url": PPA_HOME_URL,
        "output_files": PPA_OUTPUT_FILES,
        "list_output_filenames": list_ppa_output_filenames,
        "detail_url_field": "ppa_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "Portal Português de Arquivos",
        "content_flag_label": "resultado audiovisual detectável na fonte",
        "website_label": "site do agregador",
        "run_script": "python scripts/run_ppa_pipeline.py",
        "build_script": "python scripts/build_ppa_analytics.py",
        "check_script": "python scripts/check_ppa_outputs.py",
        "run_script_path": "scripts/run_ppa_pipeline.py",
        "build_script_path": "scripts/build_ppa_analytics.py",
        "check_script_path": "scripts/check_ppa_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
    "aapb": {
        "code": "aapb",
        "label": "American Archive of Public Broadcasting",
        "short_label": "AAPB",
        "category_code": "aggregator",
        "expansion_priority": 8,
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional norte-americano",
        "scope": "agregador temático audiovisual",
        "methodological_unit": "registros PBCore recuperados pela API pública do agregador",
        "ape_relationship": (
            "entra após o fechamento europeu como primeiro corpus audiovisual extraeuropeu, "
            "sem ser confundido com agregador continental"
        ),
        "expansion_rationale": (
            "A fila global priorizou o AAPB após o protocolo do ArchiveGrid, porque a rota "
            "API JSON/PBCore permite coleta leve, reprodutível e diretamente audiovisual."
        ),
        "observatory_role": "agregador audiovisual nacional incorporado ao organismo",
        "audiovisual_scope_note": (
            "É uma fonte especializada em televisão pública e registros audiovisuais; a presença "
            "audiovisual é materializada por registros PBCore retornados pela API pública."
        ),
        "zero_result_policy": (
            "Se retornar zero audiovisual, isso indicaria falha de rota ou mudança estrutural, "
            "pois o audiovisual é constitutivo da fonte."
        ),
        "source_url": AAPB_FAQ_URL,
        "output_files": AAPB_OUTPUT_FILES,
        "list_output_filenames": list_aapb_output_filenames,
        "detail_url_field": "aapb_detail_url",
        "content_flag_field": "content_available_in_source",
        "detail_url_label": "página institucional do AAPB",
        "content_flag_label": "conteúdo audiovisual detectável na fonte",
        "website_label": "site do agregador",
        "run_script": "python scripts/run_aapb_pipeline.py",
        "build_script": "python scripts/run_aapb_pipeline.py",
        "check_script": "python scripts/check_aapb_outputs.py",
        "run_script_path": "scripts/run_aapb_pipeline.py",
        "build_script_path": "scripts/run_aapb_pipeline.py",
        "check_script_path": "scripts/check_aapb_outputs.py",
        "organism_active": True,
        "monthly_refresh_enabled": True,
    },
}


def get_corpus_definition(code):
    return CORPORA[code]


def get_category_definition(code):
    return CORPUS_CATEGORIES[code]


def list_corpora_by_category(category_code):
    return [
        corpus_definition
        for corpus_definition in CORPORA.values()
        if corpus_definition["category_code"] == category_code
    ]


def list_active_corpora(*, monthly_only=False):
    corpora = [
        corpus_definition
        for corpus_definition in CORPORA.values()
        if corpus_definition.get("organism_active", False)
    ]
    if monthly_only:
        corpora = [
            corpus_definition
            for corpus_definition in corpora
            if corpus_definition.get("monthly_refresh_enabled", False)
        ]
    return sorted(
        corpora,
        key=lambda corpus_definition: (
            CORPUS_CATEGORIES[corpus_definition["category_code"]]["expansion_priority"],
            corpus_definition["expansion_priority"],
            corpus_definition["short_label"],
        ),
    )


__all__ = [
    "OBSERVATORY_PROFILE",
    "CORPORA",
    "CORPUS_CATEGORIES",
    "get_category_definition",
    "get_corpus_definition",
    "list_active_corpora",
    "list_corpora_by_category",
]
