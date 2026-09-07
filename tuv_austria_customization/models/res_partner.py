from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    telefax = fields.Char(string='Telefax')
    distinctive_title = fields.Char(string='Distinctive Title')
    contact_type = fields.Selection([
        ('client', 'Client'),
        ('vendor', 'Vendor'),
        ('auditor', 'Auditor'),
    ], string='Contact Type')
    industry_ea_code_id = fields.Many2one('industry.ea.code', string='Industry/EA Code')
    cnic = fields.Char(string='CNIC')

    employment_type_ids = fields.Many2many('employment.type', string='Employment Type')
    approved_ea_code_ids = fields.Many2many(
        'industry.ea.code', 'res_partner_approved_ea_code_rel',
        'partner_id', 'ea_code_id', string='Approved EA Codes')
    certification_standard_ids = fields.Many2many(
        'certification.standard', string='Certification Standards Competent In')
    auditor_category_ids = fields.Many2many('auditor.category', string='Auditor Category')
    lead_auditor = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Lead Auditor?')
    # named auditor_active, not active: 'active' is reserved by Odoo for record archiving
    auditor_active = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Active?')
    auditor_notes = fields.Char(string='Notes/Restrictions')

    # Inverse of project.task.auditor_id. It exists so the ORM has a real dependency
    # path to invalidate auditor_busy (and therefore display_name) when a task is
    # assigned or moved between stages.
    auditor_task_ids = fields.One2many(
        'project.task', 'auditor_id', string='Assigned Audit Tasks')
    auditor_busy = fields.Boolean(
        string='Auditor Occupied', compute='_compute_auditor_busy',
        help='Set while the auditor is assigned to a task that is still in a stage '
             'flagged as occupying the auditor.')

    @api.depends('auditor_task_ids.stage_id.auditor_busy')
    def _compute_auditor_busy(self):
        busy_ids = set()
        if self.ids:
            tasks = self.env['project.task'].sudo().search([
                ('auditor_id', 'in', self.ids),
                ('stage_id.auditor_busy', '=', True),
            ])
            busy_ids = set(tasks.mapped('auditor_id').ids)
        for partner in self:
            partner.auditor_busy = partner.id in busy_ids

    @api.depends('auditor_busy')
    @api.depends_context('show_auditor_availability')
    def _compute_display_name(self):
        """Append (Available) / (Not Available) only where it was asked for.

        The flag comes from the context of the Auditor field on a task, so the plain
        partner name is untouched everywhere else in the system.
        """
        super()._compute_display_name()
        if not self.env.context.get('show_auditor_availability'):
            return
        for partner in self:
            label = _('Not Available') if partner.auditor_busy else _('Available')
            partner.display_name = '%s (%s)' % (partner.display_name, label)
