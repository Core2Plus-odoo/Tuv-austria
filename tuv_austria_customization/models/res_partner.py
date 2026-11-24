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

    # Inverses of the three audit-team fields on project.task. They exist so the ORM
    # has a real dependency path to invalidate auditor_busy (and therefore
    # display_name) when a task is assigned or moved between stages.
    auditor_task_ids = fields.One2many(
        'project.task', 'auditor_id', string='Assigned Audit Tasks')
    co_auditor_task_ids = fields.One2many(
        'project.task', 'md_co_auditor_id', string='Assigned Co-Auditor Tasks')
    trainee_task_ids = fields.One2many(
        'project.task', 'md_trainee_id', string='Assigned Trainee Tasks')
    auditor_busy = fields.Boolean(
        string='Auditor Occupied', compute='_compute_auditor_busy',
        help='Set while the contact is the auditor, co-auditor or trainee of a task '
             'that is still in a stage flagged as occupying the audit team.')

    def _get_busy_auditor_ids(self, exclude_task_ids=None):
        """Ids of the partners in self that are still tied up on an open task.

        A partner counts as busy when any task carries it as auditor, co-auditor or
        trainee while sitting in a stage whose "Occupies The Auditor" flag is on -
        i.e. before Certificate Issuance / Feedback & Continuous Improvement.
        """
        if not self.ids:
            return set()
        domain = [
            ('stage_id.auditor_busy', '=', True),
            '|', '|',
            ('auditor_id', 'in', self.ids),
            ('md_co_auditor_id', 'in', self.ids),
            ('md_trainee_id', 'in', self.ids),
        ]
        if exclude_task_ids:
            domain.append(('id', 'not in', exclude_task_ids))
        tasks = self.env['project.task'].sudo().search(domain)
        busy_ids = set()
        for role in ('auditor_id', 'md_co_auditor_id', 'md_trainee_id'):
            busy_ids |= set(tasks.mapped(role).ids)
        return busy_ids & set(self.ids)

    @api.depends('auditor_task_ids.stage_id.auditor_busy',
                 'co_auditor_task_ids.stage_id.auditor_busy',
                 'trainee_task_ids.stage_id.auditor_busy')
    def _compute_auditor_busy(self):
        busy_ids = self._get_busy_auditor_ids()
        for partner in self:
            partner.auditor_busy = partner.id in busy_ids

    @api.depends('auditor_busy')
    @api.depends_context('show_auditor_availability', 'availability_exclude_task')
    def _compute_display_name(self):
        """Append (Available) / (Not Available) only where it was asked for.

        The flag comes from the context of the audit-team fields on a task, so the
        plain partner name is untouched everywhere else in the system. Those fields
        also pass their own task id, which is left out of the check: a contact must
        not be reported as busy because of the very task being edited.
        """
        super()._compute_display_name()
        if not self.env.context.get('show_auditor_availability'):
            return
        current_task = self.env.context.get('availability_exclude_task')
        # an unsaved task sends id = False, and a virtual id is not searchable
        if isinstance(current_task, int) and current_task > 0:
            busy_ids = self._get_busy_auditor_ids(exclude_task_ids=[current_task])
        else:
            busy_ids = {partner.id for partner in self if partner.auditor_busy}
        for partner in self:
            label = _('Not Available') if partner.id in busy_ids else _('Available')
            partner.display_name = '%s (%s)' % (partner.display_name, label)
