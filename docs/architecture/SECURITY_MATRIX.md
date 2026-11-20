# Security, Approval & Audit Framework — TÜV Austria BIC

**Project/company:** TÜV Austria BIC (single company assumed, A-01/D-02)
**Identity provider:** Odoo internal users (SSO/MFA: Unknown — ADR-009)
**Company scoping:** none today (no `ir.rule` in any module) ⚠️
**Audit retention owner:** To confirm
Template reference: `docs/architecture/SECURITY_MATRIX_TEMPLATE.md`.

## 1. As-built groups (verified)

| Group (category "TUV Austria") | Implies | De-facto role |
|---|---|---|
| Planning Team | project manager + project stages | runs the certification process; ATJF/NC/dispatch gates |
| Technical Reviewer | project user | 17021-1 reviews |
| Finance / Tax Manager | account invoicing + partner manager | STI issue; finance |
| Certificate Approver | project user | four-eyes certificate approval |
| Certification Manager | project user | feedback review, improvement actions |
| Certificate Register Viewer | internal user | read-only register (PNAC assessor) |

No hierarchy between custom groups; `base.group_system` bypasses every code-level check.

## 2. Access matrix — current vs target (R read, W write, C create, D delete, ✗ none; **bold = change required**)

| Object / operation | Sales | Planning | Tech. Reviewer | Finance/Tax | Cert. Approver | Cert. Manager | Reg. Viewer | Target change |
|---|---|---|---|---|---|---|---|---|
| Sale order (application/contract) | RWC own | R (locked for others while in review) | R | R | ✗ | ✗ | ✗ | — |
| **Approve/reject application review** | **RPC-callable today** ⚠️ | intended approver | ✗ | ✗ | ✗ | ✗ | ✗ | **SEC-001: server-side `has_group` + SoD: submitter ≠ approver** |
| ATJF approve | ✗ | ✓ (checked ✅) | ✗ | ✗ | ✗ | ✗ | ✗ | — |
| Audit checklist / evidence | ✗ | RWC | R | ✗ | ✗ | ✗ | ✗ | evidence D only pre-submission (code-guarded ✅, ACL allows D ⚠️) |
| **NC state** | ✗ | close (checked ✅) | R | ✗ | ✗ | ✗ | ✗ | **SEC-002: block direct state writes (all project users hold W)** |
| **Technical review state** | ✗ | R | W via buttons | ✗ | ✗ | ✗ | ✗ | **SEC-002 guard** |
| Commercial invoice (`account.move`) | ✗ | R | ✗ | per std `account` groups | ✗ | ✗ | ✗ | — |
| STI issue | ✗ | R | ✗ | ✓ (checked ✅) | ✗ | ✗ | ✗ | — |
| **Certificate prepare/confirm** | ✗ | ✓ (checked ✅) | ✗ | ✗ | approve only (four-eyes ✅) | ✗ | ✗ | **SEC-002: state-write guard** |
| Certificate register | ✗ | R | ✗ | R | R | R | R | append-only enforced in code ✅; **record rule once multi-company (SEC-003)** |
| Client feedback / performance | ✗ | R | ✗ | ✗ | ✗ | review ✓ | ✗ | — |
| Improvement actions | ✗ | W ⚠️ (all project users) | ✗ | ✗ | ✗ | ✓ | ✗ | tighten ACL (SEC-002) |
| Master data (EA codes, standards, clauses) | R | R ⚠️ (admin-only maintain) | R | R | R | R | R | decide maintainer group (CFG-005) |
| Annex lines/products | **full CRUD for every internal user** ⚠️ | | | | | | | tighten ACL (SEC-002) |

## 3. Confirmed findings and required controls

| ID | Finding (verified) | Required control | Blueprint ref |
|---|---|---|---|
| SEC-001 | `action_approve_review`/`action_reject_review`: no server-side group check; methods write via sudo; any internal user can self-approve over RPC | `has_group` guard + submitter≠approver SoD + test | §10.1 no silent self-approval |
| SEC-002 | Workflow `state` fields on NC, technical review, certificate, improvement action writable directly by groups with W | transition guards in `write()` (allowed-transition map + group check), keep button UX | §8 transition guards |
| SEC-003 | Zero record rules; `company_id` only on STI + surveillance reminder; global sequences | decision D-02 first; then company fields + rules on business models, company-scoped sequences | §4.3, §10.1 |
| SEC-004 | Public feedback controller: sudo write path OK (uuid4 token, state check, CSRF) but no token expiry, no rate limit | expiry (e.g. 90 days), per-IP throttle, don't pass sudo record to render context | §10.2 |
| SEC-005 | `_review_notified_users` always adds `base.user_admin` | remove; notify role group | §10.1 least privilege |
| SEC-006 | 71 `sudo()` calls (21 in `sale_order_review.py`) | audit each against §10.1; replace with explicit groups where possible | §17.1 |
| SEC-007 | Evidence/annex ACLs allow delete broadly (code guards only partially) | ACL tightening pass with regression tests | §10.1 default deny |

## 4. Audit-trail state

Good: `mail.thread` on 10 models, `tracking=True` on key states, chatter messages on
triggers, append-only register, dispatch four-eyes. Missing: audit events for **master-data
changes** (EA codes, standards, clauses, MD schemes), for ACL/group grants, and for the
public feedback writes (actor = sudo; log token + IP within privacy policy). → SEC-008.

## 5. Mandatory negative tests (gate for any security change)

Self-approval of own review (must fail after SEC-001); direct RPC state write on NC /
certificate / technical review (must fail after SEC-002); cross-company read of
certificate/register once D-02 enacted; feedback POST replay after answered state (already
blocked — add test); feedback token brute-force throttle; register write/unlink (already
raises — add test); non-planning NC closure; non-tax-manager STI issue; preparer approving
own certificate (already blocked — add test).
