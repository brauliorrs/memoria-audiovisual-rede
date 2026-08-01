from bs4 import BeautifulSoup

from memoria_audiovisual.digital_infrastructure_audit import (
    detect_ai_cataloguing,
    detect_apis,
    detect_cms,
    detect_interoperability,
    detect_metadata,
    detect_restrictions,
    detect_search,
)


HTML = """
<html>
  <head>
    <meta name="generator" content="Omeka S 4.0">
    <meta name="DC.title" content="Arquivo de teste">
    <meta property="og:title" content="Arquivo de teste">
    <link rel="alternate" type="application/rss+xml" href="/feed">
    <link rel="service" href="/iiif/manifest/1">
    <script type="application/ld+json">{"@context":"https://schema.org"}</script>
  </head>
  <body>
    <form action="/search"><input name="q"></form>
    <p>Automatic transcription is used to enrich archive metadata and indexing.</p>
    <p>Sign in to access restricted materials.</p>
  </body>
</html>
"""


def test_detectors_find_public_signals():
    soup = BeautifulSoup(HTML, "html.parser")

    assert detect_cms(HTML, soup, {}) == "Omeka S 4.0"
    api_types, _, urls = detect_apis(HTML, soup, "https://example.org")
    assert "IIIF" in api_types
    assert "https://example.org/iiif/manifest/1" in urls
    assert "Dublin Core" in detect_metadata(HTML, soup)
    assert "JSON-LD / Schema.org" in detect_metadata(HTML, soup)
    assert "Schema.org" in detect_interoperability(HTML, soup)
    assert "RSS/Atom" in detect_interoperability(HTML, soup)
    assert "Formulário de busca HTML" in detect_search(soup, HTML)
    assert "Autenticação/login" in detect_restrictions(soup, soup.get_text(" "))

    status, evidence = detect_ai_cataloguing(soup.get_text(" "))
    assert status == "Evidência pública textual detectada"
    assert "Automatic transcription" in evidence
