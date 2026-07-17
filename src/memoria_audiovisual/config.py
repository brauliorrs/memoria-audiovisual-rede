from pathlib import Path


BASE_URL = "https://www.iasa-web.org"
START_URL = "https://www.iasa-web.org/category/links-categories/national-archives"
IASA_CCAAA_URL = "https://www.iasa-web.org/links/ccaaa"
CCAAA_HOME_URL = "https://www.ccaaa.org/"
CCAAA_MEMBERS_URL = "https://www.ccaaa.org/pages/who-we-are/list-of-current-members.html"
INA_HOME_URL = "https://www.ina.fr/"
INA_INSTITUTION_URL = "https://www.ina.fr/institut-national-audiovisuel"
INA_COLLECTIONS_URL = "https://www.ina.fr/institut-national-audiovisuel/collection-preservation-and-documentation-of-audiovisual-heritage"
INA_DATA_URL = "https://www.ina.fr/actualites-ina/data-donnees-visualisation-intelligence-artificielle-dataina"
INA_NEWS_URL = "https://www.ina.fr/actualites-ina"
INA_MEDIA_MAGAZINE_URL = "https://www.ina.fr/ina-eclaire-actu"
INA_MADELEN_URL = "https://madelen.ina.fr/"
INA_MEDIACLIP_URL = "https://mediaclip.ina.fr/"
EUSCREEN_HOME_URL = "https://euscreen.eu/"
EUSCREEN_ABOUT_URL = "https://euscreen.eu/about/"
EUSCREEN_COLLECTIONS_URL = "https://euscreen.eu/collections/"
EUSCREEN_EUROPEANA_URL = "https://euscreen.eu/europeana/"
EUSCREEN_COLLECTION_GRID_URL_TEMPLATE = "https://euscreen.eu/collection-grid-{index}/?btn={index}&gridcols=3"
EUSCREEN_ITEM_URL_TEMPLATE = "https://www.euscreen.eu/?page_id=388&item_id={item_id}"
EUROPEAN_FILM_GATEWAY_HOME_URL = "https://www.europeanfilmgateway.eu/"
EUROPEAN_FILM_GATEWAY_SEARCH_URL_TEMPLATE = "https://www.europeanfilmgateway.eu/search-efg?searchString={query}"
EUROPEANA_HOME_URL = "https://www.europeana.eu/"
EUROPEANA_SEARCH_URL_TEMPLATE = "https://www.europeana.eu/en/search?query={query}&media=true"
EUROPEANA_API_REFERENCE_URL = "https://pro.europeana.eu/page/apis"
PARES_HOME_URL = "https://pares.cultura.gob.es/"
PARES_SEARCH_URL_TEMPLATE = "https://pares.mcu.es/ParesBusquedas20/catalogo/find?nm=&texto={query}"
PPA_HOME_URL = "https://portal.arquivos.pt/"
PPA_SEARCH_URL_TEMPLATE = "https://portal.arquivos.pt/search?q={query}"
AAPB_HOME_URL = "https://americanarchive.org/"
AAPB_FAQ_URL = "https://americanarchive.org/faq"
AAPB_API_URL_TEMPLATE = "https://americanarchive.org/api.json?q={query}&rows={rows}"
ANF_OFFICIAL_URL = "http://www.anf-cinemateca.ro/"
ANF_EFG_PAGE_URL = "https://www.europeanfilmgateway.eu/content/arhiva-nationala-de-filme-bucarest"
ANF_EVENTBOOK_URL = "https://eventbook.ro/program/cinemateca-online"
AQSHF_HOME_URL = "https://aqshf.gov.al/"
AQSHF_MOTION_PICTURES_URL = "https://aqshf.gov.al/en/motion-pictures-listing/"
AQSHF_STATISTICS_URL = "https://aqshf.gov.al/en/statistics/"
AQSHF_WP_MOTION_PICTURE_API_URL = "https://aqshf.gov.al/wp-json/wp/v2/motion_picture"
IAM_HOME_URL = "https://institut-audiovisuel.mc/"
IAM_MEDIAS_URL = "https://institut-audiovisuel.mc/medias/"
IAM_MEDIAS_API_URL = "https://institut-audiovisuel.mc/wp-json/wp/v2/medias"
IAM_CONSULTATION_ROOM_URL = "https://institut-audiovisuel.mc/linstitut/les-espaces-publics/salle-de-consultation/"
AUTREFOIS_HOME_URL = "https://www.autrefoisgeneve.ch/"
AUTREFOIS_VIDEOS_API_URL = "https://www.autrefoisgeneve.ch/wp-json/wp/v2/aiovg_videos"
AUTREFOIS_TAGS_API_URL = "https://www.autrefoisgeneve.ch/wp-json/wp/v2/aiovg_tags"
AUTREFOIS_VIDEOS_SITEMAP_URL = "https://www.autrefoisgeneve.ch/aiovg_videos-sitemap.xml"
BBC_ARCHIVE_HOME_URL = "https://www.bbc.co.uk/archive"
BBC_ARCHIVE_TOPIC_URL = "https://www.bbc.co.uk/topics/c01yxyz46myt"
BBC_ARCHIVE_ACCESS_URL = "https://www.bbc.co.uk/archiveservices/archive-access-for-non-commercial-use"
BBC_ARCHIVE_SEARCH_URL = "https://archivesearch.tools.bbc.co.uk/"
BBC_ARCHIVE_SERVICES_URL = "https://archiveservices.tools.bbc.co.uk/"
BBC_ARCHIVE_REWIND_URL = "https://discover.bbcrewind.co.uk/"
BBC_ARCHIVE_DOWNLOADER_URL = "https://archive-downloader.bbcrewind.co.uk/"
BFI_NATIONAL_ARCHIVE_URL = "https://www.bfi.org.uk/bfi-national-archive"
BFI_ARCHIVE_SEARCH_URL = "https://www.bfi.org.uk/bfi-national-archive/search-bfi-archive"
BFI_ARCHIVE_FAQ_URL = "https://www.bfi.org.uk/bfi-national-archive/inside-archive/bfi-national-archive-faq"
BFI_RESEARCH_VIEWING_URL = "https://www.bfi.org.uk/bfi-national-archive/search-bfi-archive/research-viewing-service"
BFI_MEDIATHEQUE_URL = "https://www.bfi.org.uk/bfi-national-archive/watch-archive-collections/visit-us-view-archive-material/bfi-mediatheque"
BFI_REPLAY_HOME_URL = "https://replay.bfi.org.uk/"
BFI_REPLAY_ABOUT_URL = "https://replay.bfi.org.uk/about"
BFI_REPLAY_SEARCH_URL = "https://replay.bfi.org.uk/search"
BFI_REPLAY_COLLECTIONS_URL = "https://replay.bfi.org.uk/collections"
BFI_PLAYER_FREE_URL = "https://player.bfi.org.uk/free"
BNT_HOME_URL = "https://bnt.bg/"
BNT_SHOWS_URL = "https://bnt.bg/bnt1/shows"
BNT_ARCHIVE_AZ_URL = "https://bnt.bg/arhiv-a-ya-25cat.html"
BNT_FILM_ARCHIVE_URL = "https://bnt.bg/bg/a/filmov-arkhiv"
BNT_FILE_ARCHIVE_URL = "https://bnt.bg/bg/a/audiovizualno-nasledstvo-v-es"
BNT_LARGEST_AV_ARCHIVE_URL = "https://bnt.bg/bg/a/bnt-s-naj-golemiya-audio-vizualen-arhiv-v-ba-lgariya"
BNT_YOUTUBE_URL = "https://www.youtube.com/@BNT1"
BNFA_HOME_HTTPS_URL = "https://bnf.bg/"
BNFA_HOME_HTTP_URL = "http://bnf.bg/"
BNFA_FILM_LIBRARY_URL = "http://bnf.bg/en/film_library/"
BNFA_FILM_COLLECTION_URL = "http://bnf.bg/en/film_library/movie_fund/"
BNFA_E_CATALOGUE_EN_URL = "http://bnf.bg/en/archive/"
BNFA_E_CATALOGUE_BG_URL = "http://bnf.bg/bg/archive/"
BNFA_SEARCH_EN_URL = "http://bnf.bg/en/search/"
BNFA_EFG_PAGE_URL = "https://www.europeanfilmgateway.eu/about_efg/partners_contributors/bulgarian-national-film-archive"
BNFA_EFG_COLLECTION_URL = "https://www.europeanfilmgateway.eu/search-efg/bnfa"
CNCAFF_HOME_URL = "https://www.cnc.fr/a-propos-du-cnc/directions-et-services/direction-du-patrimoine-cinematographique"
CNCAFF_LEGACY_URL = "https://www.cnc-aff.fr"
CNCAFF_LISE_URL = "https://lise.cnc.fr"
CNCAFF_EFG_PAGE_URL = "https://www.europeanfilmgateway.eu/content/archives-fran%C3%A7aises-du-film-du-cnc-bois-darcy"
CNCAFF_EFG_SEARCH_URL = "https://www.europeanfilmgateway.eu/search-efg/Centre%20nationale%20du%20cin%C3%A9ma%20CNC"
BARCH_HOME_URL = "https://www.bundesarchiv.de/"
BARCH_FILMS_URL = "https://www.bundesarchiv.de/en/research-our-records/research-by-media-type/films/"
BARCH_SEARCH_SYSTEMS_URL = "https://www.bundesarchiv.de/en/research-our-records/research-archive-material/search-systems/"
BARCH_DIGITAL_READING_ROOM_INFO_URL = "https://www.bundesarchiv.de/en/research-our-records/research-archive-material/search-systems/digital-reading-room/"
BARCH_DIGITAL_READING_ROOM_URL = "https://digitaler-lesesaal.bundesarchiv.de/en"
BARCH_EFG_PAGE_URL = "https://www.europeanfilmgateway.eu/content/bundesarchiv-filmarchiv-berlin"
BARCH_EFG_COLLECTION_URL = "https://www.europeanfilmgateway.eu/search-efg/bundesarchiv"
ASIM_HOME_URL = "https://www.conselldemallorca.es/asim"
ASIM_VIDEO_FUNDS_URL = "https://www.conselldemallorca.es/fons-videografics"
ASIM_EFG_PAGE_URL = "https://www.europeanfilmgateway.eu/content/Arxiu%20del%20So%20i%20de%20la%20Imatge%20de%20Mallorca%20%28Palma%29"
ASIM_EFG_FILM_COLLECTION_URL = "https://www.europeanfilmgateway.eu/node/1848"
ASIM_EFG_SEARCH_URL = "https://www.europeanfilmgateway.eu/search-efg/Arxiu%20del%20So%20i%20de%20la%20Imatge%20de%20Mallorca"
CRNOGORSKA_KINOTEKA_HOME_URL = "https://kinoteka.me/"
CRNOGORSKA_KINOTEKA_EFG_CONTENT_URL = "https://www.europeanfilmgateway.eu/content/crnogorska-kinoteka-podgorica"
CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL = "https://www.europeanfilmgateway.eu/da/search-efg/ck%20crnogorska%20kinoteka"
CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL = (
    "https://europeanfilmgateway.eu/da/detail/"
    "Non%20%C3%A8%20resurrezione%20senza%20morte/ck%3A%3Ae7b8ca4b11b56d30c9d260216ffb18aa"
)
ARSENAL_HOME_URL = "https://www.arsenal-berlin.de/"
ARSENAL_ARCHIVE_DISTRIBUTION_URL = "https://www.arsenal-berlin.de/en/archive-distribution/"
ARSENAL_FILM_DATABASE_URL = "https://films.arsenal-berlin.de/Front/Index/lang/en_US"
ARSENAL_FILM_DATABASE_BROWSE_URL = "https://films.arsenal-berlin.de/Browse/Works"
CICLIC_HOME_URL = "https://ciclic.fr/"
CICLIC_MEMOIRE_HOME_URL = "https://memoire.ciclic.fr/"
CICLIC_FILMS_ARCHIVES_URL = "https://memoire.ciclic.fr/films-d-archives"
CICLIC_FILMS_AJAX_URL = "https://memoire.ciclic.fr/ssks/ajax/modspe/ciclic_memoire_liste_films"
CICLIC_WEB_MISSION_URL = "https://ciclic.fr/patrimoine/les-missions/diffuser-les-films-sur-le-web"
CINEAM_HOME_URL = "https://www.cineam.asso.fr/"
CINEAM_ABOUT_URL = "https://www.cineam.asso.fr/a-propos-897-0-0-0.html"
CINEAM_DEPOSIT_URL = "https://www.cineam.asso.fr/deposez-vos-films-898-0-0-0.html"
CINEAM_FILMS_URL = "https://www.cineam.asso.fr/exploration-905-0-0-0.html"
CINEAM_REALISATIONS_URL = "https://www.cineam.asso.fr/realisations-1094-0-0-0.html"
CINEMEMOIRE_HOME_URL = "https://cinememoire.net/"
CINEMEMOIRE_ARCHIVES_URL = "https://cinememoire.net/archives-cinememoire-ligne/archives-cinememoire-ligne"
CINEMEMOIRE_SEARCH_URL = "https://cinememoire.net/recherche-simple"
CCMA_HOME_URL = "https://www.3cat.cat/3cat/"
CCMA_CORPORATE_URL = "https://www.3cat.cat/corporatiu/ca/el-grup/"
CCMA_SEARCH_API_URL = "https://api.3cat.cat/cercador/tot"
CCMA_VIDEO_API_URL = "https://api.3cat.cat/videos"
CCMA_ARCHIVE_SALES_URL = "https://www.3cat.cat/venda-imatges/"
CZECH_TELEVISION_HOME_URL = "https://www.ceskatelevize.cz/"
CZECH_TELEVISION_IVYSILANI_URL = "https://www.ceskatelevize.cz/ivysilani/"
CZECH_TELEVISION_KULTURA_CATALOG_URL = "https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/"
CZECH_TELEVISION_DOKUMENTY_CATALOG_URL = "https://www.ceskatelevize.cz/ivysilani/kategorie/4003-dokumenty/katalog/"
CZECH_TELEVISION_HISTORIE_CATALOG_URL = "https://www.ceskatelevize.cz/ivysilani/kategorie/4079-historie/katalog/"
DFF_HOME_URL = "https://www.dff.film/en/"
DFF_FILM_ARCHIVE_URL = "https://www.dff.film/en/erkunden/archives/film-archive/"
DFF_FILMPORTAL_INFO_URL = "https://www.dff.film/en/erkunden/digital-international/filmportal-de/"
DFF_FILMPORTAL_VIDEOS_URL = "https://www.filmportal.de/videos"
DHM_HOME_URL = "https://www.dhm.de/"
DHM_ZEUGHAUSKINO_HOME_URL = "https://www.dhm.de/zeughauskino/en/"
DHM_FILM_ARCHIVE_URL = "https://www.dhm.de/zeughauskino/en/about-us/film-archive/"
DHM_ZEUGHAUSKINO_ONLINE_URL = "https://www.dhm.de/zeughauskino/en/programs/zeughauskino-online/"
DHM_MARSHALL_PLAN_URL = "https://www.dhm.de/zeughauskino/en/programs/zeughauskino-online/films-of-the-marshall-plan/"
DHM_EFG_PAGE_URL = "https://www.europeanfilmgateway.eu/node/1859"
ECPAD_HOME_URL = "https://www.ecpad.fr/"
ECPAD_ARCHIVES_HOME_URL = "https://archives.ecpad.fr/archives/archives"
ECPAD_ONLINE_ARCHIVES_URL = "https://archives.ecpad.fr/archives/consulter-les-archives-en-ligne"
ECPAD_SEARCH_API_URL = "https://archives.ecpad.fr/_recherche-api/search/2"
ECPAD_SEARCH_SIMPLE_API_URL = "https://archives.ecpad.fr/_recherche-api/search-simple/2"
ECPAD_SEARCH_MOTOR_URL = "https://archives.ecpad.fr/_recherche-api/moteur"
ERT_HOME_URL = "https://www.ert.gr/"
ERT_ARCHIVE_HOME_URL = "https://archive.ert.gr/"
ERT_COLLECTIONS_URL = "https://archive.ert.gr/arxikh1/sylloges/"
ERT_CONTACT_ACCESS_URL = "https://archive.ert.gr/epikinonia/"
ERT_WP_POSTS_API_URL = "https://archive.ert.gr/wp-json/wp/v2/posts"
EAFA_HOME_URL = "https://eafa.org.uk/"
EAFA_SEARCH_URL = "https://eafa.org.uk/search/"
EAFA_ACCESS_URL = "https://eafa.org.uk/access/"
EAFA_ABOUT_URL = "https://eafa.org.uk/about-us/"
EAFA_UEA_PAGE_URL = "https://www.uea.ac.uk/library/archives-and-special-collections/east-anglian-film-archive"
DEUTSCHE_KINEMATHEK_HOME_URL = "https://www.deutsche-kinemathek.de/en"
DEUTSCHE_KINEMATHEK_STREAMING_URL = "https://www.deutsche-kinemathek.de/en/online/streaming"
DEUTSCHE_KINEMATHEK_DIGITAL_COLLECTION_URL = "https://www.deutsche-kinemathek.de/en/online/digital-collection"
DEUTSCHE_KINEMATHEK_FILM_ARCHIVE_URL = "https://www.deutsche-kinemathek.de/en/research/archives/film-archive"
DEUTSCHE_KINEMATHEK_SEARCH_PORTAL_URL = "https://sammlungen.deutsche-kinemathek.de/recherche/"
DR_HOME_URL = "https://www.dr.dk/"
DR_DRTV_HOME_URL = "https://www.dr.dk/drtv/"
DR_GENSYN_URL = "https://www.dr.dk/drtv/gensyn"
DR_API_BASE_URL = "https://prod95-cdn.dr-massive.com/api"
CINEARCHIVES_HOME_URL = "https://www.cinearchives.org/"
CINEARCHIVES_CATALOG_URL = "https://www.cinearchives.org/catalogue-1104-0-0-0.html"
CINEARCHIVES_CATALOG_PAGE_URL_TEMPLATE = "https://www.cinearchives.org/catalogue-1104-0-0-{page}.html"
CINEMATHEQUE_BRETAGNE_HOME_URL = "https://www.cinematheque-bretagne.bzh/"
CINEMATHEQUE_BRETAGNE_FILMS_URL = "https://www.cinematheque-bretagne.bzh/voir-les-films-426-0-0-0.html"
CINEMATHEQUE_BRETAGNE_FILMS_PAGE_URL_TEMPLATE = (
    "https://www.cinematheque-bretagne.bzh/voir-les-films-426-0-0-{page}.html"
)
CINEMATHEQUE_FRANCAISE_HOME_URL = "https://www.cinematheque.fr/"
CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL = "https://www.cinematheque.fr/les-collections-de-la-cinematheque-francaise.html"
CINEMATHEQUE_FRANCAISE_HENRI_URL = "https://www.cinematheque.fr/henri/"
CINEMATEK_HOME_URL = "https://cinematek.be/en/"
CINEMATEK_FILM_COLLECTION_URL = "https://cinematek.be/en/collections/film"
CINEMATEK_BE_FILM_URL = "https://cinematek.be/en/collections/be-film"
EYE_HOME_URL = "https://www.eyefilm.nl/"
EYE_COLLECTION_RESEARCH_URL = "https://www.eyefilm.nl/en/collection/research"
EYE_FILM_DATABASE_URL = "https://filmdatabase.eyefilm.nl/en"
EYE_FILM_FRAGMENT_LIST_URL = (
    "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/all"
    "?f%5B0%5D=field_cm_media_filter%3Awith%20film%20fragment"
)
EYE_FILM_PLAYER_URL = "https://player.eyefilm.nl/"
ESTONIAN_FILM_ARCHIVE_HOME_URL = "https://www.ra.ee/"
ESTONIAN_FILM_ARCHIVE_FILM_PAGE_URL = "https://www.ra.ee/en/film-photo-audio/film/"
ARKAADER_HOME_URL = "https://arkaader.ee/"
ARKAADER_PROJECT_SLUG = "rHczO7kKnl"
ARKAADER_SEARCH_API_KEY = "0026558e-3439-4133-a1a3-1d43d689ef7d"
ARKAADER_FILM_SHELF_URL = f"{ARKAADER_HOME_URL}landing/br/{ARKAADER_PROJECT_SLUG}/pbOiQfMOLr"
ARKAADER_MOVIES_JSON_URL = (
    "https://vl-prod.s3.eu-north-1.amazonaws.com/visitor-data/p/"
    f"{ARKAADER_SEARCH_API_KEY}/en/movies.json"
)
ARKAADER_BROADCASTS_API_URL = f"{ARKAADER_HOME_URL}api/broadcasts"
CINEMATHEQUE_SUISSE_HOME_URL = "https://www.cinematheque.ch/"
CINEMATHEQUE_SUISSE_FILM_DEPARTMENT_URL = "https://www.cinematheque.ch/en/collections/film-department"
CINEMATHEQUE_SUISSE_MEMOBASE_INSTITUTION_URL = "https://api.memobase.ch/institution/csa?format=Json"
CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL = "https://api.memobase.ch/recordSet/csa-001?format=Json"
CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL = "https://api.memobase.ch/record/advancedSearch"
CPSA_HOME_URL = "https://www.letelepherique.org/"
CPSA_FILMS_URL = "https://www.letelepherique.org/le-catalogue-des-collections-527-0-0-0.html"
CPSA_FILMS_PAGE_URL_TEMPLATE = "https://www.letelepherique.org/le-catalogue-des-collections-527-0-0-{page}.html"
SAINT_ETIENNE_HOME_URL = "https://cinematheque.saint-etienne.fr/"
SAINT_ETIENNE_COLLECTIONS_URL = "https://cinematheque.saint-etienne.fr/Default/contenu-collections-test.aspx"
CINEMATECA_PT_HOME_URL = "https://www.cinemateca.pt/"
CINEMATECA_PT_COLLECTIONS_URL = "https://www.cinemateca.pt/colecoes/filme-e-video.aspx"
CINEMATECA_PT_ACCESS_URL = "https://www.cinemateca.pt/servicos/acesso-arquivo-filmico.aspx"
CINEMATECA_PT_DIGITAL_HOME_URL = "https://www.cinemateca.pt/cinemateca-digital.aspx"
CINEMATECA_PT_VIDEO_LIST_URL = "https://www.cinemateca.pt/cinemateca-digital/video.aspx"
CINEMATECA_PT_FELIX_URL = "https://felix.cinemateca.pt/"
FILMOTECA_VASCA_HOME_URL = "https://filmoteka.eus/"
FILMOTECA_VASCA_CATALOG_URL = "https://filmoteka.eus/es/coleccion/catalogo"
FILMOTECA_VASCA_MULTIMEDIA_URL = "https://filmoteka.eus/es/coleccion/multimedia"
CNA_HOME_URL = "https://cna.public.lu/en.html"
CNA_COLLECTIONS_URL = "https://cna.public.lu/fr/archives/lescollections.html"
CNA_ACCESS_URL = "https://cna.public.lu/en/archives/access.html"
CNA_ACCESS_FORM_URL = "https://cna.public.lu/en/archives/access/formulaire-acces.html"
CNA_SEARCH_URL = "https://cnasearch.public.lu/search/simple"
CNA_SEARCH_PROFILE_URL = "https://cnasearch.public.lu/searchprofiles/run/4/film"
CNA_RESULTS_URL = "https://cnasearch.public.lu/results"
CNA_RESULTS_NAV_URL_TEMPLATE = "https://cnasearch.public.lu/resultsnavigate/{page}"
LUCE_HOME_URL = "https://www.archivioluce.com/"
LUCE_CINECITTA_ARCHIVE_URL = "https://cinecitta.com/en/archivio-storico/"
LUCE_CINEMATIC_ARCHIVE_URL = "https://www.archivioluce.com/archivio-cinematografico/"
LUCE_CATALOG_HOME_URL = "https://patrimonio.archivioluce.com/luce-web/"
LUCE_CATALOG_FILMS_URL = (
    "https://patrimonio.archivioluce.com/luce-web/search/result.html?"
    "query=&jsonVal=%7B%22jsonVal%22%3A%7B%22startDate%22%3A%22%22%2C%22endDate%22%3A%22%22%2C"
    "%22fieldDate%22%3A%22dataNormal%22%2C%22_perPage%22%3A20%2C"
    "%22archiveType_string%22%3A%22%5C%22xDamsCineLuce%5C%22%22%7D%7D&activeFilter=archiveType_string"
)
LUCE_CATALOG_FILMS_PAGE_URL_TEMPLATE = (
    "https://patrimonio.archivioluce.com/luce-web/search/result.html?"
    "startPage={start}&query=&jsonVal=%7B%22jsonVal%22%3A%7B%22startDate%22%3A%22%22%2C"
    "%22endDate%22%3A%22%22%2C%22fieldDate%22%3A%22dataNormal%22%2C%22_perPage%22%3A20%2C"
    "%22archiveType_string%22%3A%22%5C%22xDamsCineLuce%5C%22%22%7D%7D&activeFilter=archiveType_string&perPage=20"
)
AAMOD_HOME_URL = "https://aamod.it/"
AAMOD_PATRIMONIO_URL = "https://aamod.it/patrimonio/"
AAMOD_FAQ_URL = "https://aamod.it/faq/"
AAMOD_WP_FILMS_URL = "https://aamod.it/wp-json/wp/v2/i-nostri-film?per_page=10"
AAMOD_ARCHIVI_ONLINE_URL = "http://patrimonio.aamod.it/aamod-web/"
AAMOD_FILMOTECA_OPAC_URL = "http://opac.aamod.xdams.net/aamod-web/film"
SFA_HOME_URL = "https://www.gov.si/drzavni-organi/organi-v-sestavi/arhiv/o-arhivu/slovenski-filmski-arhiv/"
SFA_ENGLISH_URL = (
    "https://www.gov.si/en/state-authorities/bodies-within-ministries/"
    "archives-of-the-republic-of-slovenia/about-the-archives/slovenian-film-archives/"
)
SFA_VAC_HOME_URL = "https://vac.sjas.gov.si/vac"
SFA_VAC_SEARCH_URL = "https://vac.sjas.gov.si/vac/search/getfullTextPage"
SFA_VAC_FUND_URL = "https://vac.sjas.gov.si/vac/search/details?id=25366"
SFA_VAC_RECORD_URL_TEMPLATE = "https://vac.sjas.gov.si/vac/search/details?id={record_id}"
ARCHIPOP_HOME_URL = "https://archipop.org/"
ARCHIPOP_FILMS_URL = "https://lesfilms.archipop.org/"
ARCHIPOP_FILMS_LIST_URL_TEMPLATE = "https://lesfilms.archipop.org/les-films-570-0-0-{page}.html"
APE_FIND_URL = "https://www.archivesportaleurope.net/find-an-institution/"
APE_CONTENT_PDF_URL = "https://www.archivesportaleurope.net/uploads/files/20251215_OnlyInstitutionsWithContent.pdf"
APE_ALL_INSTITUTIONS_PDF_URL = "https://www.archivesportaleurope.net/uploads/files/20251215_AllInstitutions.pdf"
APE_DETAIL_URL_TEMPLATE = (
    "https://www.archivesportaleurope.net/advanced-search/search-in-institutions/"
    "results-%28institutions%29/?repositoryCode={repository_code}"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)"
}

