from odoo import api, fields, models

# The standards of the "It has been proven that the requirements of the standard" grid of form
# FM-TAGMBH-MSZ-038, in the form's order (3 rows of 4; the last two cells are free).
CT_STANDARDS = [
    ('ct_std_iso9001', 'ISO 9001', ('iso_9001_2015',)),
    ('ct_std_iso14001', 'ISO 14001', ('iso_14001_2015',)),
    ('ct_std_iso45001', 'ISO 45001', ('iso_45001_2018',)),
    ('ct_std_iso29990', 'ISO 29990', ()),
    ('ct_std_scc', 'SCC*/**(p)', ('scc',)),
    ('ct_std_scp', 'SCP', ('scp',)),
    ('ct_std_iso22000', 'ISO 22000', ('iso_22000_2018', 'fssc_22000')),
    ('ct_std_iso50001', 'ISO 50001', ('iso_50001_2018',)),
    ('ct_std_iso27001', 'ISO 27001', ('iso_27001_2013', 'iso_27001_2022')),
    ('ct_std_iso20000', 'ISO 20000-1', ('iso_20000_1_2018',)),
]


class AuditCertificateTextMixin(models.AbstractModel):
    """Certificate text, form FM-TAGMBH-MSZ-038, past its sections 1 and 2."""

    _name = 'tuv.audit.certificate.text.mixin'
    _description = 'Certificate Text Fields'

    ct_contact_person = fields.Char(string='Contact Person')
    ct_phone = fields.Char(string='Phone')
    ct_fax = fields.Char(string='Fax')
    ct_email = fields.Char(string='Email')

    # Certificate issue
    ct_format_a3 = fields.Boolean(string='A3')
    ct_format_a4 = fields.Boolean(string='A4', default=True)
    ct_format_pdf = fields.Boolean(string='pdf-file', default=True)
    ct_languages = fields.Char(string='Desired Languages')
    ct_certificates_per_language = fields.Char(string='Number of Certificates per Language')
    ct_additional_costs = fields.Char(string='Additional Costs for Additional Certificates')

    # Sub certificates (optional)
    ct_sub_certificate_1 = fields.Text(string='Sub Certificate 01')
    ct_sub_certificate_2 = fields.Text(string='Sub Certificate 02')
    ct_sub_certificate_3 = fields.Text(string='Sub Certificate 03')
    ct_sub_certificate_4 = fields.Text(string='Sub Certificate 04')

    # Certificate wording
    ct_company_text = fields.Text(string='Certified Company (name, address, zip code, place)')
    ct_scope_text = fields.Text(string='Scope')
    ct_std_iso9001 = fields.Boolean(string='ISO 9001')
    ct_std_iso14001 = fields.Boolean(string='ISO 14001')
    ct_std_iso45001 = fields.Boolean(string='ISO 45001')
    ct_std_iso29990 = fields.Boolean(string='ISO 29990')
    ct_std_scc = fields.Boolean(string='SCC*/**(p)')
    ct_std_scp = fields.Boolean(string='SCP')
    ct_std_iso22000 = fields.Boolean(string='ISO 22000')
    ct_std_iso50001 = fields.Boolean(string='ISO 50001')
    ct_std_iso27001 = fields.Boolean(string='ISO 27001')
    ct_std_iso20000 = fields.Boolean(string='ISO 20000-1')
    ct_std_other_1 = fields.Char(string='Other Standard 1')
    ct_std_other_2 = fields.Char(string='Other Standard 2')
    ct_send_logo = fields.Selection([('yes', 'yes'), ('no', 'no'), ('undefined', 'undefined')],
                                    string='Send Certification Logo as jpg to Company')

    # Statement of applicability (ISO 27001) / operator number (IT-SiKat)
    ct_soa_file = fields.Char(string='SoA Filename, Version')
    ct_soa_date = fields.Date(string='SoA Date')
    ct_branch_electricity = fields.Char(string='Branch Electricity')
    ct_branch_gas = fields.Char(string='Branch Gas')

    def _ct_standard_grid(self):
        """[(label, ticked)] in the form's order, the two free cells last."""
        self.ensure_one()
        grid = [(label, self[fname]) for fname, label, _codes in CT_STANDARDS]
        grid += [(self.ct_std_other_1 or '', bool(self.ct_std_other_1)),
                 (self.ct_std_other_2 or '', bool(self.ct_std_other_2))]
        return grid


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = ['tuv.audit.plan', 'tuv.audit.certificate.text.mixin']


class ProjectProject(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'tuv.audit.certificate.text.mixin']

    # filled from sections 1 and 2 of the project, still editable
    ct_contact_person = fields.Char(compute='_compute_ct_from_project', store=True, readonly=False)
    ct_phone = fields.Char(compute='_compute_ct_from_project', store=True, readonly=False)
    ct_email = fields.Char(compute='_compute_ct_from_project', store=True, readonly=False)
    ct_company_text = fields.Text(compute='_compute_ct_from_project', store=True, readonly=False)
    ct_scope_text = fields.Text(compute='_compute_ct_from_project', store=True, readonly=False)
    ct_std_iso9001 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso14001 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso45001 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso29990 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_scc = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_scp = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso22000 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso50001 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso27001 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)
    ct_std_iso20000 = fields.Boolean(compute='_compute_ct_standards', store=True, readonly=False)

    @api.depends('ap_partner_id', 'ap_company_address', 'ap_representative',
                 'ap_representative_email', 'ap_certificate_scope')
    def _compute_ct_from_project(self):
        for project in self:
            partner = project.ap_partner_id
            project.ct_contact_person = project.ap_representative
            project.ct_phone = partner.phone
            project.ct_email = project.ap_representative_email
            address = [line.strip(' ,') for line in (project.ap_company_address or '').split('\n')]
            project.ct_company_text = '\n'.join(filter(None, [partner.name] + address)) or False
            project.ct_scope_text = project.ap_certificate_scope

    @api.depends('ap_standard_line_ids.standard')
    def _compute_ct_standards(self):
        for project in self:
            codes = set(project.ap_standard_line_ids.mapped('standard'))
            for fname, _label, standard_codes in CT_STANDARDS:
                project[fname] = bool(codes & set(standard_codes))
