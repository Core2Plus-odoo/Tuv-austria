from odoo import Command, api, fields, models

# Audit plans of the accreditation bodies ESYD, PNAC and SAAC. Sections 1 and 2 reuse the
# ap_* fields of tuv.audit.info.mixin (models/audit_plan.py); each plan adds its own fields:
#   eap_   ESYD  FM-BA-ZET-MS-All-008-AP-EN (revision 00)
#   pap_   PNAC  "1. Audit Plan" (TUV/BA/FM/04-1, revision 10)
#   sap_   SAAC  FM-BA-ZET-MS-All-008-AP-Audit_plan_EN (revision 04/26.07.2024)
#   sapi_  SAAC  FM-BA-ZET-MS-All-008a-AP-Audit_plan_27001_EN (revision 04/16.01.2024)
# ESYD and PNAC keep the older schedule (Date / Time | Department | Representative |
# Processes | Auditors) and a participants list; SAAC uses the TUV schedule columns.

# Blank rows of the Word forms; the PDF fills up to these with empty rows.
ESYD_SCHEDULE_ROWS = 6
PNAC_SCHEDULE_ROWS = 9
PARTICIPANT_ROWS = 7

PNAC_AUDIT_OBJECTIVES = 'Verify the Documentation/implementation of the requirements for scope of work'
PNAC_AUDIT_CRITERIA = (
    'Requirements of applicable standard(s) including requirements of ISO 9001, ISO 14001 & '
    'ISO 45001 & ISO 22000\n'
    'Management System Requirements of the organization\n'
    'Applicable legal and other requirements')

# Fixed rows of the SAAC audit plan schedule (empty rows are the blank lines of the Word form).
SAAC_SCHEDULE = [
    {'content': 'Location address', 'is_section': True},
    {'content': 'Opening meeting Introduction of all participants, Confirmation of the audit plan'},
    {'content': ''},
    {'content': ''},
    {'content': ''},
    {'content': 'Break'},
    {'content': ''},
    {'content': ''},
    {'content': ''},
    {'content': 'Coordination of the auditors, Clarification of open issues'},
    {'content': 'Closing meeting, Presentation of audit findings, Discussion'},
    {'content': 'End of audit'},
]

