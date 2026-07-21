from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import OUTPUT_DIR
from .corpora import CORPORA, CORPUS_CATEGORIES, list_active_corpora


EUROPE_RESEARCH_REGISTRY_FILENAME = "observatorio_pesquisa_europa.csv"
EUROPE_RESEARCH_QUEUE_FILENAME = "observatorio_fila_pesquisa_europa.csv"
EUROPE_RESEARCH_SUMMARY_FILENAME = "observatorio_resumo_pesquisa_europa.csv"
EUROPE_RESEARCH_RULE_VERSION = "2026-05-pesquisa-europa-v3"

EUROPEANA_AGGREGATORS_SOURCE_URL = "https://pro.europeana.eu/page/aggregators"
ACE_SOURCE_URL = "https://ace-film.eu/about-ace/"
EBU_MEMBERS_SOURCE_URL = "https://www.ebu.ch/about/members"
EFG_CONTRIBUTING_ARCHIVES_SOURCE_URL = "https://ftp.europeanfilmgateway.eu/about_efg/contributing_archives"
FIAF_SOURCE_URL = "https://www.fiafnet.org/pages/Community/Members.html"
EUSCREEN_SOURCE_URL = "https://euscreen.eu/"
FIAT_IFTA_SOURCE_URL = "https://fiatifta.org/membership/members/"
INEDITS_SOURCE_URL = "https://inedits.eu/en/Members/"

EUROPE_RESEARCH_COLUMNS = [
    "unit_code",
    "unit_label",
    "unit_type",
    "source_family",
    "country_or_scope",
    "territorial_scope",
    "source_url",
    "audiovisual_relevance",
    "coverage_hint",
    "relationship_to_current_corpus",
    "organism_status",
    "queue_layer",
    "queue_decision",
    "queue_priority",
    "definitive_queue_rank",
    "queue_reason",
    "next_action",
    "inclusion_gate",
    "video_location_status",
    "video_location_candidate_url",
    "video_location_strategy",
    "blocks_expansion",
    "evidence_reference",
    "rule_version",
]

EUROPE_RESEARCH_SUMMARY_COLUMNS = [
    "camada",
    "categoria",
    "decisao",
    "total",
    "rule_version",
]

PROTOCOLLED_EUROPEAN_CODES = {
    "archives-hub",
    "francearchives",
    "fiaf-arsenal-filminstitut",
    "fiaf-cnc-aff",
    "fiat-atresmedia",
    "cinematheque-suisse",
    "fiaf-filmoteca-vaticana",
    "fiaf-filmmuseum-munchen",
    "fiaf-cineteca-italiana",
    "fiaf-cineteca-bologna",
    "fiaf-cinematheque-luxembourg",
    "inedits-ad-libitum",
    "inedits-county-archives-puy-de-dome",
    "inedits-cinematheque-corse",
    "inedits-prise-2",
}

DIRECTORY_EXPANSION_CODES = {
    "efg-contributing-archives",
    "fiaf-europe-members",
    "euscreen-network-members",
    "fiat-ifta-members",
    "inedits-members",
}

DOCUMENTED_SWEEP_SOURCE_CODES = {
    "ace-members",
    "ebu-public-service-media-members",
}

