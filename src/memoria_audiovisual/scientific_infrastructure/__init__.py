"""Registro e carregamento canônico dos artefatos da infraestrutura científica."""

from .indicator_registry import (
    IndicatorRegistry,
    IndicatorRegistryError,
    load_indicator_registry,
    validate_indicator_registry,
)
from .registry import (
    ArtifactFormat,
    ArtifactScope,
    ArtifactSpec,
    InfrastructureRegistry,
    build_default_registry,
)
from .loaders import (
    ArtifactState,
    LoadedArtifact,
    ScientificInfrastructureLoader,
)

__all__ = [
    "ArtifactFormat",
    "ArtifactScope",
    "ArtifactSpec",
    "ArtifactState",
    "IndicatorRegistry",
    "IndicatorRegistryError",
    "InfrastructureRegistry",
    "LoadedArtifact",
    "ScientificInfrastructureLoader",
    "build_default_registry",
    "load_indicator_registry",
    "validate_indicator_registry",
]