# Rows of the SAAC ISO 27001 audit plan, taken from the Word form. Notation of `content`
# (see _sap_schedule_blocks): first line bold, "- " a bullet, "[blue]" / "[red]" colours a
# heading or a bullet (the new ISO 27001:2022 controls are red), "[note]" a centred line on
# yellow (the hint row the auditor deletes), a heading "Optional: ..." prints "Optional:" on yellow.
SAAC_27001_SCHEDULE = [
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
    {'content': '6. Planning\n- 6.1 Actions to address risks and opportunities\n- 6.1.3 SoA\n- 6.2 Information security objectives and planning to achieve them\n- [red]6.3 Planning of changes\n[blue]ISO 27701 Requirements\n- 5.4.1.2 Integration into risk management\n- 5.4.1.3 Extension of SoA'},
    {'content': '7. Support\n- 7.1 Resources\n- 7.2 Competence\n- 7.3 Awareness\n- 7.4 Communication\n- 7.5 Documented Information'},
    {'content': '8. Operation\n- 8.1 Operational planning and control\n- 8.2 Information security risk assessment\n- 8.3 Information security risk treatment'},
    {'content': '[red]ISO 9001, 8. Operation\n- 8.1 Operational planning and control\n- 8.2 Requirements for products and services\n- 8.3 Design and development of products and services\n- 8.4 Control of externally provided processes, products, and services\n- 8.5 Production and service provision\n- 8.6 Release of products and services\n- 8.7 Control of nonconforming outputs'},
    {'content': '9. Performance evaluation\n- 9.1 Monitoring, measurement, analysis, and evaluation\n- 9.2 Internal audit\n- 9.3 Management review'},
    {'content': '10. Improvement\n- 10.1 Continual improvement\n- 10.2 Nonconformity and corrective action'},
    {'content': 'Optional: Information security management\n- 4. Context of the organization\n- 5. Leadership\n- 7. Support\n- 9. Performance evaluation\n- 10. Improvement\n[blue]ISO 27701 Requirements\n- 5.2 Context / Scope'},
    {'content': 'Optional: Risk management\n- 6.1 Actions to address risks and opportunities\n- 6.1.3 SoA\n- 6.2 Information security objectives and planning to achieve them\n- [red]6.3 Planning of changes\n- 8.1 Operational planning and control\n- 8.2 Information security risk assessment\n- 8.3 Information security risk treatment\n[blue]ISO 27701 Requirements\n- 5.4.1.2 Integration into risk management\n- 5.4.1.3 Extension of SoA'},
    {'content': 'Break'},
    {'content': 'A.5 Information security policies\n- A.5.1 Management direction for information security'},
    {'content': 'A.6 Organization of information security\n- A.6.1 Internal organization\n- A.6.2 Mobile devices and teleworking'},
    {'content': 'A.7 Human resource security\n- A.7.1 Prior to employment\n- A.7.2 During employment\n- A.7.3 Termination and change of employment'},
    {'content': 'A.8 Asset management\n- A.8.1 Responsibility for assets\n- A.8.2 Information classification\n- A.8.3 Media handling'},
    {'content': 'A.9 Access control\n- A.9.1 Business requirements of access control\n- A.9.2 User access management\n- A.9.3 User responsibilities\n- A.9.4 System and application access control'},
    {'content': 'A.10 Cryptography\n- A.10.1 Cryptographic controls'},
    {'content': 'A.11 Physical and environmental security\n- Introduction and visit of the data center\n- Inspection of site security measures\n- A.11.1 Secure areas\n- A.11.2 Equipment'},
    {'content': 'A.12 Operations security\n- A.12.1 Operational procedures and responsibilities\n- A.12.2 Protection from malware\n- A.12.3 Backup\n- A.12.4 Logging and monitoring\n- A.12.5 Control of operational software\n- A.12.6 Technical vulnerability management\n- A.12.7 Information systems audit considerations'},
    {'content': 'A.13 Communications security\n- A.13.1 Network security management\n- A.13.2 Information transfer'},
    {'content': 'A.14 System acquisition, development, and maintenance\n- A.14.1 Security requirements of information systems\n- A.14.2 Security in development and support processes\n- A.14.3 Test data'},
    {'content': 'A.15 Supplier relationships\n- A.15.1 Information security in supplier relationships\n- A.15.2 Supplier service delivery management'},
    {'content': 'A.16 Information security incident management\n- A.16.1 Management of information security incidents and improvements'},
    {'content': 'A.17 Information security aspects of business continuity management\n- A.17.1 Information security continuity\n- A.17.2 Redundancies'},
    {'content': 'A.18 Compliance\n- A.18.1 Compliance with legal and contractual requirements\n- A.18.2 Information security reviews'},
    {'content': '[note]From here on requirements of Annex A of ISO 27001:2022\n[note]New requirements are marked in RED\n[note](This line is to be DELETED)'},
    {'content': 'Organizational information security\n- A.5.1 Policies for information security\n- A.5.2 Information security roles and responsibilities\n- A.5.3 Segregation of duties\n- A.5.4 Management responsibilities\n- A.5.5 Contact with authorities\n- A.5.6 Contact with special interest groups\n- [red]A.5.7 Threat intelligence\n- A.5.8 Information security in project management'},
    {'content': 'Asset management\n- A.5.9 Inventory of information and other associated assets\n- A.5.10 Acceptable use of information and other associated assets\n- A.5.11 Return of assets\n- A.5.12 Classification of information\n- A.5.13 Labelling of information\n- A.7.10 Storage media\n- A.7.14 Secure disposal or re-use of equipment'},
    {'content': 'Customers and suppliers\n- A.5.14 Information transfer\n- A.5.19 Information security in supplier relationships\n- A.5.20 Addressing information security within supplier agreements\n- A.5.21 Managing information security in the information and communication technology (ICT) supply chain\n- A.5.22 Monitoring, review and change management of supplier services\n- [red]A.5.23 Information security for use of cloud services\n- A.6.6 Confidentiality or non-disclosure agreements'},
    {'content': 'Access control\n- A.5.15 Access control\n- A.5.16 Identity management\n- A.5.17 Authentication information\n- A.5.18 Access rights\n- A.8.2 Privileged access rights\n- A.8.3 Information access restriction\n- A.8.4 Access to source code\n- A.8.5 Secure authentication'},
    {'content': 'Information security incidents\n- A.6.8 Information security event reporting\n- A.5.24 Information security incident management planning and preparation\n- A.5.25 Assessment and decision on information security events\n- A.5.26 Response to information security incidents\n- A.5.27 Learning from information security incidents\n- A.5.28 Collection of evidence'},
    {'content': 'Business continuity\n- A.5.29 Information security during disruption\n- [red]A.5.30 ICT readiness for business continuity'},
    {'content': 'Compliance\n- A.5.31 Legal, statutory, regulatory, and contractual requirements\n- A.5.32 Intellectual property rights\n- A.5.33 Protection of records\n- A.5.34 Privacy and protection of personal identifiable information (PII)\n- A.5.35 Independent review of information security\n- A.5.36 Compliance with policies, rules, and standards for information security'},
    {'content': 'Human resource security\n- A.6.1 Screening\n- A.6.2 Terms and conditions of employment\n- A.6.3 Information security awareness, education, and training\n- A.6.4 Disciplinary process\n- A.6.5 Responsibilities after termination or change of employment\n- A.6.7 Remote working'},
    {'content': 'Physical security\n- Introduction and visit of the data center\n- Inspection of site security measures\n- A.7.1 Physical security perimeters\n- A.7.2 Physical entry\n- A.7.3 Securing offices, rooms, and facilities\n- [red]A.7.4 Physical security monitoring\n- A.7.5 Protecting against physical and environmental threats\n- A.7.6 Working in secure areas\n- A.7.7 Clear desk and clear screen'},
    {'content': 'Devices and equipment\n- A.7.8 Equipment siting and protection\n- A.7.9 Security of assets off-premises\n- A.7.11 Supporting utilities\n- A.7.12 Cabling security\n- A.7.13 Equipment maintenance'},
    {'content': 'IT operation\n- A.5.37 Documented operating procedures\n- A.8.1 User end point devices\n- A.8.6 Capacity management\n- A.8.7 Protection against malware\n- A.8.8 Management of technical vulnerabilities\n- A.8.19 Installation of software on operational systems\n- A.8.34 Protection of information systems during audit testing'},
    {'content': 'Configuration- and data management\n- [red]A.8.9 Configuration management\n- [red]A.8.10 Information deletion\n- [red]A.8.11 Data masking\n- [red]A.8.12 Data leakage prevention'},
    {'content': 'Backup, logging, monitoring\n- A.8.13 Information backup\n- A.8.14 Redundancy of information processing facilities\n- A.8.15 Logging\n- [red]A.8.16 Monitoring activities\n- A.8.17 Clock synchronization\n- A.8.18 Use of privileged utility programs'},
    {'content': 'Network security\n- A.8.20 Networks security\n- A.8.21 Security of network services\n- A.8.22 Segregation of networks\n- [red]A.8.23 Web filtering\n- A.8.24 Use of cryptography'},
    {'content': 'Development\n- A.8.25 Secure development life cycle\n- A.8.26 Application security requirements\n- A.8.27 Secure system architecture and engineering principles\n- [red]A.8.28 Secure coding\n- A.8.29 Security testing in development and acceptance\n- A.8.30 Outsourced development\n- A.8.31 Separation of development, test, and production environments\n- A.8.32 Change management\n- A.8.33 Test information'},
    {'content': '[blue]ISO 27701 Annex A\n[blue]PIMS-specific reference control objectives and controls (PII Controllers)\n- A.7.2 Conditions for collection and processing\n- A.7.3 Obligations to PII principals\n- A.7.4 Privacy by design and privacy by default\n- A.7.5 PII sharing, transfer and disclosure'},
    {'content': '[blue]ISO 27701 Annex B\n[blue]PIMS-specific reference control objectives and controls (PII Processors)\n- B.8.2 Conditions for collection and processing\n- B.8.3 Obligations to PII principals\n- B.8.4 Privacy by design and privacy by default\n- B.8.5 PII sharing, transfer and disclosure'},
    {'content': 'Clarification of open issues\n- Discussion of open questions'},
    {'content': 'Preparation of audit conclusions\n- Review and adjustment of findings'},
    {'content': 'Coordination of the auditors'},
    {'content': 'Feedback of audit day 1'},
    {'content': 'End of audit day 1'},
    {'content': 'Closing meeting\n- Presentation of audit findings\n- Discussion'},
    {'content': 'End of audit'},
]