EUROPEANA_AGGREGATOR_ROWS = [
    ("carare", "CARARE", "agregador_tematico", "Europeana Aggregators Forum", "Ireland, IE", "Europa", "patrimônio arqueológico e arquitetônico; audiovisual indireto", "agregador temático"),
    ("archives-portal-europe", "Archives Portal Europe", "agregador_arquivistico", "Europeana Aggregators Forum", "Netherlands, NL", "Europa", "fonte geral com potencial audiovisual", "agregador arquivístico europeu"),
    ("euscreen", "EUscreen", "agregador_audiovisual", "Europeana Aggregators Forum", "Netherlands, NL", "Europa", "televisão e patrimônio audiovisual", "agregador audiovisual europeu"),
    ("european-fashion-heritage", "European Fashion Heritage Association", "agregador_tematico", "Europeana Aggregators Forum", "Italy, IT", "Europa", "audiovisual indireto", "agregador temático"),
    ("european-film-gateway", "The European Film Gateway", "agregador_audiovisual", "Europeana Aggregators Forum", "Germany, DE", "Europa", "cinema e patrimônio fílmico", "agregador fílmico europeu"),
    ("jewish-heritage-network", "Jewish Heritage Network", "agregador_tematico", "Europeana Aggregators Forum", "Netherlands, NL", "Europa", "audiovisual indireto", "agregador temático"),
    ("manuscriptorium", "Manuscriptorium", "agregador_tematico", "Europeana Aggregators Forum", "Czech Republic, CZ", "Europa", "baixo; manuscritos", "agregador temático"),
    ("museu", "MUSEU", "agregador_tematico", "Europeana Aggregators Forum", "Belgium, BE", "Europa", "baixo a indireto", "agregador temático"),
    ("openup", "OpenUp!", "agregador_tematico", "Europeana Aggregators Forum", "Austria, AT", "Europa", "baixo; história natural", "agregador temático"),
    ("photoconsortium", "PHOTOCONSORTIUM", "agregador_tematico", "Europeana Aggregators Forum", "Italy, IT", "Europa", "baixo; fotografia", "agregador temático"),
    ("tib", "TIB - Leibniz Information Centre for Science and Technology and University Library", "agregador_tematico", "Europeana Aggregators Forum", "Germany, DE", "Europa", "potencial vídeo científico", "agregador temático"),
    ("europeana-local-austria", "Europeana Local Austria", "agregador_nacional_regional", "Europeana Aggregators Forum", "Austria, AT", "Áustria", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("kulturpool", "Kulturpool", "agregador_nacional_regional", "Europeana Aggregators Forum", "Austria, AT", "Áustria", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("varna-public-library", "Public Library Pencho Slaveykov, Varna", "agregador_nacional_regional", "Europeana Aggregators Forum", "Bulgaria, BG", "Bulgária", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("ekultura-hr", "eKultura.hr", "agregador_nacional_regional", "Europeana Aggregators Forum", "Croatia, HR", "Croácia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("cyprus-culture", "Deputy Ministry of Culture, Republic of Cyprus", "agregador_nacional_regional", "Europeana Aggregators Forum", "Cyprus, CY", "Chipre", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("czech-digital-library", "Czech Digital Library", "agregador_nacional_regional", "Europeana Aggregators Forum", "Czech Republic, CZ", "República Tcheca", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("estonian-e-repository", "Estonian e-Repository and Conservation of Collections", "agregador_nacional_regional", "Europeana Aggregators Forum", "Estonia, EE", "Estônia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("national-library-finland", "National Library of Finland", "agregador_nacional_regional", "Europeana Aggregators Forum", "Finland, FI", "Finlândia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("gallica", "Gallica", "agregador_nacional_regional", "Europeana Aggregators Forum", "France, FR", "França", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("ribambelle", "Ribambelle", "agregador_nacional_regional", "Europeana Aggregators Forum", "France, FR", "França", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("german-digital-library", "German Digital Library", "agregador_nacional_regional", "Europeana Aggregators Forum", "Germany, DE", "Alemanha", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("searchculture-gr", "Greek Aggregator SearchCulture.gr", "agregador_nacional_regional", "Europeana Aggregators Forum", "Greece, GR", "Grécia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("forum-hungaricum", "Forum Hungaricum Non-profit Ltd.", "agregador_nacional_regional", "Europeana Aggregators Forum", "Hungary, HU", "Hungria", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("museummap", "MuseuMap", "agregador_nacional_regional", "Europeana Aggregators Forum", "Hungary, HU", "Hungria", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("digital-repository-ireland", "Digital Repository of Ireland", "agregador_nacional_regional", "Europeana Aggregators Forum", "Ireland, IE", "Irlanda", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("culturaitalia", "CulturaItalia", "agregador_nacional_regional", "Europeana Aggregators Forum", "Italy, IT", "Itália", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("lt-aggregator-service", "LT-Aggregator Service National Library of Lithuania", "agregador_nacional_regional", "Europeana Aggregators Forum", "Lithuania, LT", "Lituânia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("heritage-malta", "Heritage Malta", "agregador_nacional_regional", "Europeana Aggregators Forum", "Malta, MT", "Malta", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("dutch-collections-for-europe", "Dutch Collections for Europe", "agregador_nacional_regional", "Europeana Aggregators Forum", "Netherlands, NL", "Países Baixos", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("digital-libraries-federation", "Digital Libraries Federation", "agregador_nacional_regional", "Europeana Aggregators Forum", "Poland, PL", "Polônia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("rnod", "RNOD - National Register for Digital Objects", "agregador_nacional_regional", "Europeana Aggregators Forum", "Portugal, PT", "Portugal", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("national-heritage-institute-bucharest", "National Heritage Institute, Bucharest", "agregador_nacional_regional", "Europeana Aggregators Forum", "Romania, RO", "Romênia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("national-library-serbia", "National Library of Serbia", "agregador_nacional_regional", "Europeana Aggregators Forum", "Serbia, RS", "Sérvia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("slovenian-e-content-aggregator", "Slovenian National E-content Aggregator", "agregador_nacional_regional", "Europeana Aggregators Forum", "Slovenia, SI", "Eslovênia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("hispana", "Hispana", "agregador_nacional_regional", "Europeana Aggregators Forum", "Spain, ES", "Espanha", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("swedish-open-cultural-heritage", "Swedish Open Cultural Heritage", "agregador_nacional_regional", "Europeana Aggregators Forum", "Sweden, SE", "Suécia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("catalonica", "Catalònica", "agregador_nacional_regional", "Europeana Aggregators Forum", "Spain, ES", "Catalunha / Espanha", "fonte geral com potencial audiovisual", "agregador regional"),
    ("slovakiana", "Slovakiana", "agregador_nacional_regional", "Europeana Aggregators Forum", "Slovakia, SK", "Eslováquia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
    ("euskariana", "Euskariana", "agregador_nacional_regional", "Europeana Aggregators Forum", "Spain, ES", "País Basco / Espanha", "fonte geral com potencial audiovisual", "agregador regional"),
    ("digital-library-latvia", "Digital Library of Latvia", "agregador_nacional_regional", "Europeana Aggregators Forum", "Latvia, LV", "Letônia", "fonte geral com potencial audiovisual", "agregador nacional/regional"),
]

EUROPEAN_DIRECTORY_ROWS = [
    {
        "unit_code": "ace-members",
        "unit_label": "ACE - Association des Cinémathèques Européennes",
        "unit_type": "diretorio_de_arquivos_filmicos",
        "source_family": "ACE",
        "country_or_scope": "Europa",
        "territorial_scope": "Europa",
        "source_url": ACE_SOURCE_URL,
        "audiovisual_relevance": "rede de cinematecas e arquivos fílmicos",
        "coverage_hint": "49 arquivos fílmicos nacionais e regionais europeus",
        "evidence_reference": "ACE se apresenta como associação de 49 arquivos fílmicos europeus.",
    },
    {
        "unit_code": "efg-contributing-archives",
        "unit_label": "European Film Gateway - contributing archives",
        "unit_type": "diretorio_de_arquivos_filmicos",
        "source_family": "EFG",
        "country_or_scope": "Europa",
        "territorial_scope": "Europa",
        "source_url": EFG_CONTRIBUTING_ARCHIVES_SOURCE_URL,
        "audiovisual_relevance": "arquivos fílmicos e coleções com registros de vídeo no European Film Gateway",
        "coverage_hint": "lista pública de arquivos contribuintes do European Film Gateway",
        "evidence_reference": "EFG mantém página pública de contributing archives com links de coleção.",
    },
    {
        "unit_code": "fiaf-europe-members",
        "unit_label": "FIAF - membros europeus",
        "unit_type": "diretorio_de_arquivos_filmicos",
        "source_family": "FIAF",
        "country_or_scope": "Europa",
        "territorial_scope": "Europa",
        "source_url": FIAF_SOURCE_URL,
        "audiovisual_relevance": "arquivos fílmicos e cinematecas",
        "coverage_hint": "diretório internacional com múltiplos membros europeus",
        "evidence_reference": "FIAF mantém diretório de arquivos de filme e cinematecas membros.",
    },
    {
        "unit_code": "euscreen-network-members",
        "unit_label": "EUscreen Network - membros",
        "unit_type": "diretorio_de_arquivos_audiovisuais",
        "source_family": "EUscreen",
        "country_or_scope": "Europa",
        "territorial_scope": "Europa",
        "source_url": EUSCREEN_SOURCE_URL,
        "audiovisual_relevance": "emissoras, arquivos de mídia e instituições audiovisuais",
        "coverage_hint": "mais de 40 membros em quase 30 países europeus",
        "evidence_reference": "EUscreen declara rede com mais de 40 membros de quase 30 países.",
    },
    {
        "unit_code": "fiat-ifta-members",
        "unit_label": "FIAT/IFTA - membros",
        "unit_type": "diretorio_de_arquivos_televisivos",
        "source_family": "FIAT/IFTA",
        "country_or_scope": "Europa / mundo",
        "territorial_scope": "Europa / mundo",
        "source_url": FIAT_IFTA_SOURCE_URL,
        "audiovisual_relevance": "arquivos televisivos, multimídia e instituições de mídia com imagem em movimento",
        "coverage_hint": "diretório internacional com múltiplos membros europeus relevantes ao audiovisual televisivo",
        "evidence_reference": "FIAT/IFTA lista serviços de arquivo de organizações de radiodifusão e arquivos de programas televisivos.",
    },
    {
        "unit_code": "inedits-members",
        "unit_label": "INEDITS - Amateur Films / Memory of Europe",
        "unit_type": "diretorio_de_arquivos_audiovisuais",
        "source_family": "INEDITS",
        "country_or_scope": "Europa",
        "territorial_scope": "Europa",
        "source_url": INEDITS_SOURCE_URL,
        "audiovisual_relevance": "arquivos de filmes amadores, familiares e memória audiovisual regional",
        "coverage_hint": "rede europeia de membros institucionais e individuais ligados ao filme amador",
        "evidence_reference": "INEDITS mantém página pública de membros com instituições de preservação audiovisual.",
    },
    {
        "unit_code": "ebu-public-service-media-members",
        "unit_label": "EBU - public service media members",
        "unit_type": "diretorio_de_emissoras_publicas",
        "source_family": "EBU",
        "country_or_scope": "Europa / área europeia de radiodifusão",
        "territorial_scope": "Europa / área europeia de radiodifusão",
        "source_url": EBU_MEMBERS_SOURCE_URL,
        "audiovisual_relevance": "emissoras públicas com potencial arquivo audiovisual, mas nem sempre com acervo público coletável",
        "coverage_hint": "lista de membros de mídia pública; fonte contextual para localizar exceções fora de FIAT/IFTA",
        "evidence_reference": "EBU lista 68 membros representando 113 organizações em 56 países.",
    },
]

EUROPEAN_INDIVIDUAL_ARCHIVE_ROWS = [
    ("fiaf-national-library-wales", "National Library of Wales - Screen and Sound Archives", "arquivo_audiovisual_individual", "FIAF", "País de Gales / Reino Unido", "https://www.archif.com"),
    ("fiaf-eye-filmmuseum", "Eye Filmmuseum", "arquivo_audiovisual_individual", "FIAF", "Países Baixos", "https://www.eyefilm.nl"),
    ("fiaf-greek-film-archive", "Tainiothiki Tis Ellados / Greek Film Archive", "arquivo_audiovisual_individual", "FIAF", "Grécia", "https://www.tainiothiki.gr"),
    ("fiaf-filmoteca-catalunya", "Filmoteca de Catalunya - ICEC", "arquivo_audiovisual_individual", "FIAF", "Catalunha / Espanha", "https://www.filmoteca.cat"),
    ("fiaf-jugoslovenska-kinoteka", "Jugoslovenska Kinoteka", "arquivo_audiovisual_individual", "FIAF", "Sérvia", "https://www.kinoteka.org.rs"),
    ("fiaf-bundesarchiv", "Bundesarchiv", "arquivo_audiovisual_individual", "FIAF", "Alemanha", "https://www.bundesarchiv.de"),
    ("fiaf-arsenal-filminstitut", "Arsenal Filminstitut", "arquivo_audiovisual_individual", "FIAF", "Alemanha", "https://www.arsenal-berlin.de"),
    ("fiaf-deutsche-kinemathek", "Deutsche Kinemathek / Museum für Film und Fernsehen", "arquivo_audiovisual_individual", "FIAF", "Alemanha", "https://www.deutsche-kinemathek.de"),
    ("fiaf-lichtspiel-bern", "Lichtspiel / Kinemathek Bern", "arquivo_audiovisual_individual", "FIAF", "Suíça", "https://www.lichtspiel.ch"),
    ("fiaf-cineteca-bologna", "Fondazione Cineteca di Bologna", "arquivo_audiovisual_individual", "FIAF", "Itália", "https://www.cinetecadibologna.it"),
    ("fiaf-slovak-film-institute", "Slovak Film Institute", "arquivo_audiovisual_individual", "FIAF", "Eslováquia", "https://www.sfu.sk"),
    ("fiaf-cinematek", "Cinémathèque royale de Belgique / Koninklijk Belgisch Filmarchief", "arquivo_audiovisual_individual", "FIAF", "Bélgica", "https://www.cinematek.be"),
    ("fiaf-cinemateca-romana", "Arhiva Nationala de Filme - Cinemateca Romana", "arquivo_audiovisual_individual", "FIAF", "Romênia", "https://www.anf-cinemateca.ro"),
    ("fiaf-nfi-hungary-film-archive", "National Film Institute Hungary - Film Archive", "arquivo_audiovisual_individual", "FIAF", "Hungria", "https://filmarchiv.hu"),
    ("fiaf-danish-film-institute", "The Danish Film Institute", "arquivo_audiovisual_individual", "FIAF", "Dinamarca", "https://www.dfi.dk"),
    ("fiaf-ifi-irish-film-archive", "IFI Irish Film Archive", "arquivo_audiovisual_individual", "FIAF", "Irlanda", "https://www.ifi.ie"),
    ("fiaf-filmmuseum-dusseldorf", "Filmmuseum Düsseldorf", "arquivo_audiovisual_individual", "FIAF", "Alemanha", "https://www.duesseldorf.de"),
    ("fiaf-dff", "DFF - Deutsches Filminstitut & Filmmuseum", "arquivo_audiovisual_individual", "FIAF", "Alemanha", "https://deutsches-filminstitut.de"),
    ("fiaf-cineteca-friuli", "La Cineteca del Friuli", "arquivo_audiovisual_individual", "FIAF", "Itália", "https://www.cinetecadelfriuli.org"),
    ("fiaf-national-library-scotland-moving-image", "National Library of Scotland - Moving Image Archive", "arquivo_audiovisual_individual", "FIAF", "Escócia / Reino Unido", "https://www.nls.uk"),
    ("fiaf-kavi", "Kansallinen Audiovisuaalinen Instituutti / National Audiovisual Institute", "arquivo_audiovisual_individual", "FIAF", "Finlândia", "https://www.kavi.fi"),
    ("fiaf-ecpad", "ECPAD - Établissement de communication et de production audiovisuelle de la Défense", "arquivo_audiovisual_individual", "FIAF", "França", "https://www.ecpad.fr"),
    ("fiaf-dovzhenko-centre", "Oleksandr Dovzhenko National Centre", "arquivo_audiovisual_individual", "FIAF", "Ucrânia", "https://dovzhenkocentre.org"),
    ("cinematheque-suisse", "Cinémathèque suisse", "arquivo_audiovisual_individual", "FIAF", "Suíça", "https://www.cinematheque.ch"),
    ("fiaf-cinemateca-portuguesa", "Cinemateca Portuguesa / Museu do Cinema", "arquivo_audiovisual_individual", "FIAF", "Portugal", "https://www.cinemateca.pt"),
    ("fiaf-slovenian-film-archive", "Arhiv Republike Slovenije - Slovenski Filmski Arhiv", "arquivo_audiovisual_individual", "FIAF", "Eslovênia", "https://www.arhiv.gov.si"),
    ("fiaf-slovenian-cinematheque", "Slovenian Cinematheque / Slovenska Kinoteka", "arquivo_audiovisual_individual", "FIAF", "Eslovênia", "https://www.kinoteka.si"),
    ("fiaf-bfi-national-archive", "BFI National Archive", "arquivo_audiovisual_individual", "FIAF", "Reino Unido", "https://www.bfi.org.uk"),
    ("fiaf-imperial-war-museums-film-archive", "Imperial War Museums - Film Archive", "arquivo_audiovisual_individual", "FIAF", "Reino Unido", "https://film.iwmcollections.org.uk"),
    ("fiaf-cinematheque-luxembourg", "Cinémathèque de la Ville de Luxembourg", "arquivo_audiovisual_individual", "FIAF", "Luxemburgo", "https://www.cinematheque.lu"),
    ("fiaf-filmoteca-espanola", "Filmoteca Española", "arquivo_audiovisual_individual", "FIAF", "Espanha", "https://www.cultura.gob.es"),
    ("fiaf-north-west-film-archive", "North West Film Archive", "arquivo_audiovisual_individual", "FIAF", "Reino Unido", "https://www.mmu.ac.uk"),
    ("fiaf-cineteca-italiana", "Fondazione Cineteca Italiana", "arquivo_audiovisual_individual", "FIAF", "Itália", "https://www.cinetecamilano.it"),
    ("fiaf-gosfilmofond", "Gosfilmofond of Russia", "arquivo_audiovisual_individual", "FIAF", "Rússia", "https://gosfilmofond.ru"),
    ("fiaf-filmmuseum-munchen", "Filmmuseum München", "arquivo_audiovisual_individual", "FIAF", "Alemanha", "https://www.muenchner-stadtmuseum.de"),
    ("fiaf-national-library-norway", "The National Library of Norway - Film and Broadcasting", "arquivo_audiovisual_individual", "FIAF", "Noruega", "https://www.nb.no"),
    ("fiaf-cinematheque-francaise", "Cinémathèque française / Musée du cinéma", "arquivo_audiovisual_individual", "FIAF", "França", "https://www.cinematheque.fr"),
    ("fiaf-cnc-aff", "Centre national du cinéma et de l'image animée - Direction du patrimoine cinématographique", "arquivo_audiovisual_individual", "FIAF", "França", "https://www.cnc-aff.fr"),
    ("fiaf-narodni-filmovy-archiv", "Národní filmový archiv", "arquivo_audiovisual_individual", "FIAF", "República Tcheca", "https://nfa.cz"),
    ("fiaf-kvikmyndasafn-islands", "Kvikmyndasafn Islands / National Film Archive of Iceland", "arquivo_audiovisual_individual", "FIAF", "Islândia", "https://www.kvikmyndasafn.is"),
    ("fiaf-csc-cineteca-nazionale", "Fondazione Centro Sperimentale di Cinematografia - Cineteca Nazionale", "arquivo_audiovisual_individual", "FIAF", "Itália", "https://www.fondazionecsc.it"),
    ("fiaf-filmoteca-vasca", "Euskadiko Filmategia Fundazioa / Fundación Filmoteca Vasca", "arquivo_audiovisual_individual", "FIAF", "País Basco / Espanha", "https://www.filmoteka.eus"),
    ("fiaf-kinoteka-north-macedonia", "Kinoteka na Republika Severna Makedonija / Cinematheque of Republic of North Macedonia", "arquivo_audiovisual_individual", "FIAF", "Macedônia do Norte", "https://kinoteka.mk"),
    ("fiaf-bulgarian-national-film-archive", "Bulgarska Nacionalna Filmoteka", "arquivo_audiovisual_individual", "FIAF", "Bulgária", "https://bnf.bg"),
    ("fiaf-swedish-film-institute", "Svenska Filminstitutet", "arquivo_audiovisual_individual", "FIAF", "Suécia", "https://www.filminstitutet.se"),
    ("fiaf-estonian-film-archive", "Film Archive of the National Archives of Estonia", "arquivo_audiovisual_individual", "FIAF", "Estônia", "https://www.ra.ee"),
    ("fiaf-albanian-national-film-archive", "Arkivi Qendror Shtetëror i Filmit / The Albanian National Film Archive", "arquivo_audiovisual_individual", "FIAF", "Albânia", "https://www.aqshf.gov.al"),
    ("fiaf-cinematheque-toulouse", "La Cinémathèque de Toulouse", "arquivo_audiovisual_individual", "FIAF", "França", "https://www.lacinemathequedetoulouse.com"),
    ("fiaf-museo-nazionale-cinema", "Museo Nazionale del Cinema - Fondazione Maria Adriana Prolo", "arquivo_audiovisual_individual", "FIAF", "Itália", "https://www.museocinema.it"),
    ("fiaf-filmoteca-valenciana", "Filmoteca Valenciana - Institut Valencià de Cultura", "arquivo_audiovisual_individual", "FIAF", "Valência / Espanha", "https://ivc.gva.es"),
    ("fiaf-filmoteca-vaticana", "Filmoteca Vaticana", "arquivo_audiovisual_individual", "FIAF", "Vaticano", "https://www.vaticanstate.va"),
    ("fiaf-filmarchiv-austria", "Filmarchiv Austria", "arquivo_audiovisual_individual", "FIAF", "Áustria", "https://www.filmarchiv.at"),
    ("fiaf-austrian-film-museum", "Österreichisches Filmmuseum / Austrian Film Museum", "arquivo_audiovisual_individual", "FIAF", "Áustria", "https://www.filmmuseum.at"),
    ("fiaf-fina", "Filmoteka Narodowa - Instytut Audiowizualny (FINA)", "arquivo_audiovisual_individual", "FIAF", "Polônia", "https://www.fn.org.pl"),
    ("fiaf-croatian-cinematheque", "Hrvatski Državni Arhiv - Hrvatska Kinoteka / Croatian State Archive - Croatian Cinematheque", "arquivo_audiovisual_individual", "FIAF", "Croácia", "https://www.arhiv.hr"),
    ("euscreen-orf", "Österreichischer Rundfunk", "instituicao_audiovisual_europeia", "EUscreen", "Áustria", "https://euscreen.eu/full-members/"),
    ("euscreen-cna", "Centre national de l'audiovisuel (CNA)", "instituicao_audiovisual_europeia", "EUscreen", "Luxemburgo", "https://euscreen.eu/full-members/"),
    ("euscreen-ccma", "Corporació Catalana de Mitjans Audiovisuals (CCMA)", "instituicao_audiovisual_europeia", "EUscreen", "Catalunha / Espanha", "https://euscreen.eu/full-members/"),
    ("euscreen-czech-television", "Czech Television", "instituicao_audiovisual_europeia", "EUscreen", "República Tcheca", "https://euscreen.eu/full-members/"),
    ("euscreen-ert", "ERT", "instituicao_audiovisual_europeia", "EUscreen", "Grécia", "https://euscreen.eu/full-members/"),
    ("ina", "Institut national de l'audiovisuel", "instituicao_audiovisual_europeia", "EUscreen", "França", "https://euscreen.eu/full-members/"),
    ("euscreen-istituto-luce-cinecitta", "Istituto Luce Cinecittà", "instituicao_audiovisual_europeia", "EUscreen", "Itália", "https://euscreen.eu/full-members/"),
    ("euscreen-learning-on-screen", "Learning on Screen", "instituicao_audiovisual_europeia", "EUscreen", "Reino Unido", "https://euscreen.eu/full-members/"),
    ("euscreen-lcva", "Lithuanian Central State Archive (LCVA)", "instituicao_audiovisual_europeia", "EUscreen", "Lituânia", "https://euscreen.eu/full-members/"),
    ("euscreen-national-archives-latvia", "National Archives of Latvia", "instituicao_audiovisual_europeia", "EUscreen", "Letônia", "https://euscreen.eu/full-members/"),
    ("euscreen-sound-vision", "Netherlands Institute for Sound & Vision", "instituicao_audiovisual_europeia", "EUscreen", "Países Baixos", "https://euscreen.eu/full-members/"),
    ("euscreen-northern-ireland-screen-dfa", "Northern Ireland Screen DFA", "instituicao_audiovisual_europeia", "EUscreen", "Irlanda do Norte / Reino Unido", "https://euscreen.eu/full-members/"),
    ("euscreen-noterik", "Noterik", "instituicao_audiovisual_europeia", "EUscreen", "Países Baixos", "https://euscreen.eu/full-members/"),
    ("euscreen-queens-university-belfast", "Queen's University Belfast", "instituicao_audiovisual_europeia", "EUscreen", "Irlanda do Norte / Reino Unido", "https://euscreen.eu/full-members/"),
    ("euscreen-universite-luxembourg", "Université du Luxembourg", "instituicao_audiovisual_europeia", "EUscreen", "Luxemburgo", "https://euscreen.eu/full-members/"),
    ("euscreen-utrecht-university", "Utrecht University", "instituicao_audiovisual_europeia", "EUscreen", "Países Baixos", "https://euscreen.eu/full-members/"),
]

EUROPEAN_COMPLEMENTARY_ARCHIVE_ROWS = [
    ("efg-aamod", "Archivio Audiovisivo del movimento operaio e democratico", "arquivo_audiovisual_individual", "EFG", "Itália", "https://www.europeanfilmgateway.eu/search-efg/AAMOD"),
    ("efg-arxiu-mallorca", "Arxiu del So i de la Imatge de Mallorca", "arquivo_audiovisual_individual", "EFG", "Mallorca / Espanha", "https://www.europeanfilmgateway.eu/search-efg/Arxiu%20del%20So%20i%20de%20la%20Imatge%20de%20Mallorca"),
    ("efg-crnogorska-kinoteka", "Crnogorska Kinoteka", "arquivo_audiovisual_individual", "EFG", "Montenegro", "https://www.europeanfilmgateway.eu/search-efg/Crnogorska%20Kinoteka"),
    ("efg-deutsches-historisches-museum", "Deutsches Historisches Museum", "arquivo_audiovisual_individual", "EFG", "Alemanha", "https://www.dhm.de"),
    ("efg-friedrich-wilhelm-murnau-stiftung", "Friedrich-Wilhelm-Murnau-Stiftung", "arquivo_audiovisual_individual", "EFG", "Alemanha", "https://www.murnau-stiftung.de"),
    ("efg-landesfilmsammlung-baden-wurttemberg", "Landesfilmsammlung Baden-Württemberg", "arquivo_audiovisual_individual", "EFG", "Baden-Württemberg / Alemanha", "https://www.europeanfilmgateway.eu/search-efg/landesfilmsammlung%20lbw"),
    ("inedits-ad-libitum", "Ad Libitum Workshop", "arquivo_audiovisual_individual", "INEDITS", "França", "http://www.adlibitum.saintmarcellin-vercors-isere.fr"),
    ("inedits-archipop", "ARCHIPOP", "arquivo_audiovisual_individual", "INEDITS", "França", "https://archipop.org"),
    ("inedits-audiovisual-institute-monaco", "Audiovisual Institute of Monaco", "arquivo_audiovisual_individual", "INEDITS", "Mônaco", "https://institut-audiovisuel.mc"),
    ("inedits-autrefois-geneve", "Autrefois Genève Foundation", "arquivo_audiovisual_individual", "INEDITS", "Suíça", "https://www.autrefoisgeneve.ch/"),
    ("inedits-ciclic-centre-val-de-loire", "CICLIC - Centre-Val-de-Loire", "arquivo_audiovisual_individual", "INEDITS", "França", "http://www.ciclic.fr/"),
    ("inedits-cine-archives", "Ciné-Archives", "arquivo_audiovisual_individual", "INEDITS", "França", "http://www.cinearchives.org/"),
    ("inedits-cineam", "CINÉAM", "arquivo_audiovisual_individual", "INEDITS", "França", "http://www.cineam.asso.fr/"),
    ("inedits-cinematheque-bretagne", "Cinémathèque de Bretagne", "arquivo_audiovisual_individual", "INEDITS", "Bretanha / França", "https://www.cinematheque-bretagne.bzh"),
    ("inedits-cinematheque-corse", "Cinémathèque de Corse", "arquivo_audiovisual_individual", "INEDITS", "Córsega / França", "https://casadilume.corse.fr/"),
    ("inedits-cinematheque-nouvelle-aquitaine", "Cinémathèque de Nouvelle-Aquitaine", "arquivo_audiovisual_individual", "INEDITS", "Nova Aquitânia / França", "https://cdna.memoirefilmiquenouvelleaquitaine.fr/presentation"),
    ("inedits-cinematheque-pays-savoie-ain", "Cinémathèque des Pays de Savoie et de l'Ain", "arquivo_audiovisual_individual", "INEDITS", "Saboia e Ain / França", "https://www.letelepherique.org/"),
    ("inedits-cinematheque-saint-etienne", "Cinémathèque of Saint-Etienne", "arquivo_audiovisual_individual", "INEDITS", "França", "https://cinematheque.saint-etienne.fr"),
    ("inedits-cinememoire", "Cinémémoire", "arquivo_audiovisual_individual", "INEDITS", "Provence / França", "https://cinememoire.net/"),
    ("inedits-county-archives-puy-de-dome", "County Archives of Puy-de-Dôme", "arquivo_audiovisual_individual", "INEDITS", "Puy-de-Dôme / França", "https://inedits.eu/en/inedits_content/the-archives-et-cinema-programme/"),
    ("inedits-cinematheque-monts-jura", "La Cinémathèque des Monts Jura", "arquivo_audiovisual_individual", "INEDITS", "Jura / França", "https://cinematheque-des-monts-jura.jimdosite.com/"),
    ("inedits-far", "Fond Audiovisuel de Recherche", "arquivo_audiovisual_individual", "INEDITS", "Charente-Maritime / França", "http://www.far-asso.fr/"),
    ("inedits-home-movies", "Fondazione Home Movies / Archivio Nazionale del film di Famiglia", "arquivo_audiovisual_individual", "INEDITS", "Itália", "https://homemovies.it/"),
    ("inedits-forum-des-images", "Forum des images", "arquivo_audiovisual_individual", "INEDITS", "Paris / França", "http://www.forumdesimages.fr/"),
    ("inedits-image-est", "Image'Est", "arquivo_audiovisual_individual", "INEDITS", "Grand Est / França", "http://www.image-est.fr/"),
    ("inedits-jean-vigo-institute", "Jean Vigo Institute", "arquivo_audiovisual_individual", "INEDITS", "França", "https://www.inst-jeanvigo.eu/"),
    ("inedits-manche-regional-archives", "Manche Regional Archives", "arquivo_audiovisual_individual", "INEDITS", "Manche / França", "https://www.archives-manche.fr/"),
    ("inedits-mira", "MIRA", "arquivo_audiovisual_individual", "INEDITS", "Alsácia / França", "https://www.miralsace.eu/"),
    ("inedits-national-library-france-video", "National Library of France - Sound, Video and Multimedia Department", "arquivo_audiovisual_individual", "INEDITS", "França", "https://www.bnf.fr/fr/departement-son-video-multimedia"),
    ("inedits-prise-2", "Association Prise 2", "arquivo_audiovisual_individual", "INEDITS", "França", "https://associationprise2.wordpress.com/"),
    ("inedits-normandie-images", "Normandie Images", "arquivo_audiovisual_individual", "INEDITS", "Normandia / França", "https://www.memoirenormande.fr/"),
    ("inedits-peliskan", "Peliskan", "arquivo_audiovisual_individual", "INEDITS", "Bélgica", "https://inedits.eu/en/inedits_content/peliskan/"),
    ("inedits-simone-de-beauvoir", "Simone de Beauvoir Audiovisual Centre", "arquivo_audiovisual_individual", "INEDITS", "França", "https://www.centre-simone-de-beauvoir.com/"),
    ("inedits-valais-martigny-media-library", "Valais-Martigny Media Library", "arquivo_audiovisual_individual", "INEDITS", "Valais / Suíça", "https://www.mediatheque.ch/"),
]

EUROPEAN_BROADCAST_ARCHIVE_ROWS = [
    ("fiat-atresmedia", "Atresmedia", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Espanha", "https://www.atresmedia.com"),
    ("fiat-bbc", "BBC Archive", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Reino Unido", "https://www.bbc.co.uk/archive"),
    ("fiat-bulgarian-national-television", "Bulgarian National Television", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Bulgária", "https://bnt.bg"),
    ("fiat-cinecitta-archivio-luce", "Cinecittà - Archivio Luce", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Itália", "https://www.archivioluce.com"),
    ("fiat-dr", "DR", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Dinamarca", "https://www.dr.dk"),
    ("fiat-east-anglian-film-archive", "East Anglian Film Archive", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Reino Unido", "https://eafa.org.uk"),
    ("fiat-mediaset-mfe", "Mediaset - MediaForEurope", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Itália", "https://www.mfemediaforeurope.com"),
    ("fiat-meemoo", "meemoo", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Bélgica", "https://meemoo.be"),
    ("fiat-rtp", "Rádio e Televisão de Portugal - Arquivos RTP", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Portugal", "https://arquivos.rtp.pt"),
    ("fiat-rte", "Raidío Teilifís Éireann / RTÉ Archives", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Irlanda", "https://www.rte.ie/archives/"),
    ("fiat-rtve", "Radio Televisión Española / RTVE Archivo", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Espanha", "https://www.rtve.es/archivo/"),
    ("fiat-rai-teche", "Rai Teche", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Itália", "https://www.teche.rai.it"),
    ("fiat-rtv-slovenia", "Radiotelevizija Slovenija", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Eslovênia", "https://www.rtvslo.si"),
    ("fiat-rts", "Radio Televizija Srbije / TV Arhiv", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Sérvia", "https://tvarhiv.rts.rs"),
    ("fiat-rtv-vojvodina", "Radio Television de Vojvodina", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Sérvia", "https://www.rtv.rs"),
    ("fiat-rmc-bfm", "RMC BFM / BFM Video", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "França", "https://bfmvideo.fr"),
    ("fiat-rtvs", "Radio and Television Slovakia", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Eslováquia", "https://www.stvr.sk"),
    ("fiat-rtsh", "Radio Televizioni Shqiptar", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Albânia", "https://rtsh.al"),
    ("fiat-reuters-screenocean", "Reuters / Screenocean", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Reino Unido", "https://www.screenocean.com"),
    ("fiat-ruv", "RÚV", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Islândia", "https://www.ruv.is"),
    ("fiat-s4c", "S4C", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "País de Gales / Reino Unido", "https://www.s4c.cymru"),
    ("fiat-srg-ssr", "SRG SSR", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Suíça", "https://www.srgssr.ch"),
    ("fiat-swr", "Südwestrundfunk / SWR", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Alemanha", "https://www.swr.de"),
    ("fiat-suspilne", "Suspilne Ukraine / Mediateka", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Ucrânia", "https://mediateka.suspilne.media"),
    ("fiat-svt", "Sveriges Television / SVT", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Suécia", "https://www.svt.se"),
    ("fiat-tg4", "TG4", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Irlanda", "https://www.tg4.ie"),
    ("fiat-trt", "Turkish Radio and Television Corporation", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Turquia / Europa", "https://www.trt.net.tr"),
    ("fiat-tvr", "TVR", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Romênia", "https://www.tvr.ro"),
    ("fiat-vrt", "VRT", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Bélgica", "https://www.vrt.be"),
    ("fiat-yle", "Yleisradio Oy / Yle", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Finlândia", "https://yle.fi"),
    ("fiat-sportcast", "Sportcast", "instituicao_televisiva_com_acervo_audiovisual", "FIAT/IFTA", "Alemanha", "https://www.sportcast.de"),
    ("fiat-european-commission-av-service", "European Commission Audiovisual Service", "instituicao_audiovisual_europeia", "FIAT/IFTA", "União Europeia", "https://audiovisual.ec.europa.eu"),
]


def _active_european_code_aliases():
    aliases = {
        "archives-portal-europe": "ape",
        "efg-aamod": "aamod",
        "efg-arxiu-mallorca": "asim",
        "efg-crnogorska-kinoteka": "crnogorska-kinoteka",
        "efg-deutsches-historisches-museum": "dhm",
        "fiaf-ecpad": "ecpad",
        "fiaf-deutsche-kinemathek": "deutsche-kinemathek",
        "fiaf-dff": "dff",
        "fiaf-eye-filmmuseum": "eye",
        "fiaf-estonian-film-archive": "estonian_film_archive",
        "fiaf-fina": "fina",
        "fiaf-filmarchiv-austria": "filmarchiv_austria",
        "fiaf-filmmuseum-dusseldorf": "filmmuseum_dusseldorf",
        "fiaf-filmoteca-catalunya": "filmoteca_catalunya",
        "fiaf-filmoteca-espanola": "filmoteca_espanola",
        "fiaf-filmoteca-valenciana": "filmoteca_valenciana",
        "fiat-dr": "dr",
        "fiat-east-anglian-film-archive": "eafa",
        "euscreen-ert": "ert",
        "fiaf-albanian-national-film-archive": "aqshf",
        "fiaf-bfi-national-archive": "bfi",
        "fiaf-bundesarchiv": "barch",
        "fiaf-cinemateca-romana": "anf",
        "fiaf-cinemateca-portuguesa": "cinemateca-portuguesa",
        "fiaf-filmoteca-vasca": "filmoteca-vasca",
        "fiaf-slovenian-film-archive": "sfa",
        "fiat-bbc": "bbc",
        "fiat-cinecitta-archivio-luce": "luce",
        "fiaf-bulgarian-national-film-archive": "bnfa",
        "fiat-bulgarian-national-television": "bnt",
        "euscreen-ccma": "ccma",
        "euscreen-czech-television": "czech-television",
        "euscreen-istituto-luce-cinecitta": "luce",
        "inedits-audiovisual-institute-monaco": "iam",
        "inedits-autrefois-geneve": "autrefois",
        "inedits-archipop": "archipop",
        "inedits-ciclic-centre-val-de-loire": "ciclic",
        "inedits-cineam": "cineam",
        "inedits-cinememoire": "cinememoire",
        "inedits-cine-archives": "cinearchives",
        "inedits-cinematheque-bretagne": "cinematheque-bretagne",
        "fiaf-cinematheque-francaise": "cinematheque-francaise",
        "fiaf-cinematek": "cinematek",
        "fiaf-csc-cineteca-nazionale": "csc-cineteca-nazionale",
        "inedits-cinematheque-nouvelle-aquitaine": "cdna",
        "inedits-cinematheque-pays-savoie-ain": "cpsa",
        "inedits-cinematheque-saint-etienne": "saint-etienne",
        "inedits-far": "far",
        "inedits-home-movies": "home-movies-memoryscapes",
        "euscreen-cna": "cna",
        "fiaf-cnc-aff": "cnc-aff",
        "the-european-film-gateway": "european-film-gateway",
    }
    for code in CORPORA:
        aliases[code] = code
    return aliases


def _is_european_corpus(corpus_def):
    coverage = str(corpus_def.get("coverage_level", "")).lower()
    return (
        corpus_def["code"] in {"ape", "euscreen", "european-film-gateway", "europeana", "pares", "portal-portugues-arquivos", "ina"}
        or "europe" in coverage
        or "europeu" in coverage
    )


def _base_row(**row):
    return {
        "relationship_to_current_corpus": row.get("relationship_to_current_corpus", ""),
        "organism_status": row.get("organism_status", ""),
        "queue_layer": row.get("queue_layer", ""),
        "queue_decision": row.get("queue_decision", ""),
        "queue_priority": row.get("queue_priority", 99),
        "definitive_queue_rank": row.get("definitive_queue_rank", ""),
        "queue_reason": row.get("queue_reason", ""),
        "next_action": row.get("next_action", ""),
        "inclusion_gate": row.get("inclusion_gate", ""),
        "video_location_status": row.get("video_location_status", ""),
        "video_location_candidate_url": row.get("video_location_candidate_url", row.get("source_url", "")),
        "video_location_strategy": row.get("video_location_strategy", ""),
        "blocks_expansion": row.get("blocks_expansion", False),
        "rule_version": EUROPE_RESEARCH_RULE_VERSION,
        **row,
    }


def _classify_research_row(row):
    code = row["unit_code"]
    active_aliases = _active_european_code_aliases()
    active_code = active_aliases.get(code, code)
    unit_type = row["unit_type"]
    country_or_scope = str(row.get("country_or_scope", ""))

    if active_code in CORPORA and CORPORA[active_code].get("organism_active", False):
        return {
            "relationship_to_current_corpus": "já incorporado ao organismo",
            "organism_status": "ativo",
            "queue_layer": "corpus_ativo",
            "queue_decision": "monitoramento_mensal",
            "queue_priority": 90,
            "queue_reason": "A unidade já opera como corpus ativo ou está representada por corpus ativo equivalente.",
            "next_action": CORPORA[active_code]["check_script"],
            "inclusion_gate": "já incorporado ao organismo",
            "video_location_status": "mapeado_no_corpus",
            "video_location_candidate_url": CORPORA[active_code].get("source_url", ""),
            "video_location_strategy": "acompanhar saídas analíticas do corpus ativo",
            "blocks_expansion": False,
        }

    if code == "fiat-east-anglian-film-archive":
        return {
            "relationship_to_current_corpus": "rota pública validada fora do corpus ativo",
            "organism_status": "protocolado",
            "queue_layer": "protocolo_de_coleta_pendente",
            "queue_decision": "aguardar_nova_janela_de_coleta_sem_waf",
            "queue_priority": 12,
            "queue_reason": (
                "O catálogo oficial EAFA expõe busca pública `hasVideo=on`; a rota anunciou 1.627 fichas "
                "em 136 páginas e uma rodada inicial confirmou 1.625 players, mas a reexecução final ativou "
                "AWS WAF CAPTCHA. A unidade não deve entrar como corpus ativo com saída zero."
            ),
            "next_action": "reexecutar `python scripts/run_eafa_pipeline.py` após liberação do WAF e validar com `python scripts/check_eafa_outputs.py`",
            "inclusion_gate": "persistir rodada completa com links de vídeo e catálogo analítico não vazios",
            "video_location_status": "rota_validada_bloqueio_temporario_waf",
            "video_location_candidate_url": "https://eafa.org.uk/search/?hasVideo=on",
            "video_location_strategy": (
                "respeitar WAF/CAPTCHA, não contornar barreiras de verificação humana e repetir a coleta "
                "com baixa concorrência/retries até materializar fichas públicas com player"
            ),
            "blocks_expansion": False,
        }

    if code == "fiat-european-commission-av-service":
        return {
            "relationship_to_current_corpus": "rota pública validada fora do corpus ativo",
            "organism_status": "protocolado",
            "queue_layer": "protocolo_de_incorporacao_em_escala",
            "queue_decision": "planejar_ingestao_incremental_antes_de_ativar",
            "queue_priority": 12,
            "queue_reason": (
                "O European Commission Audiovisual Service expõe API pública com mais de 177 mil "
                "registros `VIDEO`; o detalhe `media?reference=` materializa HLS, DASH, MP4, "
                "miniaturas, legendas, duração, temas, instituições e direitos. A unidade não deve "
                "entrar como corpus ativo por amostra arbitrária: a incorporação exige estratégia "
                "incremental ou particionada."
            ),
            "next_action": "definir_estrategia_incremental_e_criar_corpus_ec_av_service",
            "inclusion_gate": (
                "persistir corpus audiovisual completo por janela, ano ou shard sem inflar o snapshot "
                "público e validar saídas não vazias"
            ),
            "video_location_status": "api_publica_validada_ingestao_em_escala_pendente",
            "video_location_candidate_url": (
                "https://8hwk2cyeyb.execute-api.eu-west-1.amazonaws.com/parrotfish-prod/search"
                "?mediaType=VIDEO&offset=1&limit=12"
            ),
            "video_location_strategy": (
                "usar apenas `mediaType=VIDEO`; coletar referências pela busca oficial e enriquecer cada "
                "item pelo endpoint público `media?reference=...`, preservando metadados de acesso e direitos"
            ),
            "blocks_expansion": False,
        }

    if code == "cinematheque-suisse":
        return {
            "relationship_to_current_corpus": "identificada fora do corpus ativo",
            "organism_status": "protocolado",
            "queue_layer": "protocolo_de_nao_incorporacao",
            "queue_decision": "manter_protocolo_sem_incorporacao",
            "queue_priority": 80,
            "queue_reason": (
                "A rota Memobase materializa metadados públicos `Film`, mas não disponibiliza vídeo "
                "público incorporável; a mídia é indicada como local/autorizada."
            ),
            "next_action": "monitorar_se_memobase_ou_site_institucional_passam_a_expor_video_publico",
            "inclusion_gate": "não incorporar até existir rota pública de vídeo ou streaming incorporável",
            "video_location_status": "metadados_publicos_midia_restrita",
            "video_location_candidate_url": CORPORA[code].get("source_url", ""),
            "video_location_strategy": "retestar Memobase, catálogo institucional e eventuais players públicos sem contornar restrições",
            "blocks_expansion": False,
        }

    if code == "fiaf-cineteca-italiana":
        return {
            "relationship_to_current_corpus": "arquivo confirmado com streaming protegido e canais públicos contextuais",
            "organism_status": "protocolado",
            "queue_layer": "protocolo_de_nao_incorporacao",
            "queue_decision": "manter_protocolo_sem_incorporacao",
            "queue_priority": 80,
            "queue_reason": (
                "A Fondazione Cineteca Italiana tem acervo fílmico confirmado, mas as rotas públicas observadas "
                "são programação de sala, streaming protegido por conta/compra/senha, visita presencial, plataforma "
                "educativa com registro e canal institucional recente. Não há catálogo público de vídeos de acervo "
                "coletável nesta rodada."
            ),
            "next_action": "retestar_site_oficial_streaming_youtube_vimeo_e_eventual_catalogo_publico_de_acervo",
            "inclusion_gate": (
                "só incorporar após validar catálogo público de vídeos de acervo ou recorte institucional assumido "
                "explicitamente como canal público separado"
            ),
            "video_location_status": "streaming_protegido_canal_publico_nao_catalografico",
            "video_location_candidate_url": (
                "https://www.cinetecamilano.it/streaming/; "
                "https://www.youtube.com/feeds/videos.xml?channel_id=UCazdgK2z2EdkCqnVMtFpelA"
            ),
            "video_location_strategy": (
                "não usar programação de sala como corpus; não contornar senha, conta ou compra; monitorar canal "
                "público apenas como recorte institucional se o projeto criar essa categoria"
            ),
            "blocks_expansion": False,
        }

    if code == "fiaf-cineteca-bologna":
        return {
            "relationship_to_current_corpus": "arquivo confirmado com catálogo público extenso e ingestão total pendente",
            "organism_status": "protocolado",
            "queue_layer": "protocolo_de_incorporacao_pendente",
            "queue_decision": "manter_protocolo_sem_incorporacao_ate_ingestao_total",
            "queue_priority": 80,
            "queue_reason": (
                "A Fondazione Cineteca di Bologna tem Archivio audiovisivi e Catalogo Film público. A rota AJAX "
                "foi validada, mas exige varredura extensa sem exportação pública integral ou REST aberto; a tentativa "
                "de coleta total excedeu a janela operacional do MVP. Não se incorpora amostra parcial."
            ),
            "next_action": "criar_ingestao_incremental_por_pagina_ou_solicitar_exportacao_publica_do_catalogo",
            "inclusion_gate": (
                "só incorporar após materializar o catálogo completo por rota reprodutível, sem misturar amostra "
                "técnica com corpus ativo"
            ),
            "video_location_status": "catalogo_publico_extenso_sem_ingestao_total_no_mvp",
            "video_location_candidate_url": (
                "https://cinetecadibologna.it/archivi/archivio/archivio-audiovisivi/catalogo-film/"
            ),
            "video_location_strategy": (
                "usar o endpoint AJAX oficial com paginação incremental, limites de requisição e retomada; "
                "validar fichas individuais e distinguir metadados públicos de mídia local/autorizada"
            ),
            "blocks_expansion": False,
        }

    if code in PROTOCOLLED_EUROPEAN_CODES:
        return {
            "relationship_to_current_corpus": "protocolado fora do corpus ativo",
            "organism_status": "protocolado",
            "queue_layer": "protocolo_de_negativa",
            "queue_decision": "manter_protocolo_sem_incorporacao",
            "queue_priority": 80,
            "queue_reason": "A unidade já tem negativa metodológica registrada por ausência de rota estável.",
            "next_action": "retestar_rota_em_ciclo_futuro",
            "inclusion_gate": "não incorporar até existir rota pública estável de coleta audiovisual",
            "video_location_status": "rota_nao_estavel",
            "video_location_strategy": "retestar busca pública, API, OAI-PMH, dump ou endpoint documentado",
            "blocks_expansion": False,
        }

    if code in DIRECTORY_EXPANSION_CODES:
        return {
            "relationship_to_current_corpus": "fonte para gerar fila de arquivos individuais",
            "organism_status": "fonte_de_expansao",
            "queue_layer": "fonte_de_fila",
            "queue_decision": "expandir_diretorio_para_fila_individual",
            "queue_priority": 1,
            "queue_reason": "A fonte ajuda a identificar arquivos audiovisuais europeus que podem ser avaliados um por um.",
            "next_action": "extrair_membros_e_criar_fila_de_instituicoes_audiovisuais",
            "inclusion_gate": "não entra como corpus; gera candidatos individuais verificáveis",
            "video_location_status": "nao_aplicavel_diretorio",
            "video_location_strategy": "extrair membros e localizar, em cada instituição, catálogo, página de acervo, player ou API",
            "blocks_expansion": False,
        }

    if code in DOCUMENTED_SWEEP_SOURCE_CODES:
        if code == "ace-members":
            return {
                "relationship_to_current_corpus": "fonte audiovisual documentada por rota pública parcial",
                "organism_status": "fonte_documentada",
                "queue_layer": "fonte_varrida_documentada",
                "queue_decision": "coberta_por_rotas_publicas_substitutas",
                "queue_priority": 6,
                "queue_reason": "ACE confirma 49 arquivos fílmicos europeus, mas a lista pública de contatos retornou acesso restrito; FIAF, EFG e INEDITS ficam como rotas públicas de expansão.",
                "next_action": "usar_fiaf_efg_inedits_e_sondagens_por_pais_para_localizar_membros_publicamente_verificaveis",
                "inclusion_gate": "não entra como corpus; serve como evidência de cobertura institucional e rota complementar",
                "video_location_status": "lista_publica_restrita",
                "video_location_strategy": "não inferir membros sem página pública; cruzar com diretórios abertos antes de implantar arquivos individuais",
                "blocks_expansion": False,
            }
        return {
            "relationship_to_current_corpus": "fonte contextual de varredura",
            "organism_status": "fonte_documentada",
            "queue_layer": "fonte_varrida_documentada",
            "queue_decision": "monitorar_sem_promover_emissoras_genericas_a_corpus",
            "queue_priority": 7,
            "queue_reason": "EBU lista emissoras públicas, mas emissora não equivale automaticamente a arquivo audiovisual público coletável.",
            "next_action": "usar_apenas_para_identificar_excecoes_com_arquivo_publico_validado",
            "inclusion_gate": "não incorporar sem página de arquivo, catálogo ou rota pública de vídeo",
            "video_location_status": "fonte_contextual",
            "video_location_strategy": "cruzar emissoras com FIAT/IFTA, EUscreen ou evidência própria de arquivo público antes de criar corpus",
            "blocks_expansion": False,
        }

    if unit_type in {
        "arquivo_audiovisual_individual",
        "instituicao_audiovisual_europeia",
        "instituicao_televisiva_com_acervo_audiovisual",
    }:
        return {
            "relationship_to_current_corpus": "candidato individual derivado de diretório especializado",
            "organism_status": "candidato_individual",
            "queue_layer": "fila_definitiva_um_por_um",
            "queue_decision": "avaliar_arquivo_individual_um_por_um",
            "queue_priority": 2,
            "queue_reason": (
                "Instituição audiovisual europeia identificada em diretório especializado; deve ser avaliada "
                "individualmente antes de entrar como corpus."
            ),
            "next_action": "sondar_site_catalogo_api_e_disponibilidade_audiovisual",
            "inclusion_gate": "só incorporar após validar rota pública de vídeos, metadados audiovisuais ou catálogo coletável",
            "video_location_status": "a_localizar",
            "video_location_strategy": "testar URL oficial, busca por vídeo/filme/televisão, sitemap, catálogo, endpoint e páginas incorporadas",
            "blocks_expansion": False,
        }

    if unit_type == "agregador_audiovisual":
        return {
            "relationship_to_current_corpus": "potencial complemento temático",
            "organism_status": "candidato",
            "queue_layer": "fila_definitiva_um_por_um",
            "queue_decision": "sondar_potencial_audiovisual",
            "queue_priority": 2,
            "queue_reason": "A unidade tem aderência audiovisual direta e deve ser testada antes de arquivos avulsos.",
            "next_action": "sondar_busca_api_ou_catalogo_publico",
            "inclusion_gate": "só incorporar após validar rota pública de vídeos, metadados audiovisuais ou catálogo coletável",
            "video_location_status": "a_localizar",
            "video_location_strategy": "testar busca pública, filtros de mídia, API, páginas de coleção e links para objetos digitais",
            "blocks_expansion": False,
        }

    if unit_type == "agregador_nacional_regional":
        is_country_already_represented = any(marker in country_or_scope for marker in ("Spain", "Portugal", "France"))
        return {
            "relationship_to_current_corpus": (
                "parcialmente coberto por corpus nacional/protocolo existente"
                if is_country_already_represented
                else "candidato nacional ou regional futuro"
            ),
            "organism_status": "candidato_futuro",
            "queue_layer": "radar_nacional_regional",
            "queue_decision": "avaliar_agregador_nacional_ou_regional",
            "queue_priority": 5 if not is_country_already_represented else 7,
            "queue_reason": "Agregador nacional/regional geral; entra após os recortes audiovisuais e diretórios especializados.",
            "next_action": "sondar_termos_audiovisuais_e_rota_de_coleta",
            "inclusion_gate": "só avançar se houver evidência pública de audiovisual com imagem em movimento",
            "video_location_status": "a_localizar",
            "video_location_strategy": "sondar termos audiovisuais e confirmar se há registros com links, mídia incorporada ou objetos digitais",
            "blocks_expansion": False,
        }

    return {
        "relationship_to_current_corpus": "fonte contextual ou temática indireta",
        "organism_status": "referencia",
        "queue_layer": "radar_contextual",
        "queue_decision": "monitorar_sem_pipeline_imediato",
        "queue_priority": 8,
        "queue_reason": "A unidade pode ajudar a pesquisa, mas não é prioridade de incorporação audiovisual no MVP.",
        "next_action": "manter_no_radar_e_reavaliar_por_evidencia_audiovisual",
        "inclusion_gate": "não incorporar sem evidência de acervo audiovisual coletável",
        "video_location_status": "sem_rota_prioritaria",
        "video_location_strategy": "reavaliar apenas se surgir evidência direta de catálogo audiovisual",
        "blocks_expansion": False,
    }


def _active_corpus_rows():
    rows = []
    for corpus_def in list_active_corpora(monthly_only=True):
        if not _is_european_corpus(corpus_def):
            continue
        category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
        rows.append(
            _base_row(
                unit_code=corpus_def["code"],
                unit_label=corpus_def["label"],
                unit_type="corpus_ativo",
                source_family=category_def["label"],
                country_or_scope=corpus_def["coverage_level"],
                territorial_scope=corpus_def["coverage_level"],
                source_url=corpus_def.get("source_url", ""),
                audiovisual_relevance=corpus_def.get("audiovisual_scope_note", ""),
                coverage_hint=corpus_def.get("methodological_unit", ""),
                evidence_reference="Corpus já materializado no organismo.",
                relationship_to_current_corpus="já incorporado ao organismo",
                organism_status="ativo",
                queue_layer="corpus_ativo",
                queue_decision="monitoramento_mensal",
                queue_priority=90,
                queue_reason="A unidade já opera como corpus ativo.",
                next_action=corpus_def["check_script"],
                inclusion_gate="já incorporado ao organismo",
                video_location_status="mapeado_no_corpus",
                video_location_candidate_url=corpus_def.get("source_url", ""),
                video_location_strategy="acompanhar saídas analíticas do corpus ativo",
            )
        )
    return rows


def _candidate_rows():
    rows = []
    active_codes = {row["unit_code"] for row in _active_corpus_rows()}
    active_aliases = _active_european_code_aliases()
    for raw_row in EUROPEANA_AGGREGATOR_ROWS:
        (
            unit_code,
            unit_label,
            unit_type,
            source_family,
            country_or_scope,
            territorial_scope,
            audiovisual_relevance,
            coverage_hint,
        ) = raw_row
        if active_aliases.get(unit_code, unit_code) in active_codes:
            continue
        row = {
            "unit_code": unit_code,
            "unit_label": unit_label,
            "unit_type": unit_type,
            "source_family": source_family,
            "country_or_scope": country_or_scope,
            "territorial_scope": territorial_scope,
            "source_url": EUROPEANA_AGGREGATORS_SOURCE_URL,
            "audiovisual_relevance": audiovisual_relevance,
            "coverage_hint": coverage_hint,
            "evidence_reference": "Lista oficial de agregadores da Europeana.",
        }
        rows.append(_base_row(**{**row, **_classify_research_row(row)}))

    for row in EUROPEAN_DIRECTORY_ROWS:
        rows.append(_base_row(**{**row, **_classify_research_row(row)}))

    for raw_row in [*EUROPEAN_INDIVIDUAL_ARCHIVE_ROWS, *EUROPEAN_COMPLEMENTARY_ARCHIVE_ROWS]:
        unit_code, unit_label, unit_type, source_family, country_or_scope, source_url = raw_row
        if active_aliases.get(unit_code, unit_code) in active_codes:
            continue
        if source_family == "FIAF":
            evidence_reference = "Lista oficial de membros da FIAF."
        elif source_family == "EUscreen":
            evidence_reference = "Página oficial de membros do EUscreen."
        elif source_family == "EFG":
            evidence_reference = "Página pública de contributing archives do European Film Gateway."
        elif source_family == "INEDITS":
            evidence_reference = "Página pública de membros da INEDITS - Amateur Films / Memory of Europe."
        else:
            evidence_reference = "Diretório especializado europeu com evidência audiovisual."
        row = {
            "unit_code": unit_code,
            "unit_label": unit_label,
            "unit_type": unit_type,
            "source_family": source_family,
            "country_or_scope": country_or_scope,
            "territorial_scope": country_or_scope,
            "source_url": source_url,
            "audiovisual_relevance": "arquivo, cinemateca, emissora, instituição de mídia ou acervo audiovisual",
            "coverage_hint": f"instituição individual identificada em diretório europeu especializado: {source_family}",
            "evidence_reference": evidence_reference,
        }
        rows.append(_base_row(**{**row, **_classify_research_row(row)}))

    for raw_row in EUROPEAN_BROADCAST_ARCHIVE_ROWS:
        unit_code, unit_label, unit_type, source_family, country_or_scope, source_url = raw_row
        if active_aliases.get(unit_code, unit_code) in active_codes:
            continue
        row = {
            "unit_code": unit_code,
            "unit_label": unit_label,
            "unit_type": unit_type,
            "source_family": source_family,
            "country_or_scope": country_or_scope,
            "territorial_scope": country_or_scope,
            "source_url": source_url,
            "audiovisual_relevance": "arquivo televisivo, emissora ou instituição de mídia com imagem em movimento",
            "coverage_hint": "instituição europeia identificada na lista pública de membros FIAT/IFTA",
            "evidence_reference": "Lista oficial de membros da FIAT/IFTA.",
        }
        rows.append(_base_row(**{**row, **_classify_research_row(row)}))

    for code in ("archives-hub", "francearchives"):
        row = {
            "unit_code": code,
            "unit_label": "Archives Hub" if code == "archives-hub" else "FranceArchives",
            "unit_type": "agregador_nacional_geral",
            "source_family": "protocolo europeu já materializado",
            "country_or_scope": "Reino Unido" if code == "archives-hub" else "França",
            "territorial_scope": "agregador nacional",
            "source_url": "https://archiveshub.jisc.ac.uk/" if code == "archives-hub" else "https://francearchives.gouv.fr/",
            "audiovisual_relevance": "fonte geral com potencial audiovisual",
            "coverage_hint": "agregador nacional protocolado fora do corpus ativo",
            "evidence_reference": "Protocolo leve já registrado no organismo.",
        }
        rows.append(_base_row(**{**row, **_classify_research_row(row)}))

    return rows


def build_europe_research_registry():
    registry_df = pd.DataFrame(
        [*_active_corpus_rows(), *_candidate_rows()],
        columns=EUROPE_RESEARCH_COLUMNS,
    )
    return (
        registry_df.drop_duplicates(subset=["unit_code"], keep="first")
        .sort_values(["queue_priority", "unit_label"])
        .reset_index(drop=True)
    )


def build_europe_research_queue(registry_df):
    if registry_df is None or registry_df.empty:
        return pd.DataFrame(columns=EUROPE_RESEARCH_COLUMNS)
    queue_df = (
        registry_df.loc[~registry_df["organism_status"].isin(["ativo", "protocolado"])]
        .sort_values(["queue_priority", "unit_label"])
        .reset_index(drop=True)
    )
    queue_df["definitive_queue_rank"] = range(1, len(queue_df) + 1)
    return queue_df


def build_europe_research_summary(registry_df):
    if registry_df is None or registry_df.empty:
        return pd.DataFrame(columns=EUROPE_RESEARCH_SUMMARY_COLUMNS)
    summary_df = (
        registry_df.groupby(["queue_layer", "unit_type", "queue_decision"], dropna=False)
        .size()
        .reset_index(name="total")
        .rename(columns={"queue_layer": "camada", "unit_type": "categoria", "queue_decision": "decisao"})
    )
    summary_df["rule_version"] = EUROPE_RESEARCH_RULE_VERSION
    return summary_df.sort_values(["camada", "categoria", "decisao"]).reset_index(drop=True)


def write_europe_research_outputs(output_dir: Path = OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_df = build_europe_research_registry()
    queue_df = build_europe_research_queue(registry_df)
    summary_df = build_europe_research_summary(registry_df)

    registry_df.to_csv(output_dir / EUROPE_RESEARCH_REGISTRY_FILENAME, index=False, encoding="utf-8-sig")
    queue_df.to_csv(output_dir / EUROPE_RESEARCH_QUEUE_FILENAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / EUROPE_RESEARCH_SUMMARY_FILENAME, index=False, encoding="utf-8-sig")
    return {
        "registry": registry_df,
        "queue": queue_df,
        "summary": summary_df,
    }


__all__ = [
    "EUROPE_RESEARCH_COLUMNS",
    "EUROPE_RESEARCH_QUEUE_FILENAME",
    "EUROPE_RESEARCH_REGISTRY_FILENAME",
    "EUROPE_RESEARCH_RULE_VERSION",
    "EUROPE_RESEARCH_SUMMARY_FILENAME",
    "build_europe_research_queue",
    "build_europe_research_registry",
    "build_europe_research_summary",
    "write_europe_research_outputs",
]
