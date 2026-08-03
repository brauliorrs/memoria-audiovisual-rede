"""Registro e carregamento canônico dos artefatos da infraestrutura científica."""

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
    "InfrastructureRegistry",
    "LoadedArtifact",
    "ScientificInfrastructureLoader",
    "build_default_registry",
]
