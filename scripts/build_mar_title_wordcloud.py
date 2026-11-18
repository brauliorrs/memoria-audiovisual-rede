#!/usr/bin/env python3
"""Generate a *frequency-only* public word cloud from historical MAR titles.

Processes the frozen Streamlit corpus CSVs offline. No titles, record identifiers,
URLs or media are emitted; only broadly recurring single-word statistics.
Raw metadata and public-record admission gates remain unchanged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/data/title-wordcloud.json"
CATALOG_GLOB = "*_catalogo_videos_analitico.csv"
WORDS_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
STOP = frozenset("""
a à às ao aos as o os um uma umas uns de da das do dos des e é em no na nos nas
por para pela pelo pelos pelas com sem sobre sob entre até aos que quem onde qual
e ou outra outros outra outro numa num dun du d une un les le la l aux au et en
dans sur par pour avec sans sont est que qui des ses ces cette leur leurs avec
the and of for from a an to on in at by with without into over under about
is are was were this that these those his her their my our your its part
und der die das den dem des ein eine einer einen im am zum zur von mit auf aus
ist als bei für ueber über nach noch nicht oder ein film kino
el los las lo la de del al y en un una unos unas por para con sin sobre entre
que se su sus como más pero desde hasta este esta estas estos muy donde
gli dei degli delle della dello di da da un una uno il i lo la le e ed per con
senza nel nella nelle degli che degli sulla dall dalla alle dei
het een de van op met uit voor zonder naar aan zijn door als ook in
och att det den som med till av på för från ett en är var inte om
ja tai että se hän hänet heidän hänen jo on oli ovat mutta tämä niitä
yksi kaksi kolme ei niin kun sekä vain kuten täällä siitä ollut aina
film films filme filmes película peliculas peliculas pellicola película
cinema cine cinematic movie movies video vídeos videos videofilm
archive archives archiv arquivo arquivos archival archivalia archivio
documentary documentário dokumentti documentaire documento documents
record registro records recording footage collection collections coleção
collections catalogue catalogo catálogo catalog catalogued public
episode episódio episodi programa program programme series serie
youtube vimeo instagram facebook unknown untitled none title trailer
part parte bölüm bölümünde clip clips short shorts
série década parte edição temporada épisode replay full
""".split())
GENERIC_TITLES = frozenset("""
youtube -youtube vimeo video film moving film-video -video-
audiovisual -audiovisual- episode programme untitled
""".split())


def content_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def terms(text: str) -> set[str]:
    # Counts each word at most once per distinct title; never quotes a title.
    result = set()
    for match in WORDS_RE.finditer(text.casefold()):
        token = match.group()
        if 4 <= len(token) <= 23 and token not in STOP and not token.startswith("http"):
            result.add(token)
    return result


def choose_title(row: dict[str, str]) -> str:
    for key in ("video_title_display", "video_title"):
        raw = (row.get(key) or "").strip()
        canonical = re.sub(r"[\W_]+", "", raw.casefold())
        if raw and raw.casefold() not in GENERIC_TITLES and canonical not in {"youtube", "vimeo", "video", "film", "moving", "none", "untitled"}:
            return raw
    return ""


def analyze_corpus(code: str, titles: object, frequency: Counter, corpora_per_word: Counter) -> tuple[int, int]:
    distinct_titles: set[str] = set()
    corpus_counts: Counter = Counter()
    rows_seen = 0
    included = 0
    for title in titles:
        rows_seen += 1
        clean = str(title or "").strip()
        # Compare case-insensitive duplicates within one corpus, not across independent sources.
        normalized = re.sub(r"\s+", " ", clean.casefold())
        if not clean or normalized in distinct_titles:
            continue
        distinct_titles.add(normalized)
        tokens = terms(clean)
        if not tokens:
            continue
        included += 1
        corpus_counts.update(tokens)
    frequency.update(corpus_counts)
    corpora_per_word.update(corpus_counts.keys())
    return rows_seen, included


def build() -> dict:
    csv.field_size_limit(20_000_000)
    frequency: Counter = Counter()
    spread: Counter = Counter()
    sources: list[dict] = []
    for path in sorted((ROOT / "data/output").glob(CATALOG_GLOB)):
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not {"video_title", "video_title_display"} & set(reader.fieldnames):
                raise ValueError(f"source lacks title field: {path.name}")
            rows, included = analyze_corpus(path.stem.replace("_catalogo_videos_analitico", ""),
                (choose_title(row) for row in reader), frequency, spread)
        sources.append({
            "code": path.stem.replace("_catalogo_videos_analitico", ""),
            "rows": rows,
            "titlesWithTerms": included,
            "sha256": content_sha(path),
        })
    if len(sources) < 60:
        raise ValueError(f"insufficient corpus snapshots: {len(sources)}")
    # KAVI is the only approved individual-record catalogue; it is additionally
    # counted as a separate source, without copying any titles into this output.
    kavi = ROOT / "site/data/kavi-public.json"
    obj = json.loads(kavi.read_text(encoding="utf-8"))
    if obj.get("approvedMetadataPublication") is not True or obj.get("total") != len(obj["records"]):
        raise ValueError("KAVI publication manifest invalid")
    rows, included = analyze_corpus("kavi", (row.get("title", "") for row in obj["records"]), frequency, spread)
    sources.append({"code": "kavi", "rows": rows, "titlesWithTerms": included, "sha256": content_sha(kavi)})

    # Minimum 20 *distinct titles* and 2 independent corpora limits unique names,
    # chance disclosure, single-provider biases and source-specific vocabulary.
    ranked = sorted(
        ((word, count, spread[word]) for word, count in frequency.items()
         if count >= 20 and spread[word] >= 2),
        key=lambda item: (-item[1], -item[2], item[0]),
    )
    words = [
        {"text": text, "count": count, "corpora": number}
        for text, count, number in ranked[:38]
    ]
    if len(words) < 18:
        raise ValueError(f"insufficient significant terms: {len(words)}")
    return {
        "schema": "mar-title-wordcloud-v1",
        "source": "Streamlit historical audiovisual title snapshots + approved KAVI index",
        "measure": "Number of distinct titles containing each term; title repetitions excluded within a corpus",
        "stopwordPolicy": "multilingual PT/EN/ES/FR/IT/DE/NL/SV/FI; removes generic media words and short tokens",
        "minimumDistinctTitlesPerTerm": 20,
        "minimumCorporaPerTerm": 2,
        "corporaProcessed": len(sources),
        "titlesExamined": sum(source["rows"] for source in sources),
        "distinctTitlesWithTerms": sum(source["titlesWithTerms"] for source in sources),
        "sourceProvenance": sources,
        "words": words,
        "rawTitlesPublished": False,
        "individualRecordsPublished": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed output differs")
    parser.add_argument("--stdout", action="store_true", help="print compact JSON for reviewed publication")
    args = parser.parse_args()
    result = build()
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.stdout:
        print("MAR_WORDCLOUD_JSON_START")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        print("MAR_WORDCLOUD_JSON_END")
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != output:
            raise SystemExit("word-cloud output not reproducible; regenerate and review publication")
    elif not args.stdout:
        OUTPUT.write_text(output, encoding="utf-8")
    print(json.dumps({
        "corporaProcessed": result["corporaProcessed"],
        "titlesExamined": result["titlesExamined"],
        "distinctTitlesWithTerms": result["distinctTitlesWithTerms"],
        "displayTerms": len(result["words"]),
        "noOriginalTitlesExported": True,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
