#!/usr/bin/env python3
"""
merge_settings.py <ours.json> <target.json>

Adds missing agents-and-skills global defaults (<ours.json>) to the user's
<target.json>. Existing user values always win, including personal settings such as
theme and statusLine. Two keys are the exception, and both are UNIONED rather than left
to the "existing wins" rule:

  * permissions.allow / permissions.deny — valid lists are unioned without duplicates
    while preserving the user's order.
  * hooks — a dict of event -> list of hook groups. Each event's list is unioned the
    same way, so our global defaults (the BUG-0016 handover guard among them) are ADDED
    to a user who already runs their own global hooks instead of being silently dropped.
    Without this, a target that already carries any `hooks` key would keep only the
    user's hooks and the handover guard would never install for exactly the power users
    most likely to have one (DEC-0032; measured on the "existing wins" branch below).

Keys starting with '_' (comments) are skipped. The previous target is backed up to
<target>.bak before writing.
"""
import json
import os
import shutil
import sys


def _merge_unique(existing, defaults):
    """Return an order-preserving union with the user's entries first."""
    merged = []
    for item in list(existing) + list(defaults):
        if item not in merged:
            merged.append(item)
    return merged


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: merge_settings.py <ours.json> <target.json>\n")
        sys.exit(2)
    ours_path, target_path = sys.argv[1], sys.argv[2]

    with open(ours_path, encoding="utf-8") as fh:
        ours = json.load(fh)
    if not isinstance(ours, dict):
        sys.stderr.write("ERROR: defaults in %s must be a JSON object.\n" % ours_path)
        sys.exit(2)
    ours = {k: v for k, v in ours.items() if not k.startswith("_")}

    target = {}
    if os.path.isfile(target_path):
        try:
            with open(target_path, encoding="utf-8") as fh:
                target = json.load(fh) or {}
        except Exception as exc:
            sys.stderr.write(
                "ERROR: could not parse %s (%s); left unchanged.\n"
                % (target_path, exc)
            )
            sys.exit(2)

    if not isinstance(target, dict):
        sys.stderr.write(
            "ERROR: existing settings in %s must be a JSON object; left unchanged.\n"
            % target_path
        )
        sys.exit(2)
    if os.path.isfile(target_path):
        shutil.copy2(target_path, target_path + ".bak")

    added = [k for k in ours if k not in target]
    preserved = [k for k in ours if k in target and k not in ("permissions", "hooks")]
    permission_additions = {"allow": 0, "deny": 0}
    hook_additions = 0
    for key, val in ours.items():
        if key == "hooks" and isinstance(val, dict) and isinstance(target.get(key), dict):
            # Union per event, the same rule as permissions.allow/deny: a user with their own
            # global hooks keeps them AND receives ours (DEC-0032). A non-list existing event is
            # preserved rather than replaced, mirroring the malformed-permissions handling below.
            thooks = target["hooks"]
            for event, groups in val.items():
                if event not in thooks:
                    thooks[event] = groups
                    hook_additions += len(groups) if isinstance(groups, list) else 0
                elif isinstance(groups, list) and isinstance(thooks[event], list):
                    existing = _merge_unique(thooks[event], [])
                    merged = _merge_unique(existing, groups)
                    hook_additions += len(merged) - len(existing)
                    thooks[event] = merged
                else:
                    sys.stderr.write(
                        "WARN: preserving non-list hooks.%s in %s; defaults not merged.\n"
                        % (event, target_path))
        elif key == "permissions" and isinstance(val, dict) and isinstance(target.get(key), dict):
            # Existing permission sub-keys win too. Only allow/deny receive special union
            # semantics, and malformed existing values are preserved rather than silently
            # replaced by installer defaults.
            tperm = target["permissions"]
            for sub, sval in val.items():
                if sub not in tperm:
                    tperm[sub] = sval
                elif sub in ("allow", "deny") and isinstance(sval, list):
                    existing = tperm[sub]
                    if isinstance(existing, list):
                        user_unique = _merge_unique(existing, [])
                        merged = _merge_unique(user_unique, sval)
                        permission_additions[sub] = len(merged) - len(user_unique)
                        tperm[sub] = merged
                    else:
                        sys.stderr.write(
                            "WARN: preserving non-list permissions.%s in %s; defaults not merged.\n"
                            % (sub, target_path)
                        )
        elif key not in target:
            target[key] = val
        else:
            # Existing top-level values are personal configuration and always win.
            continue

    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as fh:
        json.dump(target, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    sys.stdout.write(
        "merged settings: added defaults=%s; preserved existing=%s; "
        "permissions +allow=%d +deny=%d; hooks +%d groups; preserved %d unrelated keys\n"
        % (",".join(added) or "-", ",".join(preserved) or "-",
           permission_additions["allow"], permission_additions["deny"], hook_additions,
           len([k for k in target if k not in ours]))
    )


if __name__ == "__main__":
    main()
