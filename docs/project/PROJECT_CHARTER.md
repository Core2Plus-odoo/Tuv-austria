# Project Charter — TÜV Austria BIC Certification ERP

**Status: DRAFT — every "To confirm" needs the business owner.** Template:
`docs/templates/PROJECT_CHARTER_TEMPLATE.md`; required by blueprint §2 before new scope.

| Field | Value | Source |
|---|---|---|
| Client / product | TÜV Austria BIC (Bureau of Inspection & Certification) — management-system certification ERP | code evidence |
| Sponsor / sign-off parties | **To confirm** | — |
| Legal entities | 1 assumed (A-01); branches Lahore / Karachi / Islamabad as addresses | hard-coded report data |
| Country / tax jurisdictions | Pakistan: FBR (NTN/CNIC/STRN, STI), provincial sales taxes incl. Punjab exemption wording | STI model, tax map |
| Industry / vertical | TIC — ISO/IEC 17021-1 certification body; accreditation: PNAC (primary), ESYD, SAAC (A-04) | form sets |
| Certification schemes | ISO 9001, 14001, 45001, 27001/27701, 22000/FSSC, 13485, 20000-1, 37301, 50001 (+ EN 15343 annex) | checklists, MD annexes |
| Platform | Odoo 19; edition **To confirm** (D-01) | manifests |
| Hosting / environments / backups | **To confirm** (ADR-010) | — |
| Current systems / migration history | live DB upgraded in place via `migrations/` (1.1→1.16); Word forms previously manual | migration scripts, module descriptions |
| Users / roles / scale | 6 custom roles defined; user counts **To confirm** | security files |
| Integrations | SMTP; public feedback form. FBR e-invoicing **To confirm** (D-05) | code |
| In-scope modules | certification lifecycle (see CAPABILITY_MATRIX) | code |
| Proposed out of scope | procurement, inventory, manufacturing, payroll, POS/e-commerce, intercompany — **ratify** | CAPABILITY_MATRIX §3 |
| Timeline / budget / risk tolerance | **To confirm** | — |
| Success measures | suggested: application→certificate cycle time; % certificates blocked on payment; NC closure within deadline; STI 48-h compliance; surveillance performed on time; feedback score — baselines **To confirm**, do not invent (blueprint §1.1) | — |