REQUEST_TIMEOUT = 25
PLAYWRIGHT_TIMEOUT = 25000
SLEEP_BETWEEN_REQUESTS = 0.5
MAX_INTERNAL_PAGES = 5

VIDEO_PLATFORMS = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "vimeo.com": "Vimeo",
    "player.vimeo.com": "Vimeo",
    "dailymotion.com": "Dailymotion",
    "archive.org": "Internet Archive",
    "replay.bfi.org.uk": "BFI Replay",
    "player.bfi.org.uk": "BFI Player",
    "bnt.bg": "BNT.bg",
    "p.bnt.bg": "BNT.bg",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "jwplayer.com": "JW Player",
    "brightcove.net": "Brightcove",
    "madelen.ina.fr": "Madelen",
    "mediaclip.ina.fr": "Mediaclip INA",
    "euscreen.eu": "EUscreen",
    "www.euscreen.eu": "EUscreen",
    "europeanfilmgateway.eu": "European Film Gateway",
    "www.europeanfilmgateway.eu": "European Film Gateway",
    "europeana.eu": "Europeana",
    "www.europeana.eu": "Europeana",
    "pares.mcu.es": "PARES",
    "pares.cultura.gob.es": "PARES",
    "portal.arquivos.pt": "Portal Português de Arquivos",
    "americanarchive.org": "American Archive of Public Broadcasting",
    "www.americanarchive.org": "American Archive of Public Broadcasting",
    "dr.dk": "DRTV/Gensyn",
    "www.dr.dk": "DRTV/Gensyn",
    "prod95-cdn.dr-massive.com": "DRTV/Gensyn",
    "eventbook.ro": "Eventbook",
    "aqshf.gov.al": "AQSHF",
    "films.arsenal-berlin.de": "Arsenal Film Database",
    "aamod.it": "AAMOD",
    "www.aamod.it": "AAMOD",
    "vac.sjas.gov.si": "VAC",
    "archipop.org": "Archipop",
    "lesfilms.archipop.org": "Archipop",
    "diazarchipop.oembed.diazinteregio.org": "Archipop",
    "memoire.ciclic.fr": "Ciclic Mémoire",
    "medias.ciclic.fr": "Ciclic Mémoire",
    "cineam.asso.fr": "CINÉAM",
    "www.cineam.asso.fr": "CINÉAM",
    "diazcineam.oembed.diazinteregio.org": "CINÉAM",
    "cinememoire.net": "Cinémémoire",
    "www.cinememoire.net": "Cinémémoire",
    "3cat.cat": "3Cat",
    "www.3cat.cat": "3Cat",
    "api.3cat.cat": "3Cat API",
    "api.ccma.cat": "3Cat API",
    "ceskatelevize.cz": "Česká televize iVysílání",
    "www.ceskatelevize.cz": "Česká televize iVysílání",
    "filmportal.de": "filmportal.de",
    "www.filmportal.de": "filmportal.de",
    "dhm.de": "DHM Zeughauskino online",
    "www.dhm.de": "DHM Zeughauskino online",
    "ecpad.fr": "ECPAD Archives",
    "www.ecpad.fr": "ECPAD Archives",
    "archives.ecpad.fr": "ECPAD Archives",
    "archive.ert.gr": "ERT Archive",
    "ert.gr": "ERT Archive",
    "www.ert.gr": "ERT Archive",
    "eafa.org.uk": "East Anglian Film Archive",
    "www.eafa.org.uk": "East Anglian Film Archive",
    "deutsche-kinemathek.de": "Deutsche Kinemathek Selects",
    "www.deutsche-kinemathek.de": "Deutsche Kinemathek Selects",
    "cinearchives.org": "Ciné-Archives",
    "www.cinearchives.org": "Ciné-Archives",
    "diazcinearchives.oembed.diazinteregio.org": "Ciné-Archives",
    "cinematheque-bretagne.bzh": "Cinémathèque de Bretagne",
    "www.cinematheque-bretagne.bzh": "Cinémathèque de Bretagne",
    "cinematheque-bretagne.fr": "Cinémathèque de Bretagne",
    "www.cinematheque-bretagne.fr": "Cinémathèque de Bretagne",
    "diazcdb.oembed.diazinteregio.org": "Cinémathèque de Bretagne",
    "cinematheque.fr": "Cinémathèque française",
    "www.cinematheque.fr": "Cinémathèque française",
    "player.vimeo.com": "Vimeo",
    "cinematek.be": "CINEMATEK",
    "www.cinematek.be": "CINEMATEK",
    "avilafilm.be": "Avila",
    "www.avilafilm.be": "Avila",
    "stream.sooner.be": "Sooner",
    "eyefilm.nl": "Eye Filmmuseum",
    "www.eyefilm.nl": "Eye Filmmuseum",
    "filmdatabase.eyefilm.nl": "Eye Filmdatabase",
    "player.eyefilm.nl": "Eye Film Player",
    "cinematheque.ch": "Cinémathèque suisse",
    "www.cinematheque.ch": "Cinémathèque suisse",
    "api.memobase.ch": "Memobase LOD API",
    "memobase.ch": "Memobase",
    "letelepherique.org": "Cinémathèque des Pays de Savoie et de l'Ain",
    "www.letelepherique.org": "Cinémathèque des Pays de Savoie et de l'Ain",
    "diazcpsa.oembed.diazinteregio.org": "Cinémathèque des Pays de Savoie et de l'Ain",
    "cinematheque.saint-etienne.fr": "Cinémathèque de Saint-Étienne",
    "diazcse.oembed.diazinteregio.org": "Cinémathèque de Saint-Étienne",
    "cinemateca.pt": "Cinemateca Digital",
    "www.cinemateca.pt": "Cinemateca Digital",
    "felix.cinemateca.pt": "Portal Félix",
    "digital.cinemateca.pt": "Cinemateca Digital",
    "cnasearch.public.lu": "CNAsearch",
    "cna.kiss.lu": "CNAsearch",
    "cna.public.lu": "CNA Luxembourg",
    "cnc.fr": "CNC",
    "www.cnc.fr": "CNC",
    "lise.cnc.fr": "LISE CNC",
    "cnc-aff.fr": "Archives françaises du film",
    "www.cnc-aff.fr": "Archives françaises du film",
    "archivioluce.com": "Archivio Luce",
    "www.archivioluce.com": "Archivio Luce",
    "patrimonio.archivioluce.com": "Archivio Luce",
    "videocinecitta.bytewise.it": "Archivio Luce",
    "memoirefilmiquedusud.eu": "Mémoire Filmique Pyrénées-Méditerranée",
    "www.memoirefilmiquedusud.eu": "Mémoire Filmique Pyrénées-Méditerranée",
    "filmo.platfo.es": "Platfo Filmo",
    "filmarchiv.at": "Filmarchiv ON",
    "www.filmarchiv.at": "Filmarchiv ON",
    "cdn.filmarchiv.at": "Filmarchiv ON",
    "emuseum.duesseldorf.de": "d:kult online",
    "filmmuseum-duesseldorf.de": "Filmmuseum Düsseldorf",
    "www.duesseldorf.de": "Landeshauptstadt Düsseldorf",
}

