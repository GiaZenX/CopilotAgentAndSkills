"""Canonical subject-manifest hashing (HARNESS_V2_SPEC.md II.2 "Hash-Kanonisierung").

Canonical JSON -- sorted keys, NFC-normalized unicode, compact separators, explicit
hash_schema_version -- deliberately NOT yaml.safe_dump: PyYAML dump output is
version-dependent and un-normalized (the V1 proc_hash.py breakage class this
replaces; verified in the 2026-07-24 review).

Fail-closed: non-JSON types and NaN/Infinity raise instead of being coerced --
a hash over silently-mangled content would defeat approval invalidation.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata


HASH_SCHEMA_VERSION = 1


def _nfc(obj):
    """Recursively NFC-normalize every string (keys and values).

    Fail-closed on the two silent-collision classes (Fable-Check 4, BUG-2/3):
    non-string dict keys (json.dumps would coerce {1: x} into {"1": x}) and
    sibling keys that collide after NFC normalization (a dict comprehension
    would silently merge them -- two different manifests, one hash).
    """
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(
                    "subject_manifest dict key %r is not a string -- canonical "
                    "hashing is only defined over JSON objects (string keys). "
                    "Remedy: convert the key explicitly before hashing." % (k,)
                )
            nk = unicodedata.normalize("NFC", k)
            if nk in out:
                raise ValueError(
                    "subject_manifest contains sibling keys that collide after "
                    "NFC normalization (%r) -- refusing to hash a silently "
                    "merged manifest. Remedy: deduplicate the keys." % nk
                )
            out[nk] = _nfc(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_nfc(v) for v in obj]
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    raise TypeError(
        "subject_manifest contains non-JSON type %r -- hashes are only defined "
        "over plain JSON data (str/int/float/bool/None/list/dict). Remedy: "
        "serialize the value explicitly before hashing." % type(obj).__name__
    )


def canonical_json(obj) -> str:
    """Deterministic JSON text: sorted keys, NFC unicode, compact, no NaN."""
    return json.dumps(
        _nfc(obj),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def subject_manifest_hash(manifest) -> str:
    """SHA-256 hex over the canonical envelope {hash_schema_version, subject_manifest}.

    The version field participates in the hash: a future canonicalization change
    bumps HASH_SCHEMA_VERSION and thereby visibly invalidates old approvals
    instead of silently colliding with them.
    """
    envelope = {
        "hash_schema_version": HASH_SCHEMA_VERSION,
        "subject_manifest": manifest,
    }
    return hashlib.sha256(canonical_json(envelope).encode("utf-8")).hexdigest()
