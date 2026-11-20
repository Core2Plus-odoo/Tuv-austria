# Testing, Reconciliation, Migration & Deployment Strategy — TÜV Austria BIC

Status: **Proposed** — nothing below exists yet except where marked *verified*.

## 7.1 Current state (verified 2026-11-20)

- Automated tests exist only in `tuv_austria_dashboard/tests/test_dashboard.py` and the
  vendored OCA module. The two core modules (`tuv_austria_customization`, ~7.1k lines of
  Python; `tuv_audit_reports`, ~5.6k) have **zero tests**.
- No CI pipeline (`.github/workflows` absent), no pre-commit config, no linting config.
- A disciplined `migrations/` trail exists (versions 1.1 → 1.16), which indicates changes
  are being applied against a live/UAT database. That database is the de-facto source of
  truth; the repo has no deployment notes for it (see ADR-010: hosting unknown).

## 7.2 Test pyramid (target)

| Layer | Tooling | Scope | Gate |
|---|---|---|---|
| Static | `pre-commit`: ruff/flake8, pylint-odoo, xmllint | every commit | blocks push |
| Unit | Odoo `TransactionCase` | MD calculation rules, certificate numbering, state transitions, feedback token validation | blocks merge |
| Integration | Odoo `TransactionCase`/`HttpCase` | sale order → project → audit → certificate chain; invoice/payment triggers; cron jobs (reminder, suspension notice) | blocks merge |
| Accounting reconciliation | scripted assertions on staging copy | commercial invoice vs. sales tax invoice vs. `account.move` totals; no orphaned project payments | blocks release |
| E2E / UAT | scripted UAT playbook per business cycle | full certification cycle incl. partial payment, NC closure, suspension, withdrawal, re-certification | blocks go-live |

Priority test debt (first sprint of hardening): the five automations encoded in the
October commits — payment-triggers-certificate, 24h commercial invoice, 48h tax invoice,
surveillance reminder (-3 months), suspension/withdrawal notice — because they run
unattended and touch money or certificate validity.

## 7.3 CI (GitHub Actions, proposed)

1. `lint`: pre-commit on changed files.
2. `tests`: spin Odoo 19 + Postgres service, `odoo-bin -i tuv_md_calculation,tuv_austria_customization,tuv_audit_reports,tuv_austria_dashboard --test-enable --stop-after-init`.
3. `migration`: restore a sanitized staging dump (secret-stored URL), run `-u all`, fail on
   traceback — this protects the live DB from broken `migrations/` scripts.

## 7.4 Environments & release procedure

| Env | Purpose | Data |
|---|---|---|
| dev (local/container) | feature work | demo data only |
| staging | UAT + migration rehearsal | sanitized copy of production (client names scrambled) |
| production | live | real |

Release steps: tag → restore prod copy on staging → `-u` upgrade → run reconciliation
script → UAT sign-off recorded in the PR → deploy in a maintenance window → post-deploy
smoke test (one record through each flow) → rollback plan = pre-upgrade dump + previous
tag (document restore time).

Never: editing posted invoices/certificates in migration scripts; schema changes without a
same-PR migration; direct DB surgery on production.

## 7.5 Data migration & reconciliation rules

- Any script touching `account.move`, payments or certificates must log record counts
  before/after and write a reconciliation report attachment on a dedicated log record.
- Certificate register (`register` model) must be rebuildable from certificates — a
  `action_rebuild_register` maintenance hook is the safety net for drift.
- Historical posted documents are never mutated; corrections go through reversal/credit
  note or a new certificate revision.
