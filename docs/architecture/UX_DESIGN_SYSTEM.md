# UI/UX Design System & Dashboard Architecture — TÜV Austria BIC

Status: **Proposed** (current-state items verified). Governing rules: blueprint §11.

## 1. Current state (verified)

- Backend apps renamed "…-Business **Insurance**" — typo for *Assurance* (**UX-004**, trivial fix).
- Project form is the operational cockpit: tabbed audit plan / execution / report /
  certificate-dispatch pages, per-tab form pickers and Print buttons; `document_preview`
  SCSS gives sale-document PDF previews in a popup ✅ (good pattern, keep).
- Shared project stages across all projects with stage-gated automation.
- Dashboard = client geography only (`res.partner`); no certification KPIs (**UX-001**).
- Public page: client feedback form on `web.frontend_layout` ✅.
- Auditor pickers show live "(Available)/(Not Available)" suffix ✅ (keep).
- ~27 regulatory PDFs with watermark support ✅.
- Accessibility/RTL: not addressed; English UI, Urdu not required (❓ confirm with owner).

## 2. Design principles for all new screens

1. Operationally calm: dense lists, clear status chips (the existing `flow_state` unified
   status bar on sale orders is the model to follow).
2. Every KPI drills down to the records behind it (blueprint §11.1); no "magic totals".
3. Exception-first: role homes lead with *what needs my action today*.
4. No new OWL app where a native list/kanban/pivot/graph view with a saved filter does the
   job (the current dashboard violates this — see UX-001 verdict in CAPABILITY_MATRIX §2).
5. Stage/state colors consistent across sale, project, NC, certificate.

## 3. Role command centres (proposed, in priority order)

| Role | Leads with (exceptions) | KPIs (all drill-down) |
|---|---|---|
| Planning Team | ATJFs to review; audits missing reports > 5 days; NCs near deadline; certificates awaiting prep | audits this month by state; auditor utilization (from task assignments); cycle time application→certificate |
| Finance / Tax Manager | unpaid invoices blocking certificates; STIs > 48 h; overdue > 7-day credit | AR aging; invoiced vs paid; STI issue lag |
| Certification Manager | feedback needing review (`needs_attention`); open improvement actions; suspended certificates | avg feedback score; NC closure rate; auditor bands |
| Technical Reviewer | reviews waiting on me | review turnaround; returns rate |
| Executive (CEO) | suspensions/withdrawals; register health; revenue vs plan | active certificates by standard/accreditation; pipeline (applications → contracts); client concentration (reuse existing geography widget here) |

Implementation path: phase 1 = native dashboards (graph/pivot actions + filters) per role
menu; phase 2 = one OWL command-centre app only if phase 1 proves insufficient (ADR-level
decision, not a default).

## 4. Form & list conventions

- Header: document number, status bar, primary action buttons only (secondary into gear menu).
- Linked-document breadcrumbs on every record in the chain: order ↔ project ↔ invoices ↔
  certificate ↔ register entry (smart buttons; several exist, complete the set — UX-005).
- Mandays sheet: replace free-text grid with computed fields + `md.scheme` lookup (joint
  FIN-002/ARC-001); show the rule-book basis inline ("ISO 9001 annex, band 26–45 → 4 MD").
- Empty states with next-step hints ("No ATJF yet — fill the planning tab and submit").
- Keep list views server-filtered by default to the user's active work, with saved filters
  for "all".

## 5. Notification hygiene

9 crons already create activities; add a digest policy (one daily digest per role instead
of per-record pings where volume is high — NCs, payment tracking) and ensure every activity
has a deep link + due date. (**UX-006**, low priority.)
