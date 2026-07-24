"""V2 state-kernel core (HARNESS_V2_SPEC.md Teil II).

One Python core shared by hooks, dashboard generation, scaffold and migration
(spec II.4). Phase 1 modules:

- lock.py     -- cross-process kernel lock (II.4 "Nebenlaeufigkeit & Locking")
- hashing.py  -- canonical subject-manifest hashing (II.2 "Hash-Kanonisierung")
"""
