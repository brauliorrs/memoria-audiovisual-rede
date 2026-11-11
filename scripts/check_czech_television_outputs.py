"""Fail-closed Czech TV completeness gate, separate from staged probes.

Public episode records, independently validated samples and a complete,
source-reconciled corpus are different claims. The bounded MVP collector never
attests the last two. No network access is performed by this verifier.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import CZECH_TELEVISION_IVYSILANI_URL, OUTPUT_DIR
from memoria_audiovisual.output_files import CZECH_TELEVISION_OUTPUT_FILES


def _positive_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_czech_episode_url(value):
    try:
        parsed = urlparse(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname == "www.ceskatelevize.cz"
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
            and not parsed.query
            and not parsed.fragment
            and re.fullmatch(r"/porady/\d{2,}-[a-z0-9-]+/\d+/?", parsed.path, re.I)
            is not None
        )
    except (ValueError, TypeError):
        return False


def _load_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _row_value(frame, name):
    if len(frame) != 1 or name not in frame.columns:
        return None
    return frame.iloc[0][name]


def _check_full_completion_evidence(coverage, actual_records):
    """Return reasons; merely setting corpus_complete=True is insufficient."""
    issues = []
    if coverage.get("scope") != "full_public_catalogue":
        issues.append("escopo integral oficial não declarado")
    if coverage.get("completion_status") != "verified_complete":
        issues.append("estado de completude não comprovado")
    declared = coverage.get("source_declared_total")
    enumerated = coverage.get("enumerated_unique_records")
    if not _positive_integer(declared) or declared != actual_records:
        issues.append("total declarado pela origem ausente ou divergente")
    if not _positive_integer(enumerated) or enumerated != actual_records:
        issues.append("enumeração deduplicada incompatível")
    if coverage.get("pagination_exhausted") is not True:
        issues.append("paginação não comprovadamente exaurida")
    if coverage.get("failed_pages") != 0 or isinstance(coverage.get("failed_pages"), bool):
        issues.append("páginas com falhas ou contador inválido")
    evidence = coverage.get("completion_evidence")
    if not isinstance(evidence, dict):
        issues.append("manifesto de proveniência integral ausente")
    else:
        if evidence.get("source_url") != CZECH_TELEVISION_IVYSILANI_URL:
            issues.append("fonte oficial da evidência integral divergente")
        if evidence.get("method") != "official_paginated_exhaustion":
            issues.append("método de enumeração integral não documentado")
        if not _positive_integer(evidence.get("audited_pages")):
            issues.append("páginas auditadas não demonstradas")
        if not re.fullmatch(r"[0-9a-f]{64}", str(evidence.get("checkpoint_chain_sha256") or "")):
            issues.append("cadeia de checkpoint integral ausente")
    return issues


def validate(output_dir=OUTPUT_DIR):
    """Return (eligible_for_complete_corpus, diagnostic). No collection occurs."""
    all_files = [output_dir / filename for filename in CZECH_TELEVISION_OUTPUT_FILES.values()]
    missing = [p.name for p in all_files if not p.is_file()]
    diagnosis = {
        "accessible_records": 0,
        "validated_sample_records": 0,
        "corpus_complete": False,
        "eligibility": "HOLD",
        "reasons": [],
    }
    if missing:
        diagnosis["reasons"].append("arquivos esperados ausentes: " + ", ".join(missing))
        return False, diagnosis

    try:
        institutions = _load_csv(output_dir / CZECH_TELEVISION_OUTPUT_FILES["institutions"])
        summary = _load_csv(output_dir / CZECH_TELEVISION_OUTPUT_FILES["summary"])
        links = _load_csv(output_dir / CZECH_TELEVISION_OUTPUT_FILES["video_links"])
        catalog = _load_csv(output_dir / CZECH_TELEVISION_OUTPUT_FILES["analytic_video_catalog"])
        snapshot = json.loads(
            (output_dir / CZECH_TELEVISION_OUTPUT_FILES["snapshot_metadata"]).read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError, json.JSONDecodeError, pd.errors.ParserError) as error:
        diagnosis["reasons"].append("artefatos ausentes de esquema válido: " + type(error).__name__)
        return False, diagnosis
    if not isinstance(snapshot, dict):
        diagnosis["reasons"].append("snapshot de metadados inválido")
        return False, diagnosis

    diagnosis["accessible_records"] = len(links)
    if institutions.empty or summary.empty or links.empty or catalog.empty:
        diagnosis["reasons"].append("instituições, amostra ou catálogo analítico vazios")
    if snapshot.get("dataset") != "czech-television":
        diagnosis["reasons"].append("dataset diferente de czech-television")
    if snapshot.get("source_url") != CZECH_TELEVISION_IVYSILANI_URL:
        diagnosis["reasons"].append("origem iVysílání não reconhecida")
    counts = snapshot.get("counts")
    if not isinstance(counts, dict):
        counts = {}
    if counts.get("video_links_total") != len(links):
        diagnosis["reasons"].append("contagem de links diverge do snapshot")
    if counts.get("videos_in_curatorial_catalog") != len(catalog):
        diagnosis["reasons"].append("catálogo analítico diverge do snapshot")
    if len(links) != len(catalog):
        diagnosis["reasons"].append("links acessíveis e catálogo analítico não reconciliados")

    required = {"platform", "video_link", "video_title", "video_description"}
    if not required.issubset(links.columns):
        diagnosis["reasons"].append("colunas de prova dos links ausentes")
    else:
        if not links["platform"].eq("Česká televize iVysílání").all():
            diagnosis["reasons"].append("plataforma oficial diferente")
        if not links["video_link"].map(_is_czech_episode_url).all():
            diagnosis["reasons"].append("URL de episódio fora da origem permitida")
        if links["video_link"].duplicated().any():
            diagnosis["reasons"].append("URLs de episódios duplicadas")
        if links["video_title"].str.strip().eq("").any():
            diagnosis["reasons"].append("títulos de episódios ausentes")
        if not links["video_description"].str.contains(
            r"(?:mediaMeta|episode)\.isPlayable=True", regex=True
        ).all():
            diagnosis["reasons"].append("prova positiva individual de isPlayable ausente")

    coverage = snapshot.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("contract_version") != 1:
        diagnosis["reasons"].append("contrato explícito de cobertura ausente")
        return False, diagnosis

    accessible = coverage.get("accessible_records")
    sample = coverage.get("validated_sample_records")
    if not _nonnegative_integer(accessible) or accessible != len(links):
        diagnosis["reasons"].append("registros acessíveis não reconciliados")
    if not _nonnegative_integer(sample) or sample > len(links):
        diagnosis["reasons"].append("contagem de amostra validada inválida")
    else:
        diagnosis["validated_sample_records"] = sample
        if sample > 0:
            proof = coverage.get("sample_checkpoint_reference")
            if (
                coverage.get("sample_validation_status") != "checkpoint_verified"
                or not isinstance(proof, dict)
                or not _positive_integer(proof.get("run_id"))
                or not re.fullmatch(r"[0-9a-f]{64}", str(proof.get("chain_sha256") or ""))
            ):
                diagnosis["reasons"].append("amostra validada sem checkpoint independente")
        elif (
            coverage.get("sample_validation_status") != "not_attested_in_this_run"
            or coverage.get("sample_checkpoint_reference") is not None
        ):
            diagnosis["reasons"].append("estado de amostragem inconsistente")

    if _row_value(summary, "accessible_records_count") != str(len(links)):
        diagnosis["reasons"].append("contador acessível no resumo não coincide")
    if _row_value(summary, "validated_sample_count") != str(sample):
        diagnosis["reasons"].append("contador de amostra no resumo não coincide")

    if coverage.get("corpus_complete") is not True:
        if (
            _row_value(summary, "coverage_scope") != "bounded_mvp"
            or _row_value(summary, "integrity_status") != "instavel"
            or _row_value(summary, "corpus_complete") not in ("False", "false")
            or _row_value(summary, "enumeration_complete") not in ("False", "false")
        ):
            diagnosis["reasons"].append("resumo parcial com alegação inconsistente")
        diagnosis["reasons"].append(
            "corpus completo NÃO demonstrado; registros acessíveis e amostras não são completude"
        )
        return False, diagnosis

    if _row_value(summary, "coverage_scope") != "full_public_catalogue":
        diagnosis["reasons"].append("resumo não declara universo integral definido")
    if _row_value(summary, "integrity_status") != "integro":
        diagnosis["reasons"].append("resumo não certifica integridade integral")
    if _row_value(summary, "corpus_complete") not in ("True", "true"):
        diagnosis["reasons"].append("resumo não certifica completude")
    if _row_value(summary, "enumeration_complete") not in ("True", "true"):
        diagnosis["reasons"].append("resumo não certifica paginação completa")
    diagnosis["reasons"].extend(_check_full_completion_evidence(coverage, len(links)))
    if diagnosis["reasons"]:
        return False, diagnosis
    diagnosis["corpus_complete"] = True
    diagnosis["eligibility"] = "COMPLETE_CORPUS_VERIFIED"
    return True, diagnosis


def main():
    eligible, diagnosis = validate()
    print("Verificação de completude — Czech Television / iVysílání")
    print(json.dumps(diagnosis, ensure_ascii=False, sort_keys=True))
    return 0 if eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
