# Documentation Index — TÜV Austria BIC ERP

Governing standard: [`ERP_MASTER_BLUEPRINT.md`](ERP_MASTER_BLUEPRINT.md) (C2P pack v1.0)
+ root [`CLAUDE.md`](../CLAUDE.md). Kickoff reference: [`START_HERE_PROMPT.md`](START_HERE_PROMPT.md).

Every document marks content as **verified** (code evidence, branch `Aug19` @ `9011b04`),
**proposed**, **assumption**, or **decision requiring approval**.

## Project (docs/project/)
| Doc | Content |
|---|---|
| [CURRENT_SYSTEM_AUDIT.md](project/CURRENT_SYSTEM_AUDIT.md) | Technical & functional audit; ranked findings F-01..F-10; assumptions A-01..A-05 |
| [CAPABILITY_MATRIX.md](project/CAPABILITY_MATRIX.md) | AS-IS ERP capability inventory; standard-vs-custom verdicts |
| [PROJECT_CHARTER.md](project/PROJECT_CHARTER.md) | Draft charter — "To confirm" fields need the owner |
| [DECISION_REGISTER.md](project/DECISION_REGISTER.md) | ADR-001..012 status + Gate-0 decisions D-01..D-10 |
| [ROADMAP_AND_BACKLOG.md](project/ROADMAP_AND_BACKLOG.md) | Waves H/1–5, prioritized backlog w/ acceptance criteria, 30/60/90 conditional milestones, first-sprint spec |
| [DEVELOPMENT_STANDARDS.md](project/DEVELOPMENT_STANDARDS.md) | Coding conventions, branching, Definition of Done |

## Architecture (docs/architecture/)
| Doc | Content |
|---|---|
| [MODULE_DEPENDENCY_MAP.md](architecture/MODULE_DEPENDENCY_MAP.md) | As-built module graph + integration touchpoints |
| [ENTITY_RELATIONSHIPS.md](architecture/ENTITY_RELATIONSHIPS.md) | As-built ERD, enforced invariants, integrity gaps |
| [PROCESS_LINKAGE_MATRIX.md](architecture/PROCESS_LINKAGE_MATRIX.md) | 25-step application→certificate→cash chain: real vs implied |
| [SECURITY_MATRIX.md](architecture/SECURITY_MATRIX.md) | Groups, access matrix current→target, SEC findings, negative tests |
| [UX_DESIGN_SYSTEM.md](architecture/UX_DESIGN_SYSTEM.md) | UX principles, role command centres, form conventions |
| SECURITY_MATRIX_TEMPLATE.md / ACCOUNTING_POSTING_RULES_TEMPLATE.md | pack templates |

## Quality (docs/quality/)
[TEST_STRATEGY.md](quality/TEST_STRATEGY.md) · [RELEASE_GATE_CHECKLIST.md](quality/RELEASE_GATE_CHECKLIST.md)

## Modules (docs/modules/)
One `MODULE_SPEC_<ID>.md` per approved backlog item (template in docs/templates/). None yet —
first will be SEC-001 and FIN-001 after Gate-0 approval.

## Templates (docs/templates/)
Pack-supplied templates incl. generic MODULE_DEPENDENCY_MAP / ENTITY_RELATIONSHIPS
reference diagrams, ADR, module spec, integration contract, data dictionary, requirements
register, migration reconciliation, test/UAT.
