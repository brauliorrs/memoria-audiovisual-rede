SPECIAL_COUNTRY_NAMES = {
    "BAHAMAS": "Bahamas",
    "BOLIVIA, PLURINATIONAL STATE OF": "Bolivia",
    "BRUNEI DARUSSALAM": "Brunei",
    "CZECH REPUBLIC": "Czech Republic",
    "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": "North Korea",
    "IRAN, ISLAMIC REPUBLIC OF": "Iran",
    "KOREA, REPUBLIC OF": "South Korea",
    "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "Laos",
    "MACEDONIA": "North Macedonia",
    "MOLDOVA, REPUBLIC OF": "Moldova",
    "PALESTINE, STATE OF": "Palestine",
    "REPUBLIC OF KOREA": "South Korea",
    "RUSSIAN FEDERATION": "Russia",
    "RUSSIA": "Russia",
    "SYRIAN ARAB REPUBLIC": "Syria",
    "TAIWAN, PROVINCE OF CHINA": "Taiwan",
    "TANZANIA, UNITED REPUBLIC OF": "Tanzania",
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "UNITED KINGDOM": "United Kingdom",
    "UNITED STATES": "United States",
    "UNITED STATES OF AMERICA": "United States",
    "USA": "United States",
    "U.S.A.": "United States",
    "VENEZUELA, BOLIVARIAN REPUBLIC OF": "Venezuela",
    "VIET NAM": "Vietnam",
}

COUNTRY_TO_CONTINENT = {
    "Andorra": "Europe",
    "Argentina": "South America",
    "Australia": "Oceania",
    "Austria": "Europe",
    "Azerbaijan": "Asia",
    "Bahamas": "North America",
    "Belarus": "Europe",
    "Belgium": "Europe",
    "Bolivia": "South America",
    "Brazil": "South America",
    "Brunei": "Asia",
    "Canada": "North America",
    "Chile": "South America",
    "China": "Asia",
    "Croatia": "Europe",
    "Czech Republic": "Europe",
    "Denmark": "Europe",
    "Egypt": "Africa",
    "Eritrea": "Africa",
    "Estonia": "Europe",
    "Finland": "Europe",
    "France": "Europe",
    "Germany": "Europe",
    "Greece": "Europe",
    "India": "Asia",
    "Indonesia": "Asia",
    "Iran": "Asia",
    "Iraq": "Asia",
    "Ireland": "Europe",
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
    "Namibia": "Africa",
    "Netherlands": "Europe",
    "New Zealand": "Oceania",
    "North Macedonia": "Europe",
    "Norway": "Europe",
    "Oman": "Asia",
    "Palestine": "Asia",
    "Poland": "Europe",
    "Portugal": "Europe",
    "Russia": "Europe",
    "Saudi Arabia": "Asia",
    "Serbia": "Europe",
    "Seychelles": "Africa",
    "Singapore": "Asia",
    "South Africa": "Africa",
    "South Korea": "Asia",
    "Spain": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Syria": "Asia",
    "Taiwan": "Asia",
    "Tanzania": "Africa",
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


def normalize_country(value):
    raw = str(value).strip()
    if not raw:
        return ""

    upper = raw.upper()
    if upper in SPECIAL_COUNTRY_NAMES:
        return SPECIAL_COUNTRY_NAMES[upper]

    return title_case_country(raw)


def country_to_continent(country):
    normalized = normalize_country(country)
    return COUNTRY_TO_CONTINENT.get(normalized, "Nao classificado")
