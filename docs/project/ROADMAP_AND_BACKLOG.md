# Development Roadmap & Prioritized Backlog — TÜV Austria BIC

Dependency-based waves per blueprint §19 — **conditional milestones, not calendar
promises**. Every item carries acceptance criteria; IDs trace to
`CURRENT_SYSTEM_AUDIT.md` findings and `SECURITY_MATRIX.md`.
Rule: one PR per item, tests included, release-gate checklist applied.

## Wave H — Hardening (do first; protects live money & certificates)

| ID | Item | Acceptance criteria (GIVEN/WHEN/THEN abbreviated) |
|---|---|---|
| B-01 | Branch & review discipline: merge `Aug19`→`main`, protect `main`, PR template w/ standard-vs-custom justification | direct pushes blocked; this docs PR is the first reviewed merge |
| QA-002 | CI: lint + install/upgrade + `--test-enable` on Odoo 19 container (needs D-01 for edition) | red CI blocks merge; `-u all` migration smoke passes on sanitized dump |
| SEC-001 | Server-side guard + SoD on application review approve/reject | GIVEN a salesperson WHEN calling `action_approve_review` via RPC THEN AccessError; submitter cannot approve own review; test proves it |
| FIN-001 | Close double-billing path | auto-invoice flows through SO lines (or hard-blocks manual invoicing when auto-invoice exists); order `invoice_status` truthful; regression test: audit completion → exactly one invoice; second attempt raises |
| SEC-002 | State-transition guards on NC / technical review / certificate / improvement action | direct `write({'state': ...})` by unauthorized group raises; allowed-transition map documented in module spec |
| QA-001 | Tests for the 5 unattended automations (invoice, STI, reminder, suspension/withdrawal, payment→certificate) | each cron has ≥1 happy + 1 edge test; suite green in CI |
| CFG-001 | SLA durations → `res.config.settings` (credit days, STI hours, report days, NC months, reminder months) | values configurable; defaults = current constants; crons read config |
| CFG-002 | Bank details & addresses out of QWeb → `res.company`/journal | commercial invoice renders from company/journal data; no IBAN in XML |
| SEC-004 | Feedback controller hardening (token expiry, rate limit) | expired token → 404 page; >N posts/min/IP throttled; tests |

**Exit gate:** CI green on all five modules; the four F-01..F-03 findings closed with
tests; release-gate checklist passed on a staging restore.

## Wave 1 — Data integrity & configuration

| ID | Item | Acceptance criteria |
|---|---|---|
| FIN-002 | Monetary/numeric typing for contract amounts (phase 1 of D-08) | new Monetary fields + migration parses existing text, writes difference register per blueprint §14; reports read typed fields; reconciliation report attached to PR |
| CFG-003 | Product/stage/tax references by xmlid & fiscal positions, not names (also province map → fiscal positions, D-05) | renaming a product/stage breaks nothing; install on empty DB passes (stages shipped in data) |
| CFG-004 | Ship all workflow stages in `data/` with flags (pattern: `requires_full_payment`), match by flag not name | fresh-DB install test proves automations fire |
| SEC-003 | Company scoping per D-02 outcome | record rules + company-scoped sequences on decided models; cross-company negative tests |
| D-10 | Evidence Binary → `ir.attachment` migration | files preserved (checksums compared), category gating intact |
| SEC-006/007 | `sudo()` audit + ACL tightening pass | each remaining sudo justified in comment; annex/evidence ACLs least-privilege; negative tests |

## Wave 2 — Single source of truth (the architecture debt)

