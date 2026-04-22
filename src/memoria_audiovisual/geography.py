import unicodedata


SPECIAL_COUNTRY_NAMES = {
    "ALBANIA": "Albania",
    "BAHAMAS": "Bahamas",
    "BELGIEN": "Belgium",
    "BELGIQUE": "Belgium",
    "BELGIË": "Belgium",
    "BELGIË BELGIQUE BELGIEN": "Belgium",
    "BELGIÃ‹": "Belgium",
    "BELGIÃ‹ BELGIQUE BELGIEN": "Belgium",
    "BOLIVIA, PLURINATIONAL STATE OF": "Bolivia",
    "BOSNIA AND HERZEGOVINA": "Bosnia and Herzegovina",
    "BRUNEI DARUSSALAM": "Brunei",
    "BUNDESREPUBLIK DEUTSCHLAND": "Germany",
    "CZECH REPUBLIC": "Czech Republic",
    "CZECHIA": "Czech Republic",
    "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": "North Korea",
    "DEUTSCHLAND": "Germany",
    "ENGLAND": "United Kingdom",
    "ENGLAND UK ENGLAND UK": "United Kingdom",
    "ENGLAND, UK": "United Kingdom",
    "ENGLAND, UNITED KINGDOM": "United Kingdom",
    "ESPAÑA": "Spain",
    "ESPAÑA ESPAÑA": "Spain",
    "ESPAÃ‘A": "Spain",
    "ESPAÃ‘A ESPAÃ‘A": "Spain",
    "GREAT BRITAIN": "United Kingdom",
    "GRIECHENLAND": "Greece",
    "HRVATSKA": "Croatia",
    "HUNGARY": "Hungary",
    "ICELAND": "Iceland",
    "IRAN, ISLAMIC REPUBLIC OF": "Iran",
    "ISLE OF MAN": "Isle of Man",
    "ITALIA": "Italy",
    "ITALIA ITALY": "Italy",
    "KOREA, REPUBLIC OF": "South Korea",
    "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "Laos",
    "LATVIJA": "Latvia",
    "LUXEMBURG LUXEMBOURG": "Luxembourg",
    "MACEDONIA": "North Macedonia",
    "MAGYARORSZÁG": "Hungary",
    "MAGYARORSZÃG": "Hungary",
    "MOLDOVA, REPUBLIC OF": "Moldova",
    "NEDERLAND": "Netherlands",
    "NEDERLAND NEDERLAND": "Netherlands",
    "NEDERLAND NEDERLAND NEDERLAND": "Netherlands",
    "NORGE": "Norway",
    "NOUVELLE-CALÉDONIE": "New Caledonia",
    "NOUVELLE-CALÃ‰DONIE": "New Caledonia",
    "ÖSTERREICH": "Austria",
    "Ã–STERREICH": "Austria",
    "PALESTINE, STATE OF": "Palestine",
    "POLSKA": "Poland",
    "REPUBLIC OF KOREA": "South Korea",
    "ROMANIA": "Romania",
    "RUSSIAN FEDERATION": "Russia",
    "RUSSIA": "Russia",
    "SCOTLAND": "United Kingdom",
    "SCOTLAND UK": "United Kingdom",
    "SCHWEIZ": "Switzerland",
    "SLOVAK REPUBLIC": "Slovakia",
    "SLOVENSKÁ REPUBLIKA": "Slovakia",
    "SLOVENSKÃ REPUBLIKA": "Slovakia",
    "SLOVENSKO": "Slovakia",
    "SLOVENIJA": "Slovenia",
    "SLOVENIJA SLOVENIJA": "Slovenia",
    "SUISSE": "Switzerland",
    "SUOMI": "Finland",
    "SVERIGE": "Sweden",
    "SVERIGE SWEDEN": "Sweden",
    "SYRIAN ARAB REPUBLIC": "Syria",
    "TAIWAN, PROVINCE OF CHINA": "Taiwan",
    "TANZANIA, UNITED REPUBLIC OF": "Tanzania",
    "THE NETHERLANDS": "Netherlands",
    "U.K.": "United Kingdom",
    "UK": "United Kingdom",
    "UNITED KINGDOM": "United Kingdom",
    "UNITED KINGDOM UNITED KINGDOM UNITED KINGDOM": "United Kingdom",
    "UNITED STATES": "United States",
    "UNITED STATES OF AMERICA": "United States",
    "USA": "United States",
    "U.S.A.": "United States",
    "VENEZUELA, BOLIVARIAN REPUBLIC OF": "Venezuela",
    "VIET NAM": "Vietnam",
    "WALES": "United Kingdom",
    "ÍSLAND": "Iceland",
    "ÃSLAND": "Iceland",
    "ČESKÁ REPUBLIKA": "Czech Republic",
    "ÄŒESKÃ REPUBLIKA": "Czech Republic",
}

