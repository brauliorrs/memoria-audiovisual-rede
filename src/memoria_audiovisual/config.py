from pathlib import Path


BASE_URL = "https://www.iasa-web.org"
START_URL = "https://www.iasa-web.org/category/links-categories/national-archives"
IASA_CCAAA_URL = "https://www.iasa-web.org/links/ccaaa"
CCAAA_HOME_URL = "https://www.ccaaa.org/"
CCAAA_MEMBERS_URL = "https://www.ccaaa.org/pages/who-we-are/list-of-current-members.html"
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
OUTPUT_DIR = ROOT_DIR / "data" / "output"