VIDEO_HINTS_IN_URL = [
    "/video",
    "/videos",
    "/watch",
    "/media",
    "/multimedia",
    "/film",
    "/films",
    "/collection",
    "/collections",
    "/archive",
    "/archives",
    "/player",
]

VIDEO_FILE_EXTENSIONS = (
    ".mp4",
    ".m3u8",
    ".webm",
    ".mov",
    ".avi",
    ".m4v",
)

ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_PREFIX = "iasa_v32"
CCAAA_OUTPUT_PREFIX = "ccaaa"
APE_OUTPUT_PREFIX = "ape"
INA_OUTPUT_PREFIX = "ina"
EUSCREEN_OUTPUT_PREFIX = "euscreen"
EUROPEAN_FILM_GATEWAY_OUTPUT_PREFIX = "efg"
EUROPEANA_OUTPUT_PREFIX = "europeana"
PARES_OUTPUT_PREFIX = "pares"
PPA_OUTPUT_PREFIX = "ppa"
AAPB_OUTPUT_PREFIX = "aapb"
ANF_OUTPUT_PREFIX = "anf"
AQSHF_OUTPUT_PREFIX = "aqshf"
IAM_OUTPUT_PREFIX = "iam"
AUTREFOIS_OUTPUT_PREFIX = "autrefois"
BBC_OUTPUT_PREFIX = "bbc"
BFI_OUTPUT_PREFIX = "bfi"
BNT_OUTPUT_PREFIX = "bnt"
BNFA_OUTPUT_PREFIX = "bnfa"
CNCAFF_OUTPUT_PREFIX = "cnc_aff"
LUCE_OUTPUT_PREFIX = "luce"
BARCH_OUTPUT_PREFIX = "barch"
ASIM_OUTPUT_PREFIX = "asim"
CRNOGORSKA_KINOTEKA_OUTPUT_PREFIX = "crnogorska_kinoteka"
ARSENAL_OUTPUT_PREFIX = "arsenal"
CICLIC_OUTPUT_PREFIX = "ciclic"
CINEAM_OUTPUT_PREFIX = "cineam"
CINEMEMOIRE_OUTPUT_PREFIX = "cinememoire"
CCMA_OUTPUT_PREFIX = "ccma"
CZECH_TELEVISION_OUTPUT_PREFIX = "czech_tv"
DFF_OUTPUT_PREFIX = "dff"
DHM_OUTPUT_PREFIX = "dhm"
ECPAD_OUTPUT_PREFIX = "ecpad"
ERT_OUTPUT_PREFIX = "ert"
EAFA_OUTPUT_PREFIX = "eafa"
DEUTSCHE_KINEMATHEK_OUTPUT_PREFIX = "deutsche_kinemathek"
DR_OUTPUT_PREFIX = "dr"
CINEARCHIVES_OUTPUT_PREFIX = "cinearchives"
CINEMATHEQUE_BRETAGNE_OUTPUT_PREFIX = "cinematheque_bretagne"
CINEMATHEQUE_FRANCAISE_OUTPUT_PREFIX = "cinematheque_francaise"
CINEMATEK_OUTPUT_PREFIX = "cinematek"
EYE_OUTPUT_PREFIX = "eye"
ESTONIAN_FILM_ARCHIVE_OUTPUT_PREFIX = "efa_estonia"
FILMARCHIV_AUSTRIA_OUTPUT_PREFIX = "filmarchiv_austria"
FILMMUSEUM_DUSSELDORF_OUTPUT_PREFIX = "filmmuseum_dusseldorf"
FILMOTECA_CATALUNYA_OUTPUT_PREFIX = "filmoteca_catalunya"
FILMOTECA_ESPANOLA_OUTPUT_PREFIX = "filmoteca_espanola"
FILMOTECA_VALENCIANA_OUTPUT_PREFIX = "filmoteca_valenciana"
CINEMATHEQUE_SUISSE_OUTPUT_PREFIX = "cinematheque_suisse"
CPSA_OUTPUT_PREFIX = "cpsa"
SAINT_ETIENNE_OUTPUT_PREFIX = "saint_etienne"
CDNA_OUTPUT_PREFIX = "cdna"
CINEMATECA_PT_OUTPUT_PREFIX = "cinemateca_pt"
FILMOTECA_VASCA_OUTPUT_PREFIX = "filmoteca_vasca"
CNA_OUTPUT_PREFIX = "cna"
AAMOD_OUTPUT_PREFIX = "aamod"
SFA_OUTPUT_PREFIX = "sfa"
ARCHIPOP_OUTPUT_PREFIX = "archipop"
OUTPUT_DIR = ROOT_DIR / "data" / "output"