SCHEDULE_COLOURS = (('[blue]', '#0000FF'), ('[red]', '#FF0000'), ('[green]', '#00B050'))


def sap_schedule_commands(kind):
    rows = SAAC_27001_SCHEDULE if kind == 'saac27' else SAAC_SCHEDULE
    return [Command.create(dict(vals, sequence=10 * (i + 1), kind=kind))
            for i, vals in enumerate(rows)]


def _padded(lines, count):
    """The lines, then blank rows (False) up to the rows of the Word form."""
    rows = list(lines)
    return rows + [False] * max(0, count - len(rows))


class AccScheduleLine(models.Model):
    """A row of the ESYD / PNAC audit schedule: Date / Time | Department / organisational
    unit | Representative | Processes | Auditors."""

    _name = 'tuv.form.eap.schedule'
    _description = 'ESYD / PNAC Audit Plan Schedule Line'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    # one table per form on the same project
    kind = fields.Selection([('esyd', 'ESYD'), ('pnac', 'PNAC')], string='Form', required=True,
                            default='esyd', index=True)
    sequence = fields.Integer(default=10)
    date = fields.Date(string='Date')
    time_from = fields.Float(string='From')
    time_to = fields.Float(string='To')
    department = fields.Char(string='Department / Organisational Unit')
    representative = fields.Char(string='Representative (Person in Charge)')
    processes = fields.Text(string='Processes')
    auditors = fields.Char(string='Auditors')


