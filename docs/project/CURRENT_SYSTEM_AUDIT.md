# Current-System Technical & Functional Audit

**Project:** TÜV Austria BIC (Bureau of Inspection & Certification) — Certification Body ERP
**Platform:** Odoo 19 (edition **to confirm**, D-01), custom addons by Core2Plus
**Audited revision:** branch `Aug19`, commit `9011b04` (2026-11-20)
**Audit date:** 2026-11-20
**Legend:** ✅ verified in code · ⚠️ verified risk · ❓ assumption / to confirm

---

## 1. Executive summary

The repository contains a **working, substantially complete certification-body ERP** built
as five Odoo 19 addons (~13.9k lines of Python, ~27.6k lines of XML). The end-to-end
certification cycle — application → contract review → proposal → contract → project →
man-day planning (ATJF) → audit plan → audit execution → nonconformities → audit report →
technical review → invoicing → payment → certificate → register → surveillance →
suspension/withdrawal → client feedback → auditor performance → management review — is
**real, linked code**, not isolated screens. Nine cron jobs and eight mail templates
automate invoicing, payment tracking, certificate preparation, reminders and notices.

The build respects several blueprint principles already: it extends `account.move` rather
than inventing a parallel invoice, uses the standard reconciliation hook for the
payment-triggers-certificate rule, keeps an append-only certificate register, enforces
four-eyes control on certificate approval, and ships a 16-step migration trail.

The main liabilities are: **financial-integrity gaps** (a double-billing path, contract
amounts stored as text), **authorization gaps** (one approval action callable by any user
via RPC, state machines enforced only in buttons, no record rules), **zero automated tests
on the two core modules**, **duplicated concepts** across modules (two checklist systems,
two dispatch flows, two man-day implementations — one of them entirely unused), and
**hard-coded business data** (bank account/IBAN, provincial tax mapping, product names,
SLA durations). None of these blocks current single-company operation, but all of them
block safe scaling, multi-company use, and compliance-grade auditability.

**Classification (per blueprint §0/§2):** path (A) **Odoo-based ERP** ✅ — all work must
follow Odoo 19 native patterns; no custom-platform or blended patterns detected.

---

## 2. Repository and process state (verified)

| Item | Finding |
|---|---|
| Branches | `main` = initial commit only; **all 59 commits live on `Aug19`** ⚠️ |
| PRs / issues | none ever opened — no code review gate ⚠️ |
| CI / lint / pre-commit | none ⚠️ |
| Tests | only `tuv_austria_dashboard` (4 cases) and the vendored OCA module; **core modules have none** ⚠️ |
| Python syntax | `compileall` clean across all modules ✅ |
| Migrations | `tuv_austria_customization` 1.1→1.16, `tuv_audit_reports` 1.1→1.3 — disciplined, implies a **live database being upgraded in place** ✅/❓ |
| Hosting / environment | unknown — no deployment config in repo (D-03) ❓ |
| Documentation | none before this document set ⚠️ |
| Licenses | custom modules LGPL-3; vendored OCA `report_qweb_pdf_watermark` is **AGPL-3** (19.0.1.0.0) — license mix to note (D-09) ⚠️ |

## 3. Module inventory (verified)

| Module | Ver. | Purpose | Size (py/xml lines) |
|---|---|---|---|
| `tuv_austria_customization` | 1.16 | Core certification workflow: 30 new models + 14 standard models extended (sale, project, account, partner, product) | 7,109 / 9,821 |
| `tuv_audit_reports` | 1.3 | Official TÜV + accreditation-body (ESYD/PNAC/SAAC) forms rendered from Odoo data; ~48 form "cards", ~27 QWeb PDF reports; depends on customization | 5,594 / 11,698 |
| `tuv_md_calculation` | 1.0 | Man-day rule book per scheme (ISO 9001/14001/27001/45001/50001/13485/20000-1/FSSC 22000) with .docx annex import wizard; **standalone — nothing calls it** ⚠️ | 932 / 5,910 |
| `tuv_austria_dashboard` | 1.0 | OWL client-portfolio dashboard over `res.partner` only | 228 / 178 |
| `report_qweb_pdf_watermark` | 19.0.1.0.0 | OCA watermark for QWeb PDFs (vendored) | — |

Dependency direction: `tuv_audit_reports` → `tuv_austria_customization` → standard Odoo.
`tuv_md_calculation` and `tuv_austria_dashboard` are leaves with no dependents. No cycles. ✅

