from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    document_type = fields.Selection([
        ('offer_application', 'Offer Application'),
        ('contract_form', 'TAC-TAH-Contract'),
        ('pnac_contract', 'PNAC-Contract'),
        ('proposal_form', 'Proposal Form'),
    ], string='Document Type')
    partner_street = fields.Char(related='partner_id.street', string='Street', readonly=True)
    partner_street2 = fields.Char(related='partner_id.street2', string='Street 2', readonly=True)
    partner_city = fields.Char(related='partner_id.city', string='City', readonly=True)
    partner_state_id = fields.Many2one(related='partner_id.state_id', string='State', readonly=True)
    partner_zip = fields.Char(related='partner_id.zip', string='Zip', readonly=True)
    partner_country_id = fields.Many2one(related='partner_id.country_id', string='Country', readonly=True)
    distinctive_title = fields.Char(
        related='partner_id.distinctive_title', string='Distinctive Title', store=True, readonly=True)
    partner_phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)
    partner_email = fields.Char(related='partner_id.email', string='Email', readonly=True)
    telefax = fields.Char(
        related='partner_id.telefax', string='Telefax', store=True, readonly=True)
    website = fields.Char(
        related='partner_id.website', string='URL', store=True, readonly=True)
    vat = fields.Char(
        related='partner_id.vat', string='VAT Nr.', store=True, readonly=True)
    certificate_no = fields.Char(string='Certificate No')
    certification_standard = fields.Char(string='Certification Standard')
    ea_code_ids = fields.Many2many('industry.ea.code', string='EA Code')
    scope_of_certification = fields.Char(string='Scope of Certification')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    next_surveillance = fields.Date(string='Next Surveillance')
    audit_type = fields.Char(string='Audit Type')
    lead_auditor = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Lead Auditor')
    certificate_status = fields.Char(string='Certificate Status')
    office_issued_from = fields.Char(string='Office Issued From')
    notes = fields.Char(string='Notes')

    audit_site = fields.Char(string='Site Where The Audit Will Take Place')
    other_facilities = fields.Char(string='Other Facilities / Subsidiaries / Temporary Sites')
    sites_to_be_audited = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Do You Wish Those Sites To Be Audited As Well?')
    company_representative = fields.Char(string='Company Representative')
    management_system_representative = fields.Char(string='Management System Representative')
    management_system_representative_phone = fields.Char(string='Management System Representative Phone')
    management_system_representative_email = fields.Char(string='Management System Representative Email')
    consultant = fields.Char(string='Consultant')
    consultant_phone = fields.Char(string='Consultant Phone')
    consultant_email = fields.Char(string='Consultant Email')
    scope_of_activity = fields.Char(string='Scope Of Activity')
    critical_processes = fields.Char(
        string='Critical Processes, Processes Carried Out By Subcontractors And Their Interaction')
    legislation_relative = fields.Char(
        string='Legislation Relative To The Products Or The Services Of The Company')
    permanent_personnel = fields.Char(string='Permanent Personnel')
    temporary_personnel = fields.Char(string='Temporary Personnel')
    personnel_on_shifts = fields.Char(string='Number Of Personnel On Shifts')
    number_of_shifts = fields.Char(string='Nr. Of Shifts (if any)')
    level_of_integration = fields.Selection(
        [(str(pct), '%d%%' % pct) for pct in range(10, 101, 10)],
        string='Level Of Integration Of Management Systems (%)')
    other_certified_management_system = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Existence Of Other Certified Management System '
              '(Please Fill In Relevant Annex In Case Of Transfer Request)')
    license_attachment = fields.Binary(
        string='Operation License / Environmental License / Corporation Charter (please attach)')
    license_attachment_filename = fields.Char(string='License Attachment Filename')

    # Proposal Form (<<XYZ>> / <<STANDARD>> placeholders of the Word proposal template)
    management_system_name = fields.Char(
        string='Management System Name', help='Goes into "<<XYZ>> MANAGEMENT SYSTEM" of the proposal.')
    charge_stage_1_audit = fields.Char(string='Stage 1 Audit')
    charge_stage_2_audit = fields.Char(string='Stage 2 Audit')
    travel_boarding_lodging = fields.Char(string='Traveling, Boarding & Lodging')
    charge_surveillance_1 = fields.Char(string='1ST Annual Surveillance@')
    charge_surveillance_2 = fields.Char(string='2nd Annual Surveillance@')

    # Summary of Cost - typed in by hand, nothing is taken from the order lines
    cost_tax_label = fields.Char(string='Sales Tax Row Label')
    cost_initial_audit = fields.Char(string='Initial Audit')
    cost_surveillance_1 = fields.Char(string='1st Surveillance Audit')
    cost_surveillance_2 = fields.Char(string='2nd Surveillance Audit')
    cost_total = fields.Char(string='Total')
    cost_tax_initial_audit = fields.Char(string='Initial Audit')
    cost_tax_surveillance_1 = fields.Char(string='1st Surveillance Audit')
    cost_tax_surveillance_2 = fields.Char(string='2nd Surveillance Audit')
    cost_tax_total = fields.Char(string='Total')
    cost_grand_initial_audit = fields.Char(string='Initial Audit')
    cost_grand_surveillance_1 = fields.Char(string='1st Surveillance Audit')
    cost_grand_surveillance_2 = fields.Char(string='2nd Surveillance Audit')
    cost_grand_total = fields.Char(string='Total')
    proposal_invoicing_terms = fields.Char(string='Invoicing Terms')

    # Prepared By block - blank falls back to the salesperson on the order
    prepared_by_name = fields.Char(string='Prepared By Name')
    prepared_by_designation = fields.Char(string='Designation')
    prepared_by_phone = fields.Char(string='Prepared By Phone')
    prepared_by_email = fields.Char(string='Prepared By Email')
    prepared_by_signature = fields.Binary(string='Signature', attachment=True)
    prepared_by_signature_filename = fields.Char(string='Signature Filename')

    # ------------------------------------------------------------------
    # Contract Form (TAC-TAH template) - every <<placeholder>> of the doc
    # ------------------------------------------------------------------
    contract_standards = fields.Char(
        string='Standard(s)', help='Goes into "<<Enter Standard(s)>>" of the contract.')
    contract_address_1 = fields.Char(string='Address 1')
    contract_address_2 = fields.Char(string='Address 2')
    contract_representative = fields.Char(string='Company Representative (Attn)')
    contract_designation = fields.Char(string='Designation')
    contract_date = fields.Date(string='Contract Date')
    contract_ref = fields.Char(string='Ref #')

    # Table: Certification Services Offered / ACCREDITATION (2 rows)
    contract_service_1 = fields.Char(string='Service 1 - Standard(s)')
    contract_accreditation_1 = fields.Char(string='Service 1 - Accreditation Body')
    contract_service_2 = fields.Char(string='Service 2 - Standard(s)')
    contract_accreditation_2 = fields.Char(string='Service 2 - Accreditation Body')

    # CHARGES table - 4 rows x 3 year columns, all typed in by hand
    contract_fee_y1 = fields.Char(string='Standard(s) - 1st Year')
    contract_fee_y2 = fields.Char(string='Standard(s) - 2nd Year')
    contract_fee_y3 = fields.Char(string='Standard(s) - 3rd Year')
    contract_mandays_y1 = fields.Char(string='# of Man-days - 1st Year')
    contract_mandays_y2 = fields.Char(string='# of Man-days - 2nd Year')
    contract_mandays_y3 = fields.Char(string='# of Man-days - 3rd Year')
    contract_tax_province = fields.Char(string='Sales Tax (Province)@')
    contract_tax_y1 = fields.Char(string='Sales Tax - 1st Year')
    contract_tax_y2 = fields.Char(string='Sales Tax - 2nd Year')
    contract_tax_y3 = fields.Char(string='Sales Tax - 3rd Year')
    contract_total_y1 = fields.Char(string='Total Payable - 1st Year')
    contract_total_y2 = fields.Char(string='Total Payable - 2nd Year')
    contract_total_y3 = fields.Char(string='Total Payable - 3rd Year')
    contract_advance_amount = fields.Char(string='1st Year Initial Audit Amount (Advance)')
    pnac_logo_1 = fields.Binary(string='PNAC Logo 1', attachment=True)
    pnac_logo_1_filename = fields.Char(string='PNAC Logo 1 Filename')
    pnac_logo_2 = fields.Binary(string='PNAC Logo 2', attachment=True)
    pnac_logo_2_filename = fields.Char(string='PNAC Logo 2 Filename')
    pnac_logo_3 = fields.Binary(string='PNAC Logo 3', attachment=True)
    pnac_logo_3_filename = fields.Char(string='PNAC Logo 3 Filename')
    pnac_logo_4 = fields.Binary(string='PNAC Logo 4', attachment=True)
    pnac_logo_4_filename = fields.Char(string='PNAC Logo 4 Filename')

    def action_view_project_ids(self):
        self.ensure_one()
        projects = self.project_ids.filtered('active')
        if len(projects) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': projects.name,
                'res_model': 'project.project',
                'res_id': projects.id,
                'view_mode': 'form',
                'views': [(False, 'form')],
                'target': 'current',
            }
        return super().action_view_project_ids()

    def action_view_task_ids(self):
        self.ensure_one()
        tasks = self.tasks_ids
        action = self.env['ir.actions.actions']._for_xml_id('project.action_view_all_task')
        if len(tasks) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = tasks.id
        else:
            action['domain'] = [('id', 'in', tasks.ids)]
        return action