ASCII_FALLBACK_COUNTRY_NAMES = {
    "?ESK? REPUBLIKA": "Czech Republic",
    "BELGIE BELGIQUE BELGIEN": "Belgium",
    "BELGI? BELGIQUE BELGIEN": "Belgium",
    "CESKA REPUBLIKA": "Czech Republic",
    "ESPANA": "Spain",
    "ESPANA ESPANA": "Spain",
    "ESPA?A": "Spain",
    "ESPA?A ESPA?A": "Spain",
    "ISLAND": "Iceland",
    "?SLAND": "Iceland",
    "MAGYARORSZAG": "Hungary",
    "NOUVELLE-CALEDONIE": "New Caledonia",
    "NOUVELLE-CAL?DONIE": "New Caledonia",
    "OSTERREICH": "Austria",
    "SLOVENSKA REPUBLIKA": "Slovakia",
    "SLOVENSK? REPUBLIKA": "Slovakia",
}

COUNTRY_TO_CONTINENT = {
    "Albania": "Europe",
    "Andorra": "Europe",
    "Argentina": "South America",
    "Australia": "Oceania",
    "Austria": "Europe",
    "Azerbaijan": "Asia",
    "Bahamas": "North America",
    "Belarus": "Europe",
    "Belgium": "Europe",
    "Bolivia": "South America",
    "Bosnia and Herzegovina": "Europe",
    "Brazil": "South America",
    "Brunei": "Asia",
    "Bulgaria": "Europe",
    "Canada": "North America",
    "Chile": "South America",
    "China": "Asia",
    "Croatia": "Europe",
    "Cyprus": "Europe",
    "Czech Republic": "Europe",
    "Denmark": "Europe",
    "Egypt": "Africa",
    "Eritrea": "Africa",
    "Estonia": "Europe",
    "Finland": "Europe",
    "France": "Europe",
    "Georgia": "Asia",
    "Germany": "Europe",
    "Greece": "Europe",
    "Hungary": "Europe",
    "Iceland": "Europe",
    "India": "Asia",
    "Indonesia": "Asia",
    "Iran": "Asia",
    "Iraq": "Asia",
    "Ireland": "Europe",
    "Isle of Man": "Europe",
    "Israel": "Asia",
    "Italy": "Europe",
    "Jamaica": "North America",
    "Japan": "Asia",
    "Kenya": "Africa",
    "Laos": "Asia",
    "Latvia": "Europe",
    "Lithuania": "Europe",
    "Luxembourg": "Europe",
    "Malta": "Europe",
    "Mexico": "North America",
    "Moldova": "Europe",
    "Monaco": "Europe",
    "Montenegro": "Europe",
    "Namibia": "Africa",
    "Netherlands": "Europe",
    "New Caledonia": "Oceania",
    "New Zealand": "Oceania",
    "North Macedonia": "Europe",
    "Norway": "Europe",
    "Oman": "Asia",
    "Palestine": "Asia",
    "Poland": "Europe",
    "Portugal": "Europe",
    "Romania": "Europe",
    "Russia": "Europe",
    "Saudi Arabia": "Asia",
    "Serbia": "Europe",
    "Seychelles": "Africa",
    "Singapore": "Asia",
    "Slovakia": "Europe",
    "Slovenia": "Europe",
    "South Africa": "Africa",
    "South Korea": "Asia",
    "Spain": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Syria": "Asia",
    "Taiwan": "Asia",
    "Tanzania": "Africa",
    "Turkey": "Asia",
    "Tunisia": "Africa",
    "Ukraine": "Europe",
    "United Kingdom": "Europe",
    "United States": "North America",
    "Venezuela": "South America",
    "Vietnam": "Asia",
    "Zambia": "Africa",
}


def title_case_country(value):
    lowered = str(value).strip().lower()
    if not lowered:
        return ""

    words = []
    for word in lowered.split():
        if word in {"and", "of", "the"}:
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words)


def ascii_fold(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_country(value):
    raw = str(value).strip()
    if not raw:
        return ""

    upper = raw.upper()
    if upper in SPECIAL_COUNTRY_NAMES:
        return SPECIAL_COUNTRY_NAMES[upper]

    ascii_upper = ascii_fold(raw).upper()
    if ascii_upper in ASCII_FALLBACK_COUNTRY_NAMES:
        return ASCII_FALLBACK_COUNTRY_NAMES[ascii_upper]

    if "," in raw:
        for part in [segment.strip() for segment in raw.split(",") if segment.strip()]:
            normalized_part = normalize_country(part)
            if normalized_part in COUNTRY_TO_CONTINENT:
                return normalized_part

    return title_case_country(raw)


def country_to_continent(country):
    normalized = normalize_country(country)
    return COUNTRY_TO_CONTINENT.get(normalized, "Nao classificado")
