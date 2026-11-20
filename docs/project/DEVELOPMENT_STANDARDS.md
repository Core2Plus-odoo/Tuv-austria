# Development Standards & Coding Conventions — TÜV Austria BIC

Status: **Proposed standard** — to be adopted for all further work on this repository.
Applies to: Odoo 19 (Community/Enterprise — edition to be confirmed, see Decision D-01).

## 4.1 Golden rules

1. **Standard first.** Before any new model, field or workflow: check standard Odoo 19
   (module or configuration), then OCA, then Studio, and only then custom code. Every
   custom addition must name the gap it closes in its PR description.
2. **No duplication of core.** Never re-implement invoicing, payments, attachments,
   approvals or messaging that `account`, `mail`, `documents` or `project` already provide.
   Extend via `_inherit`, not parallel models, unless a regulatory form genuinely has no
   standard counterpart.
3. **Single source of truth.** One master model per business concept. Cross-module links
   are real `Many2one`/`One2many` fields, never text references or duplicated columns.
4. **No fake completion.** A task is "done" only with: migration applied on a staging DB,
   tests passing, and the functional flow demonstrated end-to-end.

## 4.2 Repository and branching

| Rule | Standard |
|---|---|
| Default branch | `main` is the released state; it must never lag the production DB |
| Development | Feature branches `feature/<topic>`, fix branches `fix/<topic>` |
| Integration | Pull request into the integration branch; **no direct pushes** |
| Review | Minimum one reviewer; PR template with "standard-vs-custom" justification |
| Commits | Imperative subject ≤ 72 chars; body explains *why*; one logical change per commit |
| Versioning | Addon versions follow `19.0.x.y.z`; bump + migration script in the same PR |

> Current state (verified 2026-11-20): all 59 commits live on `Aug19`, `main` holds only
> the initial commit, and no PR or issue has ever been opened. Adopting the table above is
> backlog item B-01.

## 4.3 Python / Odoo conventions

- Follow the [OCA guidelines](https://github.com/OCA/odoo-community-association/blob/master/CONTRIBUTING.md) and Odoo's own coding standards.
- Model files: one business model per file, named after the model (`certificate.py` →
  `tuv.certificate`). Prefix all custom models `tuv.`.
- Every stateful model: `state` as `Selection` with explicit transitions in methods named
  `action_<verb>`; no state writes from views.
- Chatter: business documents inherit `mail.thread` + `mail.activity.mixin`; key fields get
  `tracking=True`.
- Access: no `sudo()` unless justified in a comment that names the attack surface it opens;
  public controllers (`auth='public'`) must validate a token and write through a minimal,
  explicit field whitelist.
- Translations: all user-visible strings wrapped; no hardcoded English in Python.
- No hardcoded company data (names, TRN/NTN numbers, logos, bank details, tax rates) in
  Python/XML — these belong in `res.company`, system parameters, or data records editable
  by functional users.
- Dates/amounts: use `fields.Date.context_today`, currency fields with `currency_id`;
  never float-compare without `float_compare`.

## 4.4 XML / views

- View IDs: `<model>_view_<type>` (e.g. `tuv_certificate_view_form`).
- Inherit standard views with targeted XPath; never copy a full standard view.
- Menus/actions in `views/menus.xml` per module; sequence gaps of 10.
- Report templates: one QWeb file per report, shared headers in a `common_templates.xml`.

## 4.5 Security artifacts (per module, mandatory)

- `security/<module>_groups.xml` — groups, with `implied_ids` chain documented.
- `security/ir.model.access.csv` — ACL for **every** model, including transient.
- Record rules for company/branch scoping on all business models (multi-company ready even
  if single company today).

## 4.6 Data & migrations

- `data/` files: `noupdate="1"` for sequences, mail templates users will edit, and master
  data loaded once; without it for layout/menu data the module owns.
- Every schema/data change that affects existing records ships a `migrations/<version>/`
  script (the existing 16-step migration trail in `tuv_austria_customization` is the right
  pattern — keep it).
- Demo data separated from production data; no client-identifiable records in the repo.

## 4.7 Definition of Done (quality gate, from the Master Directive §8)

A PR may merge only when:

1. Functional requirement in the PR description is satisfied and demonstrated.
2. ACLs/record rules updated for any new model.
3. At least one automated test covers the happy path and one edge case.
4. `odoo-bin -u <module> --test-enable` passes on a staging copy.
5. Linked documents (sale order ↔ project ↔ certificate ↔ invoice) still drill down.
6. No regression on the existing flows listed in `docs/architecture/PROCESS_LINKAGE_MATRIX.md`.
7. Documentation in `docs/` updated when the architecture or data model changed.