class AccParticipant(models.Model):
    """A row of the "Participants List (to be filled during the audit)" of the ESYD and PNAC
    audit plans."""

    _name = 'tuv.form.eap.participant'
    _description = 'ESYD / PNAC Audit Plan Participant'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    kind = fields.Selection([('esyd', 'ESYD'), ('pnac', 'PNAC')], string='Form', required=True,
                            default='esyd', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Name', required=True)
    position = fields.Char(string='Position')
    opening_meeting = fields.Boolean(string='Opening Meeting')
    closing_meeting = fields.Boolean(string='Closing Meeting')
    signature = fields.Binary(string='Signature', copy=False)


class SaacScheduleLine(models.Model):
    """A row of the SAAC audit schedules (same columns as the TUV audit plan:
    Date / Time | Audit content / Processes | Participants | Auditor(s))."""

    _name = 'tuv.form.sap.schedule'
    _description = 'SAAC Audit Plan Schedule Line'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    kind = fields.Selection([('saac', 'SAAC Audit Plan'), ('saac27', 'SAAC Audit Plan ISO 27001')],
                            string='Form', required=True, default='saac', index=True)
    sequence = fields.Integer(default=10)
    is_section = fields.Boolean(string='Heading',
                                help='A heading row, e.g. the audit day with its location.')
    date = fields.Date(string='Date')
    time_from = fields.Float(string='From')
    time_to = fields.Float(string='To')
    content = fields.Text(string='Audit Content / Processes')
    participants = fields.Text(string='Department / Organizational Unit / Participants')
    auditors = fields.Char(string='Auditor(s)')


class EsydAuditPlanMixin(models.AbstractModel):
    """ESYD audit plan past sections 1 and 2: schedule (eap_schedule_line_ids), signatures,
    significant issues and the participants list (eap_participant_ids)."""

    _name = 'tuv.form.eap.mixin'
    _description = 'ESYD Audit Plan Fields'

    eap_schedule_observations = fields.Text(string='Observations')
    eap_sign_place = fields.Char(string='Place')
    eap_sign_date = fields.Date(string='Date')
    eap_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    eap_auditor_signature = fields.Binary(string='Co-Auditor(s) Signature', copy=False)
    eap_significant_issues = fields.Text(string='Significant Issues Impacting on the Audit Program')
    eap_opening_date = fields.Date(string='Opening Meeting Date')
    eap_closing_date = fields.Date(string='Closing Meeting Date')
    eap_participant_observations = fields.Text(string='Observations (Participants)')

    def _eap_schedule_rows(self):
        return _padded(self.eap_schedule_line_ids, ESYD_SCHEDULE_ROWS)

    def _eap_participant_rows(self):
        return _padded(self.eap_participant_ids, PARTICIPANT_ROWS)

    def _eap_audit_types(self):
        """The single "Audit type" cell of the ESYD / PNAC plans: the audit types of the
        standards (section 2), each once."""
        self.ensure_one()
        labels = dict(self.env['tuv.audit.plan.standard']._fields['audit_type'].selection)
        names = []
        for line in self.ap_standard_line_ids:
            name = (line.audit_type_other if line.audit_type in ('others', 'self_definition')
                    and line.audit_type_other else labels.get(line.audit_type))
            if name and name not in names:
                names.append(name)
        return ', '.join(names)


class PnacAuditPlanMixin(models.AbstractModel):
    """PNAC audit plan: what its sections 1 and 2 add to the TUV ones (company description,
    audit objectives / criteria, IAF code, risk category), then as the ESYD plan."""

    _name = 'tuv.form.pap.mixin'
    _description = 'PNAC Audit Plan Fields'

    pap_company_description = fields.Text(string='Company Description, Business Activities')
    pap_audit_objectives = fields.Text(string='Audit Objectives (Focus)',
                                       default=PNAC_AUDIT_OBJECTIVES)
    pap_audit_criteria = fields.Text(string='Audit Criteria', default=PNAC_AUDIT_CRITERIA,
                                     help='One criterion per line.')
    pap_iaf_code = fields.Char(string='IAF Code')
    pap_risk_category = fields.Char(string='Risk Category')

    pap_schedule_observations = fields.Text(string='Observations')
    pap_sign_place = fields.Char(string='Place')
    pap_sign_date = fields.Date(string='Date')
    pap_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    pap_auditor_signature = fields.Binary(string='Co-Auditor(s) Signature', copy=False)
    pap_significant_issues = fields.Text(string='Significant Issues Impacting on the Audit Program')
    pap_opening_date = fields.Date(string='Opening Meeting Date')
    pap_closing_date = fields.Date(string='Closing Meeting Date')
    pap_participant_observations = fields.Text(string='Observations (Participants)')

    def _pap_schedule_rows(self):
        return _padded(self.pap_schedule_line_ids, PNAC_SCHEDULE_ROWS)

    def _pap_participant_rows(self):
        return _padded(self.pap_participant_ids, PARTICIPANT_ROWS)


class SaacAuditPlanMixin(models.AbstractModel):
    """SAAC audit plan (TUV plan with the audit objectives in section 2) past sections 1 and 2:
    schedule (sap_schedule_line_ids), signatures, significant issues."""

    _name = 'tuv.form.sap.mixin'
    _description = 'SAAC Audit Plan Fields'

    sap_sign_place = fields.Char(string='Place')
    sap_sign_date = fields.Date(string='Date')
    sap_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    sap_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)
    sap_significant_issues = fields.Text(string='Significant Issues Impacting on the Audit Program',
                                         default='None.')

    @api.model
    def _sap_schedule_blocks(self, line):
        """The content of a SAAC schedule row as blocks to print:
        ('h', text, colour, mark) a bold line ("Optional:" as mark, printed on yellow),
        ('ul', [(text, colour)]) a run of bullets, ('note', [texts]) centred lines on yellow.
        Rows written without any "- " read as on the TUV plan: first line bold, then bullets."""
        texts = [t.strip() for t in (line.content or '').split('\n') if t.strip()]
        explicit = any(t.startswith('- ') for t in texts)
        blocks = []
        for i, text in enumerate(texts):
            bullet = text.startswith('- ') if explicit else i > 0
            if text.startswith('- '):
                text = text[2:].strip()
            if text.startswith('[note]'):
                text = text[len('[note]'):].strip()
                if blocks and blocks[-1][0] == 'note':
                    blocks[-1][1].append(text)
                else:
                    blocks.append(('note', [text]))
                continue
            colour = False
            for tag, value in SCHEDULE_COLOURS:
                if text.startswith(tag):
                    text, colour = text[len(tag):].strip(), value
            if bullet:
                if blocks and blocks[-1][0] == 'ul':
                    blocks[-1][1].append((text, colour))
                else:
                    blocks.append(('ul', [(text, colour)]))
                continue
            mark = ''
            if text.startswith('Optional:'):
                mark, text = 'Optional:', text[len('Optional:'):].strip()
            blocks.append(('h', text, colour, mark))
        return blocks

    @api.model
    def _sap_schedule_title(self, line):
        """The first line of a schedule row without its tags."""
        first = next((t.strip() for t in (line.content or '').split('\n') if t.strip()), '')
        for tag in ('[note]', '[blue]', '[red]', '[green]'):
            first = first.replace(tag, '', 1)
        return first.strip()


