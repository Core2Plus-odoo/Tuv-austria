from odoo import api, fields, models


class AuditReport(models.Model):
    """One card on the Reports screen: a predefined audit form (a Word form of TUV Austria).

    Each card opens its own single, predefined record. New forms are added as data,
    not by the users, so the screen has no "New" button.
    """

    _name = 'tuv.audit.report'
    _description = 'Audit Report Form'
    _order = 'sequence, id'

    name = fields.Char(string='Form', required=True)
    sequence = fields.Integer(default=10)
    accreditation = fields.Selection([
        ('tuv_austria', 'TÜV Austria'),
        ('esyd', 'ESYD'),
        ('pnac', 'PNAC'),
        ('saac', 'SAAC'),
    ], string='Accreditation', required=True, default='tuv_austria',
        help='The accreditation body the form set belongs to (folders ODOO_AUSTRIAN_CERT, '
             'ODOO_ESYD, ODOO_PNAC, ODOO_SAAC).')
    subtitle = fields.Char(string='Subtitle')
    code = fields.Char(string='Form Number')
    revision = fields.Char(string='Revision')
    document_name = fields.Char(string='Word Document')
    record_xmlid = fields.Char(string='Form Record', required=True,
                               help='XML id of the predefined record this card opens.')
    view_xmlid = fields.Char(string='Form View', help='XML id of the form view the card opens.')
    report_action_xmlid = fields.Char(string='PDF Report',
                                      help='XML id of the PDF report printed from the project.')
    report_key = fields.Char(string='Key', required=True,
                             help='Technical key the project form uses to show this report\'s fields.')
    uses_audit_info = fields.Boolean(
        string='Company and Audit Information', default=True,
        help='The form opens with sections "1. Company information" and "2. Audit information".')
    # The project's Audit Plan tab offers only these (audit_plan, audit_plan_isms,
    # esyd_audit_plan, pnac_audit_plan, saac_audit_plan, saac_audit_plan_27001).
    is_audit_plan = fields.Boolean(string='Audit Plan Form', compute='_compute_is_audit_plan', store=True)
    # The project's Audit Execution tab offers these: participation lists, audit checklists
    # and the AQG audit questionnaires (checklists of ESYD / PNAC / SAAC).
    is_execution_form = fields.Boolean(string='Audit Execution Form', compute='_compute_is_audit_plan',
                                       store=True)
    # The project's Audit Report tab offers these: the audit reports and the expert reports.
    is_final_report = fields.Boolean(string='Audit Report Form', compute='_compute_is_audit_plan',
                                     store=True)
    # The project's Certificate Dispatched tab offers these: the certificate texts.
    is_certificate_form = fields.Boolean(string='Certificate Form', compute='_compute_is_audit_plan',
                                         store=True)

    @api.depends('report_key')
    def _compute_is_audit_plan(self):
        for card in self:
            key = card.report_key or ''
            card.is_audit_plan = 'audit_plan' in key
            card.is_execution_form = (key.endswith('participation_list')
                                      or key.startswith(('checklist_', 'aqg_')))
            card.is_final_report = key.endswith(('audit_report', 'expert_report'))
            card.is_certificate_form = key.endswith('certificate_text')

    @api.depends('name', 'accreditation')
    def _compute_display_name(self):
        # "PNAC - Audit Plan" in the project's Report field, where every body has an audit plan
        labels = dict(self._fields['accreditation'].selection)
        for card in self:
            card.display_name = '%s - %s' % (labels.get(card.accreditation, ''), card.name)

    def action_open_form(self):
        self.ensure_one()
        record = self.env.ref(self.record_xmlid)
        view = self.view_xmlid and self.env.ref(self.view_xmlid)
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': record._name,
            'res_id': record.id,
            'view_mode': 'form',
            'views': [(view.id if view else False, 'form')],
            'target': 'current',
        }

    def _print(self, records):
        """The PDF of this form for `records` (projects or standalone forms)."""
        self.ensure_one()
        if not self.report_action_xmlid:
            return False
        # the forms bring their own header/footer: no "Configure your document layout" popup
        return self.env.ref(self.report_action_xmlid).with_context(
            discard_logo_check=True).report_action(records)
