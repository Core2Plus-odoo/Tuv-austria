# AS-IS Capability Inventory & Standard-vs-Custom Analysis

**Scope ratings:** Existing / Partial / Missing / Out of scope (proposed) / Unknown
**Fit ratings (per blueprint §0):** Standard / Configure / Extend / Integrate / Defer
**Evidence:** branch `Aug19` @ `9011b04`. "Std Odoo" = native Odoo 19 capability.

## 1. ERP capability matrix

| Capability (blueprint §5) | Status | Evidence / gap | Recommended fit |
|---|---|---|---|
| PLT-01 Company & org structure | **Partial** | single company assumed; no record rules; branches = hard-coded addresses | Configure + Extend (SEC-003, CFG-002) |
| PLT-02 Identity, roles, approvals | **Partial** | 6 custom groups w/ Odoo 19 privileges; approval gaps F-02/F-03 | Extend (server-side guards) |
| PLT-03 Contacts & counterparties | **Existing** | `res.partner` extended: client/vendor/auditor types, EA codes, competence, availability | Keep (Extend) |
| PLT-04 Item/service catalog | **Existing** | `product.template` + service category, UoB, MD rates; ⚠️ name-based lookups, forced PKR/USD | Configure fixes (CFG-003) |
| PLT-05 Currency, tax, fiscal | **Partial** | std `account` taxes; ⚠️ province→tax map in code; multicurrency ad hoc (text "USD" labels) | Configure (fiscal positions) |
| PLT-06 Documents, audit trail | **Partial** | chatter+tracking on 10 models; evidence model w/ Binary files; no retention policy | Standard (`ir.attachment`) + Extend |
| PLT-07 Workflow, jobs, notifications | **Existing** | 9 crons, 8 mail templates, activities throughout | Keep; add tests (QA-001) |
| PLT-08 Data governance, sequences | **Partial** | sequences per document type but global (no company scope); no import framework | Configure |
| CRM-01 Leads/opportunities | **Missing** | sales start at `sale.order` application; std `crm` not installed/used | Standard (Defer until needed) |
| SLS-01 Quotation/orders | **Existing (custom-heavy)** | `document_type` flow application→review→proposal→contract; ~150 Word-template fields; amounts as Char (F-05) | Extend + FIN-002 refactor |
| SLS-02 Contracts/recurring | **Partial** | 3-year certification cycle fields on order; no `sale.subscription`; next cycle = manual new order | Extend (OPS-001 surveillance automation) |
| SLS-03 Returns/credit notes | **Missing** | no credit-note workflow for certification fees | Standard `account.move` reversal (Defer) |
| PUR-01/02 Procurement | **Missing** | no purchase usage | Standard when needed (Defer) |
| INV-01..03 Inventory | **Missing** | empty `stock.picking` stub + TODO | Remove dep or Defer (ARC-006) |
| FIN-01 GL & controls | **Standard** | native `account`; no custom posting logic ✅ | Keep Standard |
| FIN-02 AR & invoicing | **Partial** | auto commercial invoice posted on `account.move` ✅ but bypasses SO invoice status (F-01); STI satellite model for FBR numbering | Extend + FIN-001 fix |
| FIN-03 AP, bank reconciliation | **Partial** | payments/reconciliation standard ✅; no bank statement import configured (Unknown) | Standard/Configure |
| FIN-04 Budgets/assets | **Missing** | — | Defer |
| FIN-05 Intercompany | **Out of scope (proposed)** | single entity (A-01) | Defer |
| PRJ-01 Projects/timesheets | **Existing (as audit engine)** | `project.project` is the certification job object; shared stages; mandays sheet; `sale_timesheet` dep | Keep; ARC-005 slimming |
| SRV-01 Helpdesk/SLA | **Partial (domain-specific)** | NC deadlines, STI 48 h, report 5-day SLAs hard-coded | Extend → configurable (CFG-001) |
| SRV-02 Equipment/maintenance | **Out of scope (proposed)** | not a TIC need here | — |
| MFG-01 Manufacturing | **Out of scope (proposed)** | — | — |
| HRM-01 HR/attendance | **Missing (by design?)** | auditors are partners, not employees; `hr` dep only for menu rename | Decision D-06 |
| HRM-02 Payroll | **Out of scope (proposed)** | — | — |
| OMC-01 POS/e-commerce/portal | **Missing** | public feedback form only | Portal = Wave 5 candidate |
| BI-01 Reporting/command centres | **Partial** | client-portfolio dashboard (partners only); management-review aggregation report | Extend (UX-001/002) |
| AI-01 Governed AI | **Missing** | — | Defer (Wave 5) |
| VRT-01 Industry vertical (TIC/ISO 17021-1) | **Existing — the core asset** | full certification lifecycle incl. accreditation-body forms, MD rule book, register, notices | Keep & harden |

## 2. Standard-vs-custom verdicts on existing custom code

| Custom artifact | Standard Odoo alternative? | Verdict |
|---|---|---|
| Auto commercial invoice on `account.move` | native invoicing from SO lines | **Refactor**: bill through SO lines (deposit/milestone product) so `invoice_status` stays truthful — closes F-01 |
| `tuv.sales.tax.invoice` (no journal entries) | fields + sequence on `account.move` | **Justified as-is** for FBR STI numbering + Tax-Manager SoD + 48-h SLA; revisit only with FBR e-invoicing integration (ADR-006) |
| Payment→certificate trigger via `_reconcile_plan` | native hook usage | **Keep** ✅ clean use of standard mechanism |
| `tuv.audit.evidence` (Binary files) | `ir.attachment` / Documents app | **Partial refactor**: keep category-gating logic, store files as attachments (PLT-06) |
| NC + improvement actions | Enterprise Quality (alerts/CAPA) | **Keep custom**: ISO 17021-1 deadlines, certificate gate and feedback links justify it (and avoids Enterprise dependency uncertainty, D-01) |
| Sale review workflow | Approvals app (Enterprise) | **Keep custom** pending D-01; add server-side guard (SEC-001) |
| Form engine in `tuv_audit_reports` | Studio/attachments can't render these regulatory PDFs | **Keep**; document regeneration pipeline (QA-004) |
| `md.scheme` rule book | none (IAF MD-style annexes) | **Keep and finally integrate** (ARC-001) |
| Client-geography dashboard | std partner pivot/graph views | **Replace** within the command-centre work (UX-001): current OWL app duplicates what a pivot view gives, minus certification KPIs |
| Menu renames / view hiding (`ir_ui_*`) | debranding via config | **Keep, fix typo** (UX-004) |

## 3. Explicit out-of-scope proposals (need owner sign-off)

Procurement, inventory/valuation, manufacturing, payroll, POS/e-commerce, equipment
maintenance, intercompany/consolidation — none has code, data or a stated requirement
today. Declaring them out of scope (rather than "Unknown") keeps the roadmap honest;
reopen via change request.
