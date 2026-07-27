INBOX — drop zone (untracked).

Put new documents here (invoices, receipts, product data, exports). The team files each item
into archive/ per project_memory/filing_plan.yaml, the single machine-readable filing truth — a
hook checks the DESTINATION against the plan before the move, so a document no rule covers is
never filed at all; the team asks you with a concrete rule proposal instead. The archive tree
itself is the record of what ended up where — nobody writes a filing log by hand, and the
regenerated scan index over the tree (project_memory/generated/filing_log.yaml, where every
rebuilt rollup lives) is planned but not built yet, so a fresh project has no such file. Items
the team cannot classify go to archive/_unsorted/ with a question list; nothing is ever deleted.