class SaacIsmsAuditPlanMixin(models.AbstractModel):
    """SAAC audit plan ISO 27001 past sections 1 and 2: the ISO 27001 / 27701 schedule
    (sapi_schedule_line_ids), signatures, significant issues."""

    _name = 'tuv.form.sapi.mixin'
    _description = 'SAAC Audit Plan ISO 27001 Fields'

    sapi_sign_place = fields.Char(string='Place')
    sapi_sign_date = fields.Date(string='Date')
    sapi_lead_auditor_signature = fields.Binary(string='Lead Auditor Signature', copy=False)
    sapi_auditor_signature = fields.Binary(string='Auditor(s) Signature', copy=False)
    sapi_significant_issues = fields.Text(string='Significant Issues Impacting on the Audit Program',
                                          default='None.')


ACC_MIXINS = ['tuv.form.eap.mixin', 'tuv.form.pap.mixin', 'tuv.form.sap.mixin',
              'tuv.form.sapi.mixin']


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan'] + ACC_MIXINS

    eap_schedule_line_ids = fields.One2many(
        'tuv.form.eap.schedule', 'plan_id', string='Audit Schedule (ESYD)', copy=True,
        domain=[('kind', '=', 'esyd')], context={'default_kind': 'esyd'})
    eap_participant_ids = fields.One2many(
        'tuv.form.eap.participant', 'plan_id', string='Participants (ESYD)', copy=True,
        domain=[('kind', '=', 'esyd')], context={'default_kind': 'esyd'})
    pap_schedule_line_ids = fields.One2many(
        'tuv.form.eap.schedule', 'plan_id', string='Audit Schedule (PNAC)', copy=True,
        domain=[('kind', '=', 'pnac')], context={'default_kind': 'pnac'})
    pap_participant_ids = fields.One2many(
        'tuv.form.eap.participant', 'plan_id', string='Participants (PNAC)', copy=True,
        domain=[('kind', '=', 'pnac')], context={'default_kind': 'pnac'})
    sap_schedule_line_ids = fields.One2many(
        'tuv.form.sap.schedule', 'plan_id', string='Audit Schedule (SAAC)', copy=True,
        domain=[('kind', '=', 'saac')], context={'default_kind': 'saac'})
    sapi_schedule_line_ids = fields.One2many(
        'tuv.form.sap.schedule', 'plan_id', string='Audit Schedule (SAAC ISO 27001)', copy=True,
        domain=[('kind', '=', 'saac27')], context={'default_kind': 'saac27'})

    def _tuv_fill_saac_schedule(self):
        """Called from data: give the predefined SAAC audit plan the rows of the Word form once."""
        for plan in self:
            if not plan.sap_schedule_line_ids:
                plan.sap_schedule_line_ids = sap_schedule_commands('saac')

    def _tuv_fill_saac_27001_schedule(self):
        """Called from data: the rows of the SAAC ISO 27001 Word form, once."""
        for plan in self:
            if not plan.sapi_schedule_line_ids:
                plan.sapi_schedule_line_ids = sap_schedule_commands('saac27')


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project'] + ACC_MIXINS

    # each table its own computed field, so it refreshes when the report is picked
    eap_schedule_line_ids = fields.One2many(
        'tuv.form.eap.schedule', 'project_id', string='Audit Schedule (ESYD)',
        domain=[('kind', '=', 'esyd')], context={'default_kind': 'esyd'},
        compute='_compute_eap_schedule_line_ids', store=True, readonly=False)
    eap_participant_ids = fields.One2many(
        'tuv.form.eap.participant', 'project_id', string='Participants (ESYD)',
        domain=[('kind', '=', 'esyd')], context={'default_kind': 'esyd'},
        compute='_compute_eap_participant_ids', store=True, readonly=False)
    pap_schedule_line_ids = fields.One2many(
        'tuv.form.eap.schedule', 'project_id', string='Audit Schedule (PNAC)',
        domain=[('kind', '=', 'pnac')], context={'default_kind': 'pnac'},
        compute='_compute_pap_schedule_line_ids', store=True, readonly=False)
    pap_participant_ids = fields.One2many(
        'tuv.form.eap.participant', 'project_id', string='Participants (PNAC)',
        domain=[('kind', '=', 'pnac')], context={'default_kind': 'pnac'},
        compute='_compute_pap_participant_ids', store=True, readonly=False)
    sap_schedule_line_ids = fields.One2many(
        'tuv.form.sap.schedule', 'project_id', string='Audit Schedule (SAAC)',
        domain=[('kind', '=', 'saac')], context={'default_kind': 'saac'},
        compute='_compute_sap_schedule_line_ids', store=True, readonly=False)
    sapi_schedule_line_ids = fields.One2many(
        'tuv.form.sap.schedule', 'project_id', string='Audit Schedule (SAAC ISO 27001)',
        domain=[('kind', '=', 'saac27')], context={'default_kind': 'saac27'},
        compute='_compute_sapi_schedule_line_ids', store=True, readonly=False)

    # Filled from the project, still editable
    eap_opening_date = fields.Date(compute='_compute_acc_meeting_dates', store=True, readonly=False)
    eap_closing_date = fields.Date(compute='_compute_acc_meeting_dates', store=True, readonly=False)
    pap_opening_date = fields.Date(compute='_compute_acc_meeting_dates', store=True, readonly=False)
    pap_closing_date = fields.Date(compute='_compute_acc_meeting_dates', store=True, readonly=False)
    pap_iaf_code = fields.Char(compute='_compute_pap_codes', store=True, readonly=False)
    pap_risk_category = fields.Char(compute='_compute_pap_codes', store=True, readonly=False)

    @api.depends('audit_report_id')
    def _compute_eap_schedule_line_ids(self):
        # no fixed rows (the PDF adds the blank ones); kept as the user enters them
        for project in self:
            project.eap_schedule_line_ids = project.eap_schedule_line_ids

    @api.depends('audit_report_id')
    def _compute_eap_participant_ids(self):
        for project in self:
            project.eap_participant_ids = project.eap_participant_ids

    @api.depends('audit_report_id')
    def _compute_pap_schedule_line_ids(self):
        for project in self:
            project.pap_schedule_line_ids = project.pap_schedule_line_ids

    @api.depends('audit_report_id')
    def _compute_pap_participant_ids(self):
        for project in self:
            project.pap_participant_ids = project.pap_participant_ids

    @api.depends('audit_report_id')
    def _compute_sap_schedule_line_ids(self):
        # the rows of the Word form, added once the SAAC plan is picked; edits are kept
        for project in self:
            if not project.sap_schedule_line_ids and project.audit_report_key == 'saac_audit_plan':
                project.sap_schedule_line_ids = sap_schedule_commands('saac')
            else:
                project.sap_schedule_line_ids = project.sap_schedule_line_ids

    @api.depends('audit_report_id')
    def _compute_sapi_schedule_line_ids(self):
        for project in self:
            if not project.sapi_schedule_line_ids \
                    and project.audit_report_key == 'saac_audit_plan_27001':
                project.sapi_schedule_line_ids = sap_schedule_commands('saac27')
            else:
                project.sapi_schedule_line_ids = project.sapi_schedule_line_ids

    @api.depends('ap_audit_date_stage1', 'ap_audit_date_stage2', 'ap_audit_date_until')
    def _compute_acc_meeting_dates(self):
        # opening meeting on the first audit day, closing meeting on the last
        for project in self:
            start = project.ap_audit_date_stage2 or project.ap_audit_date_stage1
            end = project.ap_audit_date_until or start
            project.eap_opening_date = project.pap_opening_date = start
            project.eap_closing_date = project.pap_closing_date = end

    @api.depends('ea_code_ids', 'md1_risk_level')
    def _compute_pap_codes(self):
        # IAF code = the EA code(s) of the project; risk category from the mandays calculation
        risk_labels = dict(self._fields['md1_risk_level'].selection)
        for project in self:
            project.pap_iaf_code = ', '.join(project.ea_code_ids.mapped('name')) or False
            project.pap_risk_category = risk_labels.get(project.md1_risk_level, False)
