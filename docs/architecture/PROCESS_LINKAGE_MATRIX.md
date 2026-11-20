# End-to-End Business Process Linkage Matrix — TÜV Austria BIC

The certification body's "lead-to-certificate-to-cash" cycle, step by step, with the
**verified implementation mechanism** and whether the link is real code or merely implied.
Verified at `Aug19` @ `9011b04`.

## 1. Application-to-certificate chain

| # | Step | Mechanism | Status |
|---|---|---|---|
| 1 | Client / auditor master data | `res.partner` ext.: `contact_type`, EA codes, standards, lead-auditor + availability flags | ✅ Real |
| 2 | Application captured | `sale.order.document_type=offer_application`, `TUV-` sequence (`tuv.austria.document`) | ✅ Real |
| 3 | Application review | `review_state draft→waiting_review→review_approved`; submit creates project + planning activities; order locked while waiting | ✅ Real (⚠️ SEC-001: approve/reject lacks server-side group check) |
| 4 | Proposal | `action_document_proposal_form` refused unless review approved | ✅ Real |
| 5 | Contract | contract `document_type` auto-confirms order + ensures project (`_handle_contract_document`) | ✅ Real |
| 6 | Man-day plan (ATJF) | `atjf_state draft→to_review→reviewed`; required-field check; auto-reset when any of 17 planning fields change; approval restricted to planning/admin | ✅ Real (⚠️ values free-text, F-05; `md.scheme` rule book not consulted, ARC-001) |
| 7 | Audit plan to client | ATJF approval auto-sends `mail_template_audit_plan`; manual resend button | ✅ Real |
| 8 | Audit execution | `audit_state not_started→in_progress→done`; start requires reviewed ATJF + standard + EA code + scope; loads clause checklist | ✅ Real |
| 9 | Audit completion fan-out | `action_audit_complete` override chain: NC sync · report activity (5-day) · auto commercial invoice (posted + emailed) · draft STI · payment tracking | ✅ Real (⚠️ F-01 double-billing path) |
| 10 | Evidence | report submission requires attendance + checklist + client-document categories; files locked after submission | ✅ Real |
| 11 | Audit report | `report_state draft→submitted`; due = completion + 5 days; lateness justification | ✅ Real |
| 12 | Nonconformities | NC/`%(year)s` numbering; open→submitted→closed; deadline 3 m (major) / 6 m (minor); closure planning-only; overdue cron; major-NC closure triggers certificate prep | ✅ Real |
| 13 | Technical review | TR/ numbering; 17021-1 checklist; reviewer-independence `@constrains`; return resets report | ✅ Real |
| 14 | Commercial invoice | posted `account.move`, fee from Summary of Cost, tax by province map, due +7 days, hourly cron safety net | ✅ Real (⚠️ F-01, CFG-001/003) |
| 15 | Sales tax invoice (FBR) | `tuv.sales.tax.invoice` STI/ numbering; Tax-Manager-only issue; NTN/CNIC + STRN required; 48-h SLA cron | ✅ Real |
| 16 | Payment tracking | `payment_status` computed from `account.move` residual; 7-day credit; hourly cron; stage `@constrains` blocks certificate stages until paid | ✅ Real |
| 17 | Payment → certificate | `account.move.line._reconcile_plan` override + hourly safety net + sudo-proof `create()` guard | ✅ Real |
| 18 | Certificate prepare→approve→print→dispatch | state chain; type from `md_audit_type`; 3-year cycle dates (12/24-month surveillance); number reuse on surveillance; four-eyes approval; PDF attachment; dispatch wizard (courier/email/in-person); first dispatch moves project to feedback stage | ✅ Real |
| 19 | Certificate register | append-only snapshot on approval; status valid/suspended/withdrawn/expired/superseded; daily completeness cron; supersede on recertification | ✅ Real |
| 20 | Surveillance reminder | daily cron, 3 months ahead of `next_surveillance_date`, unique per (entry, kind, date) | ✅ Real |
| 21 | Suspension / withdrawal | daily cron: surveillance 3 m overdue → suspension notice; grace (configurable days) → withdrawal; new certificate lifts suspensions | ✅ Real |
| 22 | Client feedback | entering flagged stage creates + emails feedback; public token form writes ratings; CM review | ✅ Real (SEC-004 hardening) |
| 23 | Auditor performance | records per job/role on feedback stage; refreshed on feedback submit; annual review cron writes competence back to partner | ✅ Real |
| 24 | Improvement actions | CA//IA/ numbering; verifier ≠ responsible; overdue cron | ✅ Real (creation from feedback is **manual button**; `source=auditor_performance` has no automation) |
| 25 | Management review | aggregation report over date range | ✅ Real (read-only) |

## 2. Links that are implied but NOT coded (gaps)

| Gap | Impact | Backlog |
|---|---|---|
| Next surveillance audit is **not** created as order/project — reminder only notifies | surveillance revenue and audits depend on manual re-entry; lifecycle traceability broken at the cycle boundary | **OPS-001** |
| Project stage progression beyond "Review Approved" is manual (`action_move_next_stage`); stages matched by name, most not shipped in data | fresh DB install breaks automations silently | **CFG-004** |
| Proposal/contract amounts typed by hand; order lines hidden | pricing not driven by catalog/man-day rules | **FIN-002 + ARC-001** |
| Execution checklist vs form checklists not synced | double data entry, divergent audit records | **ARC-002** |
| Improvement action from auditor performance | manual only | OPS-002 (low) |

## 3. Exception-path coverage (blueprint §8)

Covered today: NC overdue, STI overdue, payment overdue, report lateness justification,
suspension lift on new certificate, review return resets report, ATJF reset on change. ⚠️
Not covered (test + design in backlog): partial payment below 100 % with certificate
pressure, invoice cancellation/credit note after auto-invoice, duplicate feedback token
POST (idempotency is state-checked ✅ but unlogged), concurrent audit completion, order
cancellation after project creation, certificate revision after dispatch error.