## 4. Functional coverage — what demonstrably works

The chain below is wired with relational fields, overrides and crons (file references in
`docs/architecture/PROCESS_LINKAGE_MATRIX.md`):

1. **Intake & contract:** `sale.order.document_type` drives application / review / proposal /
   contract documents with a dedicated `TUV-` sequence; review workflow
   (`draft → waiting_review → review_approved`) gates the proposal; selecting a contract type
   auto-confirms the order and creates the linked project.
2. **Planning:** ATJF (`draft → to_review → reviewed`) with required-field checks and
   auto-reset when any of 17 planning fields change; approval auto-emails the audit plan.
3. **Execution:** audit start requires reviewed ATJF + standard + EA code + scope, loads
   clause checklists; completion requires all lines resolved with evidence on NC/N-A lines.
4. **Completion fan-out (one trigger, five effects):** NC records synced from checklist;
   report activity with 5-day deadline; commercial invoice auto-created and **posted** on
   `account.move` and emailed; draft sales-tax invoice (FBR-style STI numbering, 48-hour
   SLA, Tax-Manager-gated issue); payment tracking starts (7-day credit).
5. **Decision:** technical review (ISO/IEC 17021-1 checklist; reviewer independence enforced
   by constraint — not on the audit team, didn't submit the report, has the EA code).
6. **Certificate:** `create()` hard-guard (technical review approved + no open major NC +
   100 % payment — holds even under sudo) ✅; payment reconciliation, review approval and
   major-NC closure each trigger preparation; numbering `TUV/CERT/%(year)s/`; four-eyes
   approval; print stores PDF as attachment; dispatch log (courier/email/in-person);
   append-only register with daily completeness cron.
7. **Post-certification:** surveillance reminders (-3 months, daily cron); suspension after
   3 months overdue; withdrawal after configurable grace days; feedback auto-sent on stage
   entry via public token form; auditor performance per job + annual review that writes
   competence back to the partner; improvement actions (CA/IA) with separate verifier;
   management-review aggregation report.

This satisfies, in structure, the October requirement set (the commit log 2026-10-08 →
2026-10-15 is a literal requirement-by-requirement trace).

## 5. Critical findings (ranked)

### F-01 ⚠️ Double-billing path (financial integrity) — **highest priority**
The automatic commercial invoice is created **without sale-order lines**, so the order's
standard `invoice_status` never reflects it; meanwhile `_add_contract_invoice_line()` plus
the standard *Create Invoice* wizard can bill the same contract fee again. The only guard
is the `commercial_invoice_id` link, which does not block a second invoice raised from the
order after the automatic one. Violates blueprint §4.2/§9 (one authoritative owner per
receivable fact). → Backlog **FIN-001**.

### F-02 ⚠️ Review approval callable by any user (security)
`sale.order.action_approve_review` / `action_reject_review` have **no server-side group
check** — the `groups=` restriction exists only on view buttons — and the methods write via
`sudo()`. Any internal user (e.g. the salesperson who created the order) can approve their
own review over RPC. Other gated actions (ATJF, NC closure, certificate, STI) do check
`has_group`, so this is an omission, not a pattern. → **SEC-001**.

### F-03 ⚠️ State machines enforced only in buttons
`state` on nonconformities, technical reviews, certificates and improvement actions is
writable directly by any group holding write access, bypassing checklist/evidence guards.
Hard stops exist only on certificate `create()`, the stage payment constraint and the
register. Blueprint §8 requires transition guards on the server. → **SEC-002**.

### F-04 ⚠️ No record rules at all / partial `company_id` coverage
No `ir.rule` anywhere; only STI and surveillance reminders carry `company_id`; sequences
are global. Single-company today (❓ to confirm, D-02) but any second company or external
viewer role breaks isolation. Register-viewer group exists for PNAC assessors — record
rules are the missing half of that feature. → **SEC-003**.

### F-05 ⚠️ Monetary amounts as text
Contract fees and the entire ~80-field man-day sheet are `Char` fields, parsed back by
regex (8 h/man-day assumption) in `tuv_audit_reports`. Violates blueprint §4.2 (fixed-point
money, no display-string identity). Any typo silently corrupts invoices and forms.
→ **FIN-002**.

### F-06 ⚠️ Duplicated concepts across modules
1. **Man-days:** `md.scheme.get_audit_days()` (rule book with imported official annexes) is
   **never called**; the sale/project man-day sheet re-implements the same idea in free text.
2. **Checklists:** execution checklist (`tuv.audit.checklist.line`, drives NCs) vs form
   checklists (`tuv.form.*`, drive PDFs) — nothing syncs them.
3. **Dispatch:** `tuv.certificate.dispatch` (customization) vs `project.dispatch_state`
   (audit_reports) with its own to-dos.
4. **Audit report:** workflow fields (`report_state`, conclusion) vs FM-003 form (`ar_*`)
   partially fed from them.
Violates single-source-of-truth. → **ARC-001..004**.

### F-07 ⚠️ Hard-coded business data
Bank name, **account number and IBAN** in the commercial-invoice QWeb template; company
legal name and Lahore/Karachi/Islamabad addresses in proposal/contract reports; Pakistani
province→tax mapping and Punjab exemption wording in Python; products matched **by exact
name** (incl. an em-dash: "Surveillance Audit — Year 1"); PKR/USD forced on products; SLA
durations (7-day credit, 48-h STI, 5-day report, 3/6-month NC, 3-month reminder) as code
constants (only withdrawal grace days configurable). → **CFG-001..003**.

### F-08 ⚠️ `project.project` table width & stage-name matching
Hundreds of stored columns (≈100 mirrored order fields incl. legacy `rf_*`, all `md_*`,
every form mixin) plus ~40 One2many fields on one model; stages such as "Certificate
Issuance" / "Feedback & Continuous Improvement" are matched **by name** and are not all
shipped in data. Performance, upgrade and rename fragility. → **ARC-005**, **CFG-004**.

### F-09 ⚠️ Zero tests on the automation spine
Nine crons and the completion fan-out run unattended against money and certificate
validity with no automated verification. → **QA-001..003**.

### F-10 Public feedback controller — acceptable, hardening advised
Token lookup via sudo is design-appropriate (uuid4, state check, CSRF on), but no token
expiry, no rate limiting, and the sudo record reaches the rendering context. → **SEC-004**.

### Minor (verified)
- Menus renamed "…-Business **Insurance**" — typo for *Assurance* (UX-004).
- Empty `stock.picking` extension with TODO; `stock`/`hr` dependencies apparently unused (ARC-006).
- `_review_notified_users` always includes `base.user_admin` (SEC-005).
- `NC_GRADE_RATING` duplicated in two files; scheme selection lists repeated 4× (ARC-007).
- Generated `standalone_blocks.xml` (2.5k lines) + JSON checklists depend on Word-form
  folders **outside the repo** (`../../ODOO_AUSTRIAN_CERT` etc.) — regeneration is not
  reproducible from a fresh clone (QA-004). A stray `tools/__pycache__` .pyc is committed.
- Dashboard shows only partner geography; name and manifest promise more than it does (UX-003).

## 6. What must NOT be rebuilt (working capital to preserve)

Per directive §9 ("never rebuild something merely because you have not inspected it"):
the certificate hard-guard; the reconciliation-hook trigger; the append-only register;
four-eyes dispatch; reviewer-independence constraint; the ATJF reset-on-change rule; the
migration discipline; the form/JSON rendering engine in `tuv_audit_reports` (unusual but
functioning and feeding ~27 regulatory PDFs); the `md.scheme` rule book (to be **wired in**,
not rewritten).

## 7. Assumptions requiring confirmation

| ID | Assumption | Evidence | Needed from owner |
|---|---|---|---|
| A-01 | Single legal company (TÜV Austria BIC Pakistan), single branch set (LHE/KHI/ISB as addresses only) | hard-coded addresses; no `company_id` discipline | confirm entity/branch model (ADR-003) |
| A-02 | Jurisdiction = Pakistan: FBR STI, NTN/CNIC/STRN, provincial sales tax | STI model, province tax map | confirm localization scope + FBR e-invoicing plans (ADR-006) |
| A-03 | Production DB exists and is upgraded from this repo (`migrations/` trail) | 19 migration scripts | confirm hosting, backup, envs (ADR-010) |
| A-04 | Accreditation bodies in scope: PNAC (primary), ESYD, SAAC | form sets and logos | confirm which are active |
| A-05 | Odoo edition: Enterprise vs Community | not determinable from repo | confirm (ADR-012) |
