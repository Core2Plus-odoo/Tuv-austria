from odoo import Command, api, fields, models

# The rows of the audit schedule of form FM-TAGMBH-MSZ-002_Auditplan-ISMS-EN (revision
# 07/20.05.2025), taken from the Word form. Notation of `content` (see _ap_schedule_blocks):
# first line bold, "- " a bullet, "[blue]" / "[red]" a coloured bold heading.
ISMS_SCHEDULE = [
    {'content': 'Location address', 'is_section': True},
    {'content': 'Opening meeting\n- Introduction of all participants\n- Confirmation of the audit plan'},
    {'content': 'Stage 1 audit\n- Verification of documents\n- 4. Context of the organization\n- 5. Leadership\n- 6. Planning\n- 7. Support\n- 8. Operation\n- 9. Performance evaluation\n- 10. Improvement'},
    {'content': 'Break'},
    {'content': 'Implementation of controls from Annex A'},
    {'content': 'Closing meeting\n- Presentation of audit findings\n- Discussion'},
    {'content': 'End of audit stage 1'},
    {'content': 'Location address', 'is_section': True},
    {'content': 'Opening meeting\n- Introduction of all participants\n- Confirmation of the audit plan'},
    {'content': 'Open issues from the stage 1 audit\n- Clarification of open topics'},
    {'content': 'Open issues from previous audits\n- Clarification of open topics'},
    {'content': 'Changes of certification scope\n- Clarification of scope changes'},
    {'content': '4. Context of the organization\n- 4.1 Context of the organization\n- 4.2 Interested parties\n- 4.3 Application area / Scope\n- 4.4 Information security management processes\n[blue]ISO 27701 Requirements\n- 5.2 Context / Scope'},
    {'content': '5. Leadership\n- 5.1 Leadership and commitment\n- 5.2 Policy\n- 5.3 Organizational roles, responsibilities, and authorities'},
    {'content': '6. Planning\n- 6.1 Actions to address risks and opportunities\n- 6.1.3 SoA\n- 6.2 Information security objectives and planning to achieve them\n- 6.3 Planning of changes\n[blue]ISO 27701 Requirements\n- 5.4.1.2 Integration into risk management\n- 5.4.1.3 Extension of SoA'},
    {'content': '7. Support\n- 7.1 Resources\n- 7.2 Competence\n- 7.3 Awareness\n- 7.4 Communication\n- 7.5 Documented Information'},
    {'content': '8. Operation\n- 8.1 Operational planning and control\n- 8.2 Information security risk assessment\n- 8.3 Information security risk treatment'},
    {'content': '9. Performance evaluation\n- 9.1 Monitoring, measurement, analysis, and evaluation\n- 9.2 Internal audit\n- 9.3 Management review'},
    {'content': '10. Improvement\n- 10.1 Continual improvement\n- 10.2 Nonconformity and corrective action'},
    {'content': '[red]ISO 9001, 8. Operation\n- 8.1 Operational planning and control\n- 8.2 Requirements for products and services\n- 8.3 Design and development of products and services\n- 8.4 Control of externally provided processes, products, and services\n- 8.5 Production and service provision\n- 8.6 Release of products and services\n- 8.7 Control of nonconforming outputs'},
    {'content': 'Information security management\n- 4. Context of the organization\n- 5. Leadership\n- 7. Support\n- 9. Performance evaluation\n- 10. Improvement\n[blue]ISO 27701 Requirements\n- 5.2 Context / Scope'},
    {'content': 'Break'},
    {'content': 'Risk management\n- 6.1 Actions to address risks and opportunities\n- 6.1.3 SoA\n- 6.2 Information security objectives and planning to achieve them\n- 6.3 Planning of changes\n- 8.1 Operational planning and control\n- 8.2 Information security risk assessment\n- 8.3 Information security risk treatment\n[blue]ISO 27701 Requirements\n- 5.4.1.2 Integration into risk management\n- 5.4.1.3 Extension of SoA'},
    {'content': 'Feedback of audit day 1'},
    {'content': 'End of audit day 1'},
    {'content': 'Location address', 'is_section': True},
    {'content': 'Opening meeting\n- Confirmation of the audit plan'},
    {'content': '#05. Organizational information security\n- A.5.1 Policies for information security\n- A.5.2 Information security roles and responsibilities\n- A.5.3 Segregation of duties\n- A.5.4 Management responsibilities\n- A.5.5 Contact with authorities\n- A.5.6 Contact with special interest groups\n- A.5.7 Threat intelligence\n- A.5.8 Information security in project management'},
    {'content': '#06. Configuration- and data management\n- A.8.9 Configuration management\n- A.8.10 Information deletion\n- A.8.11 Data masking\n- A.8.12 Data leakage prevention'},
    {'content': '#07. Human resource security\n- A.6.1 Screening\n- A.6.2 Terms and conditions of employment\n- A.6.3 Information security awareness, education, and training\n- A.6.4 Disciplinary process\n- A.6.5 Responsibilities after termination or change of employment\n- A.6.6 Confidentiality or non-disclosure agreements\n- A.6.7 Remote working'},
    {'content': '#08. Asset management\n- A.5.9 Inventory of information and other associated assets\n- A.5.10 Acceptable use of information and other associated assets\n- A.5.11 Return of assets\n- A.5.12 Classification of information\n- A.5.13 Labelling of information\n- A.7.10 Storage media\n- A.7.14 Secure disposal or re-use of equipment'},
    {'content': '#09. Access control\n- A.5.15 Access control\n- A.5.16 Identity management\n- A.5.17 Authentication information\n- A.5.18 Access rights\n- A.8.2 Privileged access rights\n- A.8.3 Information access restriction\n- A.8.5 Secure authentication'},
    {'content': '#10. Devices and equipment\n- A.7.8 Equipment siting and protection\n- A.7.9 Security of assets off-premises\n- A.7.11 Supporting utilities\n- A.7.12 Cabling security\n- A.7.13 Equipment maintenance'},
    {'content': '#11. Physical security\n- Introduction and visit of the data center\n- Inspection of site security measures\n- A.7.1 Physical security perimeters\n- A.7.2 Physical entry\n- A.7.3 Securing offices, rooms, and facilities\n- A.7.4 Physical security monitoring\n- A.7.5 Protecting against physical and environmental threats\n- A.7.6 Working in secure areas\n- A.7.7 Clear desk and clear screen'},
    {'content': 'Break'},
    {'content': '#12. IT operation\n- A.5.37 Documented operating procedures\n- A.8.1 User end point devices\n- A.8.6 Capacity management\n- A.8.7 Protection against malware\n- A.8.8 Management of technical vulnerabilities\n- A.8.13 Information backup\n- A.8.15 Logging\n- A.8.16 Monitoring activities\n- A.8.17 Clock synchronization\n- A.8.18 Use of privileged utility programs\n- A.8.19 Installation of software on operational systems\n- A.8.34 Protection of information systems during audit testing'},
    {'content': '#13. Network security\n- A.8.20 Networks security\n- A.8.21 Security of network services\n- A.8.22 Segregation of networks\n- A.8.23 Web filtering\n- A.8.24 Use of cryptography'},
    {'content': '#14. Development\n- A.8.25 Secure development life cycle\n- A.8.26 Application security requirements\n- A.8.27 Secure system architecture and engineering principles\n- A.8.28 Secure coding\n- A.8.4 Access to source code\n- A.8.29 Security testing in development and acceptance\n- A.8.30 Outsourced development\n- A.8.31 Separation of development, test, and production environments\n- A.8.32 Change management\n- A.8.33 Test information'},
    {'content': '#15. Customers and suppliers\n- A.5.14 Information transfer\n- A.5.19 Information security in supplier relationships\n- A.5.20 Addressing information security within supplier agreements\n- A.5.21 Managing information security in the information and communication technology (ICT) supply chain\n- A.5.22 Monitoring, review and change management of supplier services\n- A.5.23 Information security for use of cloud services'},
    {'content': 'Feedback of audit day 2'},
    {'content': 'End of audit day 2'},
    {'content': 'Location address', 'is_section': True},
    {'content': 'Opening meeting\n- Confirmation of the audit plan'},
    {'content': '#16. Information security incidents\n- A.6.8 Information security event reporting\n- A.5.24 Information security incident management planning and preparation\n- A.5.25 Assessment and decision on information security events\n- A.5.26 Response to information security incidents\n- A.5.27 Learning from information security incidents\n- A.5.28 Collection of evidence'},
    {'content': '#17. Business continuity\n- A.5.29 Information security during disruption\n- A.5.30 ICT readiness for business continuity\n- A.8.14 Redundancy of information processing facilities'},
    {'content': '#18. Compliance\n- A.5.31 Legal, statutory, regulatory, and contractual requirements\n- A.5.32 Intellectual property rights\n- A.5.33 Protection of records\n- A.5.34 Privacy and protection of personal identifiable information (PII)\n- A.5.35 Independent review of information security\n- A.5.36 Compliance with policies, rules, and standards for information security'},
    {'content': 'Break'},
    {'content': '[blue]ISO 27701 Annex A\n[blue]PIMS-specific reference control objectives and controls (PII Controllers)\n- A.7.2 Conditions for collection and processing\n- A.7.3 Obligations to PII principals\n- A.7.4 Privacy by design and privacy by default\n- A.7.5 PII sharing, transfer and disclosure'},
    {'content': '[blue]ISO 27701 Annex B\n[blue]PIMS-specific reference control objectives and controls (PII Processors)\n- B.8.2 Conditions for collection and processing\n- B.8.3 Obligations to PII principals\n- B.8.4 Privacy by design and privacy by default\n- B.8.5 PII sharing, transfer and disclosure'},
    {'content': 'Clarification of open issues\n- Discussion of open questions'},
    {'content': 'Preparation of audit conclusions\n- Review and adjustment of findings'},
    {'content': 'Coordination of the auditors'},
    {'content': 'Closing meeting\n- Presentation of audit findings\n- Discussion'},
    {'content': 'End of audit'},
]


