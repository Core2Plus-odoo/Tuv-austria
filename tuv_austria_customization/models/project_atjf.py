from odoo import _, api, fields, models
from odoo.exceptions import UserError

# What the ATJF prints and what the reviewer signs off. Every one of these already
# lives on the project (Mandays tab, audit team, the order's application form), so
# the ATJF reads them instead of keeping a copy. Changing any of them after the
# review sends the ATJF back to Draft: an approved form must match what is planned.
ATJF_FIELDS = (
    'auditor_id', 'md_co_auditor_id', 'md_trainee_id', 'md_other_participants',
    'ea_code_ids',
    'md_standard_1', 'md_standard_2', 'md_standard_3', 'md_standard_other',
    'md_audit_duration', 'md4_total_cert', 'md4_total_surv1', 'md4_total_surv2',
    'md_audit_date_st1', 'md_audit_date_st2', 'md_audit_date_surveillance',
    'md_audit_date_recert',
)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    atjf_state = fields.Selection([
        ('draft', 'Draft'),
        ('to_review', 'Waiting for Review'),
        ('reviewed', 'Reviewed'),
    ], string='ATJF Status', default='draft', required=True, copy=False, tracking=True)
    atjf_prepared_by = fields.Many2one('res.users', string='Prepared By', readonly=True, copy=False)
    atjf_prepared_on = fields.Datetime(string='Prepared On', readonly=True, copy=False)
    atjf_reviewed_by = fields.Many2one('res.users', string='Reviewed By', readonly=True, copy=False)
    atjf_reviewed_on = fields.Datetime(string='Reviewed On', readonly=True, copy=False)
    atjf_review_notes = fields.Text(string='Review Notes', copy=False)

    # Client site, as the ATJF prints it: the audit site of the application form,
    # falling back on the client's own address when sales left it empty.
    atjf_site_address = fields.Text(string='Client Site Address', compute='_compute_atjf_site_address')
    # Standard(s) of the ATJF: the order's standard plus those picked on the Mandays tab.
    atjf_standards = fields.Char(string='ATJF Standard(s)', compute='_compute_atjf_standards')

    @api.depends('certification_standard', 'md_standard_1', 'md_standard_2',
                 'md_standard_3', 'md_standard_other')
    def _compute_atjf_standards(self):
        labels = dict(self._fields['md_standard_1'].selection)
        for project in self:
            names = [project.certification_standard] + [
                labels.get(code) for code in (
                    project.md_standard_1, project.md_standard_2, project.md_standard_3)
            ] + [project.md_standard_other]
            # the order says "ISO 9001:2015", the Mandays list "ISO9001:2015": one standard
            unique = {}
            for name in filter(None, names):
                unique.setdefault(name.replace(' ', '').lower(), name)
            project.atjf_standards = ', '.join(unique.values()) or False

    @api.depends('audit_site', 'md_street', 'md_street2', 'md_city', 'md_zip',
                 'md_state_id', 'md_country_id')
    def _compute_atjf_site_address(self):
        for project in self:
            address = ', '.join(part for part in (
                project.md_street, project.md_street2, project.md_city, project.md_zip,
                project.md_state_id.name, project.md_country_id.name) if part)
            project.atjf_site_address = project.audit_site or address or False

    # ------------------------------------------------------------------
    # Prepare -> Review
    # ------------------------------------------------------------------
    def _atjf_missing(self):
        """Labels of what the ATJF cannot go without."""
        self.ensure_one()
        checks = [
            (self.auditor_id, _('Auditor (LA)')),
            (self.ea_code_ids, _('EA Code')),
            (self.atjf_standards, _('Standard')),
            (self.md_audit_duration or self.md4_total_cert, _('Man-days')),
            (self.md_audit_date_st1 or self.md_audit_date_st2 or self.md_audit_date_surveillance
             or self.md_audit_date_recert, _('Audit Date')),
            (self.atjf_site_address, _('Client Site Address')),
        ]
        return [label for value, label in checks if not value]

    def action_atjf_submit(self):
        self.ensure_one()
        if self.atjf_state != 'draft':
            raise UserError(_('The ATJF of %s is already submitted.', self.name))
        missing = self._atjf_missing()
        if missing:
            raise UserError(_('Fill these in before submitting the ATJF:\n- %s',
                              '\n- '.join(missing)))
        self.write({
            'atjf_state': 'to_review',
            'atjf_prepared_by': self.env.user.id,
            'atjf_prepared_on': fields.Datetime.now(),
            'atjf_reviewed_by': False,
            'atjf_reviewed_on': False,
        })
        self.message_post(body=_('ATJF prepared by %s and sent for review.', self.env.user.name))
        return True

    def action_atjf_approve(self):
        self.ensure_one()
        if self.atjf_state != 'to_review':
            raise UserError(_('Only an ATJF waiting for review can be approved.'))
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_planning_team')
                or user.has_group('base.group_system')):
            raise UserError(_('Only the planning team can review an ATJF.'))
        self.write({
            'atjf_state': 'reviewed',
            'atjf_reviewed_by': self.env.user.id,
            'atjf_reviewed_on': fields.Datetime.now(),
        })
        self.message_post(body=_('ATJF reviewed and approved by %s.', self.env.user.name))
        return True

    @api.model
    def _atjf_draft_values(self):
        # a sign-off belongs to the version that was reviewed, not to the next one
        return {'atjf_state': 'draft', 'atjf_reviewed_by': False, 'atjf_reviewed_on': False}

    def action_atjf_reset(self):
        """Send the ATJF back to Draft so it can be corrected."""
        self.ensure_one()
        self.write(self._atjf_draft_values())
        self.message_post(body=_('ATJF sent back to draft by %s.', self.env.user.name))
        return True

    def write(self, vals):
        changed = set(vals) & set(ATJF_FIELDS)
        reopened = self.filtered(lambda p: p.atjf_state != 'draft') if changed else self.browse()
        res = super().write(vals)
        if reopened and 'atjf_state' not in vals:
            super(ProjectProject, reopened).write(self._atjf_draft_values())
            for project in reopened:
                project.message_post(body=_(
                    'ATJF back to draft: %s changed after it was prepared.',
                    ', '.join(self._fields[name].string for name in sorted(changed))))
        return res
