"""Indicadores analíticos nativos."""

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
    "DublinCoreCoverageIndicator",
    "IiifCoverageIndicator",
    "InteroperabilityCoverageIndicator",
    "JsonLdCoverageIndicator",
    "OaiPmhCoverageIndicator",
    "SchemaOrgCoverageIndicator",
]
