# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""A small JSON Schema checker for exactly the keywords the engine's published
schemas use ($ref into $defs, anyOf, type, items, properties, required,
additionalProperties). Standard library only, so the test suite needs nothing
the console does not."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

ENVELOPE = frozenset({"schema", "kind", "engine"})

_TYPES: dict[str, Any] = {
    "string": str, "integer": int, "number": (int, float), "boolean": bool,
    "array": list, "object": dict, "null": type(None),
}


def _type_ok(value: Any, name: str) -> bool:
    if name in ("integer", "number") and isinstance(value, bool):
        return False
    return isinstance(value, _TYPES[name])


def validate(instance: Any, schema: Mapping[str, Any]) -> list[str]:
    root = schema
    out: list[str] = []

    def walk(value: Any, sub: Mapping[str, Any], path: str) -> list[str]:
        if "$ref" in sub:
            ref = str(sub["$ref"])
            assert ref.startswith("#/$defs/"), f"unsupported $ref {ref}"
            return walk(value, root["$defs"][ref.split("/")[-1]], path)
        if "anyOf" in sub:
            attempts = [walk(value, option, path) for option in sub["anyOf"]]
            return [] if any(not a for a in attempts) else [f"{path}: matches none of anyOf ({attempts[0][0] if attempts[0] else ''})"]
        errs: list[str] = []
        kind = sub.get("type")
        if kind is not None and not _type_ok(value, kind):
            return [f"{path}: expected {kind}, got {type(value).__name__}"]
        if kind == "array":
            for i, item in enumerate(value):
                if "items" in sub:
                    errs += walk(item, sub["items"], f"{path}[{i}]")
        if kind == "object":
            props: Mapping[str, Any] = sub.get("properties", {})
            for name in sub.get("required", []):
                if name not in value:
                    errs.append(f"{path}: missing required {name!r}")
            for name, item in value.items():
                if name in props:
                    errs += walk(item, props[name], f"{path}.{name}")
                elif sub.get("additionalProperties") is False:
                    errs.append(f"{path}: unexpected field {name!r}")
        return errs

    if isinstance(instance, dict):
        instance = {k: v for k, v in instance.items() if k not in ENVELOPE}
    out += walk(instance, schema, "$")
    return out
