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


# What an item id looks like when a SCHEMA declares one: the type (or an alternation of types)
# followed by the four-digit number, with the anchors and the group parentheses a regex needs.
# `backlog_types._ID_RE` is the same convention read off a VALUE; this reads it off a PATTERN, and
# the two cannot be one function because the pattern is the description and the value is the thing.
_ID_PATTERN_RX = re.compile(r"\^?\(?([A-Z]{2,4}(?:\|[A-Z]{2,4})*)\)?-\\d\{4,\}\$?")


def _declared_item_types(spec: dict) -> frozenset:
    """The item types a field's declared pattern accepts, empty when it accepts no id at all.

    Read off `pattern` (scalar fields) and `item_pattern` (list fields) -- the same two keys
    `_check_field` enforces, so a field this answers "names an item" about is one the validator
    really holds to an item id.
    """
    found = set()
    for key in ("pattern", "item_pattern"):
        match = _ID_PATTERN_RX.fullmatch(spec.get(key) or "")
        if match:
            found.update(match.group(1).split("|"))
    return frozenset(found)


def _item_schemas():
    """(item type, fields) for every shipped schema that describes an ITEM.

    WHICH schema describes an item is read off the schema, not off its file name: a schema whose
    `id` field is held to an item-id pattern describes an item of that type. So a new companion
    joins by being written, and a schema that describes something else (`session_brief`,
    `result_envelope`) stays out without needing to be named anywhere.
    """
    for name in sorted(os.listdir(_SCHEMA_DIR)):
        if not name.endswith(".yaml"):
            continue
        fields = (load_schema(name[:-5]) or {}).get("fields") or {}
        owner = _declared_item_types(fields.get("id") or {})
        if len(owner) == 1:
            yield next(iter(owner)), fields


def item_required_fields() -> dict:
    """{item type -> the fields its schema REQUIRES} for the types the kernel freezes.

    The other half of `backlog_types.REQUIRED_FIELDS`, and the reason the state validator can
    judge an `ARC`/`WFR`/`DSN` at all: those items never pass `capture`, so the capture-time map
    says nothing about them and the validator's field-duty loop ran zero times for exactly the
    three types whose contract is declared here (spec II.8 assigns it "ARC ohne derives_from ->
    Validator-Flag").
    """
    return {item_type: tuple(name for name, spec in fields.items() if (spec or {}).get("required"))
            for item_type, fields in _item_schemas()}


def item_field_contracts() -> dict:
    """{item type -> {field name: the item types that field may name}} for every ITEM schema.

    THE SECOND HALF OF THE FIELD CONTRACT. `backlog_types.REQUIRED_FIELDS` declares what a
    caller must provide at CAPTURE, and therefore covers only the types `capture` creates. The
    types the kernel FREEZES instead (ARC/WFR/DSN -- spec II.6a promotion path) declare their
    fields here, in the companion/manifest schemas `staging.freeze_*` validates against. Both
    are field contracts; neither is the whole one.

    Every DECLARED field is reported, not only the required ones: whether the graph walks a field
    is a question about the field's meaning, not about whether an item may omit it.
    """
    return {item_type: {field: _declared_item_types(spec or {})
                        for field, spec in fields.items()}
            for item_type, fields in _item_schemas()}


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