CDNA_HOME_URL = "https://cdna.memoirefilmiquenouvelleaquitaine.fr/"
CDNA_FILMS_URL = "https://cdna.memoirefilmiquenouvelleaquitaine.fr/films"
CDNA_API_URL = "https://cdna.memoirefilmiquenouvelleaquitaine.fr/index.php"
CDNA_VIDEO_BASE_URL = "https://videos-cdna.memoirefilmiquenouvelleaquitaine.fr"
FILMARCHIV_AUSTRIA_HOME_URL = "https://www.filmarchiv.at/"
FILMARCHIV_AUSTRIA_ON_URL = "https://www.filmarchiv.at/de/filmarchiv-on"
FILMMUSEUM_DUSSELDORF_HOME_URL = "https://filmmuseum-duesseldorf.de/"
FILMMUSEUM_DUSSELDORF_ARCHIVE_URL = "https://filmmuseum-duesseldorf.de/forschung/audiovisuelles-archiv"
DKULT_DUSSELDORF_AV_COLLECTION_URL = "https://emuseum.duesseldorf.de/collections/56457/audiovisuelle-dokumente-zu-dusseldorf"
DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL = f"{DKULT_DUSSELDORF_AV_COLLECTION_URL}/objects"
DKULT_DUSSELDORF_COLLECTION_PAGE_URL_TEMPLATE = f"{DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL}/images?page={{page}}"
FILMOTECA_CATALUNYA_HOME_URL = "https://www.filmoteca.cat/web/es/coleccion-filmica"
FILMOTECA_CATALUNYA_PLATFO_URL = "https://filmo.platfo.es/pages/home"
FILMOTECA_ESPANOLA_HOME_URL = "https://www.cultura.gob.es/cultura/areas/cine/filmoteca-espanola.html"
FILMOTECA_ESPANOLA_PLATFO_URL = "https://filmo.platfo.es/pages/home"
FILMOTECA_ESPANOLA_API_URL = "https://galgo-filmoteca.galgo.tv"
FILMOTECA_VALENCIANA_HOME_URL = "https://ivc.gva.es/es/audiovisuales/la-filmoteca-es"
FILMOTECA_VALENCIANA_RESTORATIONS_URL = "https://www.restauracionesfilmoteca.com/"
FILMOTECA_VALENCIANA_CATALOG_URL = "http://arxiu.ivac-lafilmoteca.es:8080/IVAC/"
