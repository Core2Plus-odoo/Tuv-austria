import re

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

from .audit_plan import EAC_SCOPES, default_schedule_commands

# Mandays Calculation tab value -> Audit Plan value
MD_STANDARD_TO_PLAN = {
    'iso9001_2015': 'iso_9001_2015',
    'iso14001_2015': 'iso_14001_2015',
    'iso22000_2018': 'iso_22000_2018',
    'fssc22000': 'fssc_22000',
    'iso45001': 'iso_45001_2018',
    'ohsas18001': 'iso_45001_2018',  # withdrawn, replaced by ISO 45001; the form does not list it
    'iso27001': 'iso_27001_2022',
    'iso22301': 'iso_22301',
    'iso50001': 'iso_50001_2018',
    'iso39001': 'iso_39001',
    'iso13485': 'iso_13485_2016',
    'emas_iii': 'emas_iii',
    'iso_iec20000': 'iso_20000_1_2018',
    'globalgap': 'globalgap',
}
MD_AUDIT_TYPE_TO_PLAN = {
    'certification': 'initial',
    '1st_surveillance': 'surveillance_1',
    '2nd_surveillance': 'surveillance_2',
    'recertification': 'recertification',
    'pre_audit': 'pre_audit',
    'extension': 'enhancement',
}
MD_AUDIT_KIND_TO_PLAN = {
    'combined': 'combined',
    'integrated': 'integrated',
    'joint_audit': 'others',
}
HOURS_PER_MANDAY = 8  # IAF MD 5: one auditor day is 8 hours


def _first_number(text):
    """'4 (Surveillance 2 / 2)' -> 4.0; None when the text holds no number."""
    match = re.search(r'\d+(?:[.,]\d+)?', text or '')
    return float(match.group().replace(',', '.')) if match else None


