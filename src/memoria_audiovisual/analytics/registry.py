"""Registro determinístico dos indicadores disponíveis."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .base import Indicator


class IndicatorRegistry:
    """Mantém uma única implementação por identificador e versão."""

    def __init__(self, indicators: Iterable[Indicator] = ()) -> None:
        self._items: dict[tuple[str, str], Indicator] = {}
        for indicator in indicators:
            self.register(indicator)

    def register(self, indicator: Indicator) -> Indicator:
        indicator.validate_definition()
        key = (indicator.indicator_id, indicator.version)
        if key in self._items:
            raise ValueError(
                f"indicador já registrado: {indicator.indicator_id}@{indicator.version}"
            )
        self._items[key] = indicator
        return indicator

    def get(self, indicator_id: str, version: str | None = None) -> Indicator:
        candidates = [
            item
            for (registered_id, registered_version), item in self._items.items()
            if registered_id == indicator_id and (version is None or registered_version == version)
        ]
        if not candidates:
            suffix = f"@{version}" if version else ""
            raise KeyError(f"indicador não registrado: {indicator_id}{suffix}")
        if version is None and len(candidates) > 1:
            raise KeyError(f"versão ambígua para o indicador: {indicator_id}")
        return candidates[0]

    def list(self) -> tuple[Indicator, ...]:
        return tuple(
            self._items[key]
            for key in sorted(self._items, key=lambda item: (item[0], item[1]))
        )

    def __iter__(self) -> Iterator[Indicator]:
        return iter(self.list())

    def __len__(self) -> int:
        return len(self._items)
