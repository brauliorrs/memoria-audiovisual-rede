"""Indicadores analíticos nativos."""

from .access import AudiovisualArchiveAccessIndex
from .composites import InteroperabilityIndexIndicator
from .coverage import ApiCoverageIndicator, InteroperabilityCoverageIndicator
from .patterns import (
    DublinCoreCoverageIndicator,
    IiifCoverageIndicator,
    JsonLdCoverageIndicator,
    OaiPmhCoverageIndicator,
    SchemaOrgCoverageIndicator,
)

__all__ = [
    "ApiCoverageIndicator",
    "AudiovisualArchiveAccessIndex",
    "DublinCoreCoverageIndicator",
    "IiifCoverageIndicator",
    "InteroperabilityCoverageIndicator",
    "InteroperabilityIndexIndicator",
    "JsonLdCoverageIndicator",
    "OaiPmhCoverageIndicator",
    "SchemaOrgCoverageIndicator",
]
