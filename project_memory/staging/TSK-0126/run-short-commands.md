# TSK-0126 -- the runs of the merge round, recorded beside the protocol

The full run and the gate suite are the two files beside this one; what follows are the
short commands whose whole output is a line or two.

## python tools/bump_kit_version.py --check

```
dev-team: unchanged (2026.09.05-6)
  office-team: unchanged (2026.09.05-6)
  research-team: unchanged (2026.09.05-6)
rc 0
```

## python tools/validate.py

```
validate.py: all structural checks passed.
rc 0
```

## python -m ruff check team-kits tools docs .claude .github user

```
All checks passed!
rc 0
```

## python -m ruff check .   (the whole repository)

```
All checks passed!
rc 0
```
