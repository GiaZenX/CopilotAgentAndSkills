"""Strict schema validation for kernel data contracts (HARNESS_V2_SPEC.md II.5).

Loads the mandatory-field schemas from `kernel/schemas/*.yaml` and validates
instances fail-closed:
- unknown top-level fields are REJECTED (strict)
- byte budgets are measured over the canonical JSON serialization
  (`kernel.hashing.canonical_json`) -- implementation-independent
- every error message states the field and the remedy

This runs inside kernel operations (not the per-tool-call hook hot path), so
using PyYAML here is fine (spec II.5 keeps the HOT path stdlib-first).
"""
from __future__ import annotations

import os
import re

import yaml

from .hashing import canonical_json

_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")
_TYPES = {
    "str": str,
    "int": int,
    "float": (int, float),
    "bool": bool,
    "list": list,
    "dict": dict,
}
_cache = {}


class SchemaError(ValueError):
    """Instance violates its schema -- fail-closed, with per-field remedies."""

    def __init__(self, schema_name, errors):
        self.schema_name = schema_name
        self.errors = list(errors)
        super().__init__(
            "%s failed schema validation:\n- %s\nRemedy: fix the listed fields; "
            "the contract is team-kits/kernel/schemas/%s.yaml."
            % (schema_name, "\n- ".join(self.errors), schema_name)
        )


def load_schema(name: str) -> dict:
    if name not in _cache:
        path = os.path.join(_SCHEMA_DIR, name + ".yaml")
        try:
            with open(path, encoding="utf-8") as fh:
                _cache[name] = yaml.safe_load(fh)
        except FileNotFoundError:
            raise KeyError(
                "unknown schema %r -- no file at %s. Remedy: use one of the "
                "schemas shipped under team-kits/kernel/schemas/." % (name, path)
            ) from None
    return _cache[name]


def _matches(pattern: str, value: str) -> bool:
    # fullmatch + ASCII (Fable-Check 6/BUG-2): `$` would match before a trailing
    # newline ('TSK-0042\n' passing an id pattern), and \d would accept
    # non-ASCII digits -- both are silent-collision holes for ids/hashes
    return re.fullmatch(pattern, value, flags=re.ASCII) is not None


def _check_str(value, spec, where, errors):
    if spec.get("max_len") is not None and len(value) > spec["max_len"]:
        errors.append("%s: %d chars exceeds max_len %d" % (where, len(value), spec["max_len"]))
    pattern = spec.get("pattern")
    if pattern and not _matches(pattern, value):
        errors.append("%s: %r does not match pattern %s" % (where, value, pattern))


def _check_field(value, spec, where, errors):
    expected = _TYPES[spec["type"]]
    if value is None:
        if spec.get("nullable"):
            return
        errors.append("%s: null is not allowed (field is not nullable)" % where)
        return
    if not isinstance(value, expected) or (
        spec["type"] in ("int", "float") and isinstance(value, bool)
    ):
        errors.append(
            "%s: expected %s, got %s" % (where, spec["type"], type(value).__name__)
        )
        return
    if spec["type"] == "str":
        _check_str(value, spec, where, errors)
        if spec.get("enum") and value not in spec["enum"]:
            errors.append("%s: %r not in enum %s" % (where, value, spec["enum"]))
    if spec["type"] == "list":
        item_type = spec.get("item_type")
        for index, item in enumerate(value):
            item_where = "%s[%d]" % (where, index)
            if item_type and not isinstance(item, _TYPES[item_type]):
                errors.append(
                    "%s: expected %s, got %s" % (item_where, item_type, type(item).__name__)
                )
                continue
            if item_type == "str" and spec.get("item_pattern"):
                if not _matches(spec["item_pattern"], item):
                    errors.append(
                        "%s: %r does not match pattern %s"
                        % (item_where, item, spec["item_pattern"])
                    )
            if item_type == "dict" and spec.get("item_required"):
                for key in spec["item_required"]:
                    if key not in item:
                        errors.append("%s: missing required key %r" % (item_where, key))
    if spec["type"] == "dict":
        for key in spec.get("sub_required", ()):
            if key not in value:
                errors.append("%s: missing required key %r" % (where, key))
        for sub_name, sub_spec in (spec.get("sub_fields") or {}).items():
            sub_where = "%s.%s" % (where, sub_name)
            if sub_name not in value:
                if sub_spec.get("required"):
                    errors.append("%s: missing required key" % sub_where)
                continue
            _check_field(value[sub_name], sub_spec, sub_where, errors)
        if spec.get("value_pattern"):
            for key, sub_value in value.items():
                if not isinstance(sub_value, str) or not _matches(spec["value_pattern"], sub_value):
                    errors.append(
                        "%s[%r]: value must match pattern %s"
                        % (where, key, spec["value_pattern"])
                    )
        for rule in spec.get("require_if", ()):
            if value.get(rule["key"]) == rule["equals"]:
                for required_key in rule["require"]:
                    if required_key not in value:
                        errors.append(
                            "%s: %r is required when %s == %r"
                            % (where, required_key, rule["key"], rule["equals"])
                        )


def validate(instance: dict, schema_name: str) -> None:
    """Raise SchemaError on any violation; return None when valid."""
    schema = load_schema(schema_name)
    fields = schema["fields"]
    errors = []
    if not isinstance(instance, dict):
        raise SchemaError(schema_name, ["instance is %s, expected a mapping" % type(instance).__name__])
    if schema.get("strict", True):
        for key in instance:
            if key not in fields:
                errors.append("unknown field %r (schema is strict)" % key)
    for name, spec in fields.items():
        if name not in instance:
            if spec.get("required"):
                errors.append("missing required field %r" % name)
            continue
        _check_field(instance[name], spec, name, errors)
    limit = schema.get("max_serialized_bytes")
    if limit and not errors:
        try:
            size = len(canonical_json(instance).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            # a schema-conform instance can still smuggle non-JSON values into
            # unchecked positions (e.g. a YAML datetime inside a plain dict) --
            # surface it as the curated SchemaError, never a raw TypeError
            # (Fable-Check 6/NIT-4)
            raise SchemaError(schema_name, ["non-JSON value inside instance: %s" % exc]) from None
        if size > limit:
            errors.append(
                "serialized size %d bytes exceeds budget %d (reference big "
                "content from staging/evidence instead of inlining it)"
                % (size, limit)
            )
    if errors:
        raise SchemaError(schema_name, errors)
