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
INA_PODCASTS_URL = "https://podcasts.ina.fr/"
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
APE_FIND_URL = "https://www.archivesportaleurope.net/find-an-institution/"
APE_CONTENT_PDF_URL = "https://www.archivesportaleurope.net/uploads/files/20251215_OnlyInstitutionsWithContent.pdf"
APE_ALL_INSTITUTIONS_PDF_URL = "https://www.archivesportaleurope.net/uploads/files/20251215_AllInstitutions.pdf"
APE_DETAIL_URL_TEMPLATE = (
    "https://www.archivesportaleurope.net/advanced-search/search-in-institutions/"
    "results-%28institutions%29/?repositoryCode={repository_code}"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IASA-Link-Explorer/3.2)"
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
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "soundcloud.com": "SoundCloud",
    "jwplayer.com": "JW Player",
    "brightcove.net": "Brightcove",
    "madelen.ina.fr": "Madelen",
    "podcasts.ina.fr": "Podcasts INA",
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
}

VIDEO_HINTS_IN_URL = [
    "/video",
    "/videos",
    "/watch",
    "/media",
    "/multimedia",
    "/film",
    "/films",
    "/audio",
    "/sound",
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
    ".mp3",
    ".wav",
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
OUTPUT_DIR = ROOT_DIR / "data" / "output"
