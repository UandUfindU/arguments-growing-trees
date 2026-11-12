"""Narrow local provider boundaries; no collection or network clients."""
from __future__ import annotations

import copy
from typing import Protocol

from .proxy import read_registered_rows
from .tree import timestamp


class EvidenceProvider(Protocol):
    def query(self, query: str, as_of: str) -> list[dict]:
        """Return materials public by as_of, with IDs, provenance and source text."""
        ...


class InMemoryEvidenceProvider:
    """Preloaded source excerpts, never an automatic collection result.

    query is a literal case-insensitive substring; replace this method for retrieval.
    Source text may be a labeled normalized excerpt; it is not invented model output.
    """
    def __init__(self, materials: list[dict]):
        self.materials = copy.deepcopy(materials)
        for material in self.materials:
            for key in ("id", "lineage_id", "published_at", "source_url", "text", "text_type"):
                if not isinstance(material.get(key), str) or not material[key].strip():
                    raise ValueError(f"Evidence requires {key}")
            timestamp(material["published_at"])
            if not material["source_url"].startswith("https://"):
                raise ValueError("Evidence requires an HTTPS source URL")

    def query(self, query: str, as_of: str) -> list[dict]:
        cutoff = timestamp(as_of)
        return copy.deepcopy([m for m in self.materials
                              if timestamp(m["published_at"]) <= cutoff
                              and query.casefold() in m["text"].casefold()])


class DatasetProvider(Protocol):
    def catalog(self, as_of: str) -> dict:
        """Public schema and metadata only; no future entries or private paths."""
        ...

    def registered(self, as_of: str) -> dict:
        """Executor references/load locations for the same registered datasets."""
        ...


class FileDatasetProvider:
    """Small registered files; schema checked by the existing proxy validator."""
    def __init__(self, datasets: dict):
        self.datasets = copy.deepcopy(datasets)

    def registered(self, as_of: str) -> dict:
        cutoff = timestamp(as_of)
        return copy.deepcopy({key: value for key, value in self.datasets.items()
                              if timestamp(value["available_at"]) <= cutoff})

    def catalog(self, as_of: str) -> dict:
        catalog = {}
        for dataset_id, dataset in self.registered(as_of).items():
            _, rows = read_registered_rows(dataset, as_of)
            catalog[dataset_id] = {key: value for key, value in dataset.items() if key != "path"}
            catalog[dataset_id]["observed_rows"] = len(rows)
            catalog[dataset_id]["actual_columns"] = list(rows[0])
        return catalog
