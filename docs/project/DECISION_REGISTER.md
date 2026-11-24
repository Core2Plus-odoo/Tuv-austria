# Decision Register — TÜV Austria BIC ERP

Format per `docs/templates/ADR_TEMPLATE.md`; blueprint §2 mandates ADR-001..012.
**Status values:** Decided / Proposed (needs owner approval) / Open (needs information).

## Blueprint-mandated ADRs

| ADR | Decision | Status | Current position & evidence |
|---|---|---|---|
| ADR-001 | Platform | **Decided (by evidence)** | Odoo-based ERP: 5 addons on Odoo 19, live migration trail. No rebuild. |
| ADR-002 | Tenant model | **Decided (by evidence)** | Single database, single tenant. |
| ADR-003 | Company/branch model | **Open (D-02)** | Single company assumed (A-01). Branch offices (LHE/KHI/ISB) are report addresses only. Owner must confirm before SEC-003 record-rule work is scoped. |
| ADR-004 | Financial source of truth | **Decided (by evidence)** | Native `account` is the ledger ✅. STI is a numbering/compliance satellite, posts nothing. Keep. |
| ADR-005 | Inventory valuation | **Proposed: out of scope** | No stock usage (empty stub). Remove dep (ARC-006) unless a requirement exists. |
| ADR-006 | Localization | **Open (D-05)** | Pakistan: provincial sales tax hard-coded in Python; FBR STI manual. Decide: move taxes to fiscal positions (Configure) and whether/when FBR digital-invoicing integration is required. |
| ADR-007 | Workflow/approval engine | **Proposed** | Keep custom state machines; add server-side guards (SEC-001/002). Do not adopt Enterprise Approvals until D-01 resolved. |
| ADR-008 | Integration strategy | **Proposed** | No integrations today beyond SMTP + public form. Every future one via `docs/templates/INTEGRATION_CONTRACT_TEMPLATE.md`. |
| ADR-009 | Security & identity | **Open** | Internal users only; SSO/MFA posture unknown. Must be answered by IT owner. |
| ADR-010 | Deployment & DR | **Open (D-03)** | Hosting, environments, backup/restore evidence unknown — repo has no deployment config. Blocking for CI design (QA-002). |
| ADR-011 | Close/correction policy | **Proposed** | Posted invoices corrected only by credit note/reversal; certificates by revision/supersede (register pattern exists ✅). Needs accountant sign-off. |
| ADR-012 | Odoo version/edition | **Open (D-01)** | Odoo 19 confirmed by OCA manifest + v19 idioms (`res.groups.privilege`, `models.Constraint`). **Edition (Community/Enterprise) unconfirmed** — determines Studio/Approvals/Quality/Documents availability. |

## Gate-0 project decisions requiring owner approval

| ID | Decision needed | Why it blocks | Recommendation |
|---|---|---|---|
| D-01 | Odoo edition + hosting (= ADR-012 + ADR-010) | CI runner image, test strategy, app choices | confirm from production instance |
| D-02 | Multi-company / external-viewer scope (= ADR-003) | scope of SEC-003 record rules & sequence scoping | if single company stays: minimal company fields + rules only on viewer-exposed models |
| D-03 | Branch protection + merge `Aug19`→`main` process | everything ships from an unreviewed branch today | PR-gated `main`, `Aug19` retired after merge (B-01) |
| D-04 | Approve FIN-001 invoicing refactor (bill via SO lines) | changes an automated financial flow in production | yes, with migration + reconciliation report |
| D-05 | FBR e-invoicing scope & provincial-tax configuration (= ADR-006) | tax engineering approach | move mapping to fiscal positions now; FBR connector as separate ADR when mandated |
| D-06 | Auditors: stay `res.partner` or adopt `hr.employee` | competence/annual-review data model; `hr` dep | keep partners (works, simpler); drop unused `hr` dep |
| D-07 | SoD policy for application review (submitter ≠ approver?) | SEC-001 implementation detail | yes — enforce |
| D-08 | Approve FIN-002/ARC-001 man-days & money typing refactor | wide migration touching live text data | phased: new typed fields + parallel run + cutover migration |
| D-09 | AGPL-3 OCA module alongside LGPL-3 addons | license/compliance posture of the repo | keep OCA module vendored as-is (its license permits use); track upstream updates; get legal nod |
| D-10 | Evidence storage: Binary fields → `ir.attachment` | affects backups/filestore sizing | migrate (PLT-06) in hardening wave |

## Project decision log (running)

| Date | Decision | By | Note |
|---|---|---|---|
| 2026-11-20 | Blueprint pack v1.0 installed as governing standard; deliverable set drafted against `Aug19` | Claude (proposed) → owner to ratify | this PR |