class ProjectProject(models.Model):
    _inherit = ['project.project', 'tuv.audit.info.mixin', 'tuv.audit.plan.mixin']
    _name = 'project.project'

    audit_report_id = fields.Many2one(
        'tuv.audit.report', string='Report',
        help='Pick the audit form to fill in for this project; its fields appear below.')
    audit_report_key = fields.Char(related='audit_report_id.report_key')
    audit_report_uses_info = fields.Boolean(related='audit_report_id.uses_audit_info')

    ap_standard_line_ids = fields.One2many(
        'tuv.audit.plan.standard', 'project_id', string='Audit Standard(s)',
        compute='_compute_ap_standard_line_ids', store=True, readonly=False)
    ap_team_line_ids = fields.One2many(
        'tuv.audit.plan.team', 'project_id', string='Audit Plan Team',
        compute='_compute_ap_team_line_ids', store=True, readonly=False)
    # labels the project already uses elsewhere; the tab shows the form's own wording
    ap_standards_display = fields.Char(string='Audit Plan Standards')
    ap_schedule_line_ids = fields.One2many(
        'tuv.audit.plan.schedule', 'project_id', string='Audit Schedule',
        domain=[('schedule_kind', '=', 'plan')],
        compute='_compute_ap_schedule_line_ids', store=True, readonly=False)

    # Filled from the sale order / project tabs, still editable on the Audit Plan tab
    ap_partner_id = fields.Many2one(string='Audit Plan Company', compute='_compute_ap_from_project',
                                    store=True, readonly=False)
    ap_other_sites = fields.Text(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_representative = fields.Char(string='Audit Plan Representative', compute='_compute_ap_from_project',
                                    store=True, readonly=False)
    ap_representative_email = fields.Char(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_certificate_scope = fields.Text(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_audit_date_stage1 = fields.Date(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_audit_date_stage2 = fields.Date(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_audit_method = fields.Selection(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_employee_count = fields.Integer(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_audit_duration_hours = fields.Float(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_eac_scope = fields.Selection(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_nace_code = fields.Char(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_category = fields.Char(compute='_compute_ap_from_project', store=True, readonly=False)
    ap_lead_auditor_id = fields.Many2one(string='Audit Plan Lead Auditor', compute='_compute_ap_from_project',
                                         store=True, readonly=False)
    ap_audit_language = fields.Selection(compute='_compute_ap_from_project', store=True, readonly=False)

    def action_print_audit_report(self):
        """Print button next to the Report field: the PDF of the selected report."""
        self.ensure_one()
        action = self.audit_report_id._print(self)
        if not action:
            raise UserError(_('Select a report to print first.'))
        return action

    @api.depends('partner_id', 'md_sale_order_id.partner_id',
                 'md_sale_order_id.management_system_representative_email',
                 'md_other_sites', 'md_company_representative', 'md_certification_scope',
                 'md_audit_date_st1', 'md_audit_date_st2', 'md_audit_kind', 'md1_total_personnel',
                 'md_audit_duration', 'ea_code_ids', 'md_nace', 'md_category', 'auditor_id',
                 'md_audit_language', 'md_standard_1', 'md_standard_2', 'md_standard_3')
    def _compute_ap_from_project(self):
        eac_codes = {code for code, _label in EAC_SCOPES}
        for project in self:
            order = project.md_sale_order_id
            partner = order.partner_id or project.partner_id
            project.ap_partner_id = partner
            project.ap_other_sites = project.md_other_sites
            project.ap_representative = project.md_company_representative
            project.ap_representative_email = (order.management_system_representative_email
                                               or partner.email)
            project.ap_certificate_scope = project.md_certification_scope
            project.ap_audit_date_stage1 = project.md_audit_date_st1
            project.ap_audit_date_stage2 = project.md_audit_date_st2
            standards = [s for s in (project.md_standard_1, project.md_standard_2,
                                     project.md_standard_3) if s]
            project.ap_audit_method = (MD_AUDIT_KIND_TO_PLAN.get(project.md_audit_kind)
                                       or ('single' if len(standards) == 1 else False))
            employees = _first_number(project.md1_total_personnel)
            project.ap_employee_count = int(employees) if employees else 0
            mandays = _first_number(project.md_audit_duration)
            project.ap_audit_duration_hours = mandays * HOURS_PER_MANDAY if mandays else 0.0
            ea = next((c for c in (n.replace('EA', '').strip()
                                   for n in project.ea_code_ids.mapped('name'))
                       if c in eac_codes), False)
            project.ap_eac_scope = ea
            project.ap_nace_code = project.md_nace
            project.ap_category = project.md_category
            project.ap_lead_auditor_id = project.auditor_id
            project.ap_audit_language = ('english' if project.md_audit_language in (False, 'english')
                                         else project.ap_audit_language or 'english')

    @api.depends('md_standard_1', 'md_standard_2', 'md_standard_3', 'md_audit_type', 'certificate_no')
    def _compute_ap_standard_line_ids(self):
        for project in self:
            audit_type = MD_AUDIT_TYPE_TO_PLAN.get(project.md_audit_type, False)
            lines = [Command.clear()]
            for seq, md_standard in enumerate((project.md_standard_1, project.md_standard_2,
                                               project.md_standard_3), start=1):
                standard = MD_STANDARD_TO_PLAN.get(md_standard)
                if standard:
                    lines.append(Command.create({
                        'sequence': seq * 10,
                        'standard': standard,
                        'audit_type': audit_type,
                        'registration_no': project.certificate_no or False,
                    }))
            project.ap_standard_line_ids = lines

    @api.depends('md_co_auditor_id', 'md_trainee_id')
    def _compute_ap_team_line_ids(self):
        for project in self:
            lines = [Command.clear()]
            if project.md_co_auditor_id:
                lines.append(Command.create({'sequence': 10, 'role': 'auditor',
                                             'partner_id': project.md_co_auditor_id.id}))
            if project.md_trainee_id:
                lines.append(Command.create({'sequence': 20, 'role': 'trainee',
                                             'partner_id': project.md_trainee_id.id}))
            project.ap_team_line_ids = lines

    @api.depends('audit_report_id')
    def _compute_ap_schedule_line_ids(self):
        # the fixed rows of the Word form, added once; what the user enters is kept
        for project in self:
            if not project.ap_schedule_line_ids:
                project.ap_schedule_line_ids = default_schedule_commands()