| ID | Item | Acceptance criteria |
|---|---|---|
| ARC-001 | Wire `md.scheme.get_audit_days()` into mandays sheet (phase 2 of D-08) | picking scheme + personnel + audit kind computes MD from the rule book; manual override logged with reason; forms read typed values (regex parsing deleted) |
| ARC-002 | Unify execution checklist ↔ form checklists | one data source; NC sync and PDF rendering both read it; double entry eliminated |
| ARC-003 | Single certificate-dispatch flow | `project.dispatch_state` retired or driven by `tuv.certificate.dispatch`; one submit path |
| ARC-004 | FM-003 audit-report form fully fed from workflow data | no re-typing of findings |
| ARC-005 | Slim `project.project` (mirrored/legacy fields non-stored or satellite) | measured column count reduction; form load improvement; `rf_*` legacy dropped after migration |
| ARC-006 | Drop unused `stock`/`hr` deps (per D-06) or implement intended feature | manifest clean; menu rename preserved |
| QA-004 | Reproducible form-JSON pipeline (commit source forms or document regeneration; remove committed `__pycache__`) | fresh clone can regenerate checklists or docs say exactly why not |

## Wave 3 — Operations completion

| ID | Item | Acceptance criteria |
|---|---|---|
| OPS-001 | Surveillance cycle automation: register due date → draft surveillance order/project with `origin_ref` chain | reminder cron also creates the draft; planning approves; full lifecycle drill-down initial→surv-1→surv-2→recert |
| OPS-002 | Improvement actions auto-suggested from low auditor scores | CM gets a prefilled draft, not an obligation |
| FBR-001 | FBR digital-invoicing connector (only if D-05 says now) | integration contract doc; idempotent submission; STI numbers reconciled |
| CRM-001 | Standard `crm` intake before application (optional, owner call) | lead→application conversion keeps origin refs |

## Wave 4 — BI & command centres (after data is trustworthy)

UX-001 role dashboards (Planning, Finance, CM, Executive — spec in
`UX_DESIGN_SYSTEM.md` §3, native views first), UX-004 "Insurance"→"Assurance" typo
(trivial — can ride along any Wave H PR), UX-005 smart-button completeness, UX-006 digest
policy. Acceptance: every KPI drills to records; dashboard numbers reconcile to list counts
(test per blueprint §15).

## Wave 5 — Portal & governed AI (optional, needs separate approval)

Client portal (audit plan visibility, NC responses, certificate downloads, feedback);
AI layer per blueprint §12 (read-only/recommend first: NC-risk flags, feedback summaries,
collector drafts). Each requires its own module spec + ADR.

## 30 / 60 / 90-day conditional milestones

- **~30 days** (if D-01/D-03 answered in week 1): Wave H complete — CI, review gate, the
  three critical fixes (SEC-001, FIN-001, SEC-002) live, automation test suite green.
- **~60 days** (if D-02/D-05/D-08 decided): Wave 1 complete — typed money, configured
  taxes/SLAs, company scoping, fresh-DB installability.
- **~90 days**: ARC-001 + ARC-002 landed (rule-book-driven man-days, one checklist);
  OPS-001 surveillance automation in UAT.

Conditions: owner decisions on schedule, a staging database available (ADR-010), and no
scope additions. Wave 4/5 are intentionally unscheduled until Wave 2 exits.

## First sprint technical spec

**Sprint goal:** Wave H items B-01, QA-002, SEC-001, FIN-001.
Detailed spec to be written as `docs/modules/MODULE_SPEC_SEC-001.md` and
`docs/modules/MODULE_SPEC_FIN-001.md` (template: `docs/templates/MODULE_SPEC_TEMPLATE.md`)
**after** D-03/D-04/D-07 are approved — per blueprint §21 Step C, no implementation before
the owner gates. Key test skeletons:

- `GIVEN` an order in `waiting_review` `WHEN` its salesperson calls `action_approve_review`
  `THEN` `AccessError` and state unchanged; `WHEN` a Planning user who is not the submitter
  calls it `THEN` state = `review_approved` and project stage moves.
- `GIVEN` a completed audit with an auto-generated posted commercial invoice `WHEN` a user
  runs *Create Invoice* on the order `THEN` the system blocks or allocates against the same
  fee line — never a second receivable for the same fee; `AND` order `invoice_status`
  reflects the auto-invoice.