def isms_schedule_commands():
    return [Command.create(dict(vals, sequence=10 * (i + 1), schedule_kind='isms'))
            for i, vals in enumerate(ISMS_SCHEDULE)]


class AuditPlanIsmsMixin(models.AbstractModel):
    """Audit plan ISMS, form FM-TAGMBH-MSZ-002, past its sections 1 and 2: the ISO 27001 /
    27701 audit schedule (ip_schedule_line_ids, declared by each model), signatures and the
    significant issues. Own fields (ip_), so it can sit next to the standard audit plan."""

    _name = 'tuv.audit.plan.isms.mixin'
    _description = 'Audit Plan ISMS Fields'

    ip_sign_place = fields.Char(string='Place')
    ip_sign_date = fields.Date(string='Date')
    ip_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    ip_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)
    ip_significant_issues = fields.Text(string='Significant Issues Impacting on the Audit Program',
                                        default='None.')


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.audit.plan.isms.mixin']

    ip_schedule_line_ids = fields.One2many('tuv.audit.plan.schedule', 'plan_id',
                                           string='Audit Schedule (ISMS)', copy=True,
                                           domain=[('schedule_kind', '=', 'isms')],
                                           context={'default_schedule_kind': 'isms'})

    def _tuv_fill_isms_schedule(self):
        """Called from data: give the predefined ISMS form the rows of the Word form once."""
        for plan in self:
            if not plan.ip_schedule_line_ids:
                plan.ip_schedule_line_ids = isms_schedule_commands()


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.audit.plan.isms.mixin']

    ip_schedule_line_ids = fields.One2many(
        'tuv.audit.plan.schedule', 'project_id', string='Audit Schedule (ISMS)',
        domain=[('schedule_kind', '=', 'isms')], context={'default_schedule_kind': 'isms'},
        compute='_compute_ip_schedule_line_ids', store=True, readonly=False)

    @api.depends('audit_report_id')
    def _compute_ip_schedule_line_ids(self):
        # the rows of the Word form, added once the ISMS plan is picked; edits are kept
        for project in self:
            if not project.ip_schedule_line_ids and project.audit_report_key == 'audit_plan_isms':
                project.ip_schedule_line_ids = isms_schedule_commands()
