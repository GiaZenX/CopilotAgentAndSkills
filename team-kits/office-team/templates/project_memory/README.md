# project_memory/ — the business's single source of truth (office-team kit)

One writer per file (constitution §6). The manager maintains its own artifacts and routes
everything else to the owning specialist. Filled YAML state is NEVER overwritten by kit updates.

| File | Writer | Purpose |
|---|---|---|
| business_profile.yaml | Manager | the business: legal form, markets, tax flags, privacy choices, revenue sources |
| masterplan.md | Manager | the automation vision (living north star) |
| process_definitions.yaml | Manager | PROC-xxxx approved processes (+ approved_hash) |
| filing_plan.yaml / filing_log.yaml | Records-Clerk | Aktenplan (+ retention) / verified filing manifest |
| master_data.yaml | Bookkeeper | EÜR-aligned categories + counterparty normalisation |
| product_catalog.yaml / content_guidelines.yaml | Product-Editor | products + copy rules |
| compliance_register.yaml | Compliance-Researcher | sourced regulation register (+ review dates) |
| marketing_plan.yaml | Marketing-Planner | channels, accounts, calendar |
| progress.yaml / changelog.yaml / project_config.yaml | Manager | one-line status + log / events / preset + model maps |

Repo folders: `inbox/` (user drops, untracked) → `archive/` (system of record, untracked, moves
only — never deletes) → `outbox/` (drafts the USER sends, untracked). `ledger/` + `reports/` are
tracked; reports are GENERATED (`scripts/euer_report.py`), the ledger is always-validated
(`scripts/ledger_add.py`).
