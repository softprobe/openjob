"""Load the reviewed source list and the opt-out denylist."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from indexer import ATS

_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA = _ROOT / "schema"


def load_sources(directory: Path, *, denylist: Path | None = None) -> list[dict]:
    blocked = _blocked(denylist if denylist is not None else directory / "denylist.yml")
    validator = _validator()
    found = []
    for path in sorted(directory.glob("*.yml")):
        if path.name == "denylist.yml":
            continue
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError(f"{path.name} is not a source record.")
        errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
        if errors:
            rendered = "; ".join(error.message for error in errors)
            raise ValueError(f"{path.name}: {rendered}")
        if document["ats"] not in ATS:
            raise ValueError(f"{path.name} uses an ATS that this indexer does not read.")
        key = (document["ats"], document["board"])
        if key in blocked or document["slug"] in blocked:
            continue
        found.append(document)
    return found


def _blocked(path: Path) -> set:
    if not path.is_file():
        return set()
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    blocked = set()
    for item in document.get("boards") or []:
        if not isinstance(item, dict):
            continue
        if item.get("ats") and item.get("board"):
            blocked.add((str(item["ats"]), str(item["board"])))
        if item.get("slug"):
            blocked.add(str(item["slug"]))
    return blocked


def _validator() -> Draft202012Validator:
    resources = []
    for path in _SCHEMA.glob("*.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema, default_specification=DRAFT202012)))
    registry = Registry().with_resources(resources)
    source = json.loads((_SCHEMA / "source.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(source, registry=registry)
