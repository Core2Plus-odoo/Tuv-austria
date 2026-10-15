from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .audit_document import _standard_key

# Validity rules: a certification cycle runs 3 years, kept alive by annual surveillance.
CYCLE_YEARS = 3
SURVEILLANCE_MONTHS = 12
# Audit type of the project -> kind of certificate
CERTIFICATE_TYPE_BY_AUDIT = {
    'certification': 'initial',
    '1st_surveillance': 'surveillance',
    '2nd_surveillance': 'surveillance',
    'recertification': 'recertification',
}


class TuvCertificate(models.Model):
    _inherit = 'tuv.certificate'

    state = fields.Selection(selection_add=[('prepared', 'Prepared'), ('cancelled',)],
                             ondelete={'prepared': 'set default'})
    certificate_type = fields.Selection([
        ('initial', 'Initial Certification'),
        ('surveillance', 'Surveillance'),
        ('recertification', 'Recertification'),
    ], string='Certificate Type', compute='_compute_certificate_type', store=True, readonly=False,
        required=True, help='Initial: new number, 3 years with annual surveillance. Surveillance: '
                            'same certificate, confirmed for 1 more year. Recertification: new number, '
                            'new 3-year cycle.')
    previous_certificate_id = fields.Many2one(
        'tuv.certificate', string='Previous Certificate', compute='_compute_previous_certificate_id',
        store=True, readonly=False,
        domain="[('state', '=', 'prepared'), ('partner_id', '=', partner_id), ('id', '!=', id)]")
    certificate_number = fields.Char(string='Certificate Number', readonly=True, copy=False, index=True)
    issue_date = fields.Date(string='Issue Date', default=fields.Date.context_today)
    # recursive: a surveillance certificate takes its cycle from the previous certificate
    cycle_start_date = fields.Date(string='Initial Certification Date', compute='_compute_validity',
                                   store=True, readonly=False, recursive=True,
                                   help='Start of the current 3-year cycle.')
    expiry_date = fields.Date(string='Expiry Date', compute='_compute_validity', store=True,
                              readonly=False, recursive=True)
    surveillance_1_date = fields.Date(string='1st Surveillance Due', compute='_compute_validity',
                                      store=True, readonly=False, recursive=True)
    surveillance_2_date = fields.Date(string='2nd Surveillance Due', compute='_compute_validity',
                                      store=True, readonly=False, recursive=True)
    next_surveillance_date = fields.Date(string='Next Surveillance Due', compute='_compute_validity',
                                         store=True, readonly=False, recursive=True)
    validity_note = fields.Char(string='Validity', compute='_compute_validity_note')
    prepared_on = fields.Datetime(string='Confirmed On', readonly=True, copy=False)
    prepared_by = fields.Many2one('res.users', string='Confirmed By', readonly=True, copy=False)

    _unique_number = models.UniqueIndex(
        "(certificate_number, certificate_type) WHERE (certificate_number IS NOT NULL AND "
        "certificate_type != 'surveillance' AND state != 'cancelled')",
        'This certificate number is already used.',
    )

    @api.depends('project_id.md_audit_type')
    def _compute_certificate_type(self):
        for cert in self:
            cert.certificate_type = CERTIFICATE_TYPE_BY_AUDIT.get(cert.project_id.md_audit_type, 'initial')

    @api.depends('certificate_type', 'partner_id', 'standards')
    def _compute_previous_certificate_id(self):
        for cert in self:
            if cert.certificate_type == 'initial':
                cert.previous_certificate_id = False
                continue
            keys = {_standard_key(s) for s in (cert.standards or '').split(',') if s.strip()}
            candidates = self.search([('state', '=', 'prepared'), ('partner_id', '=', cert.partner_id.id),
                                      ('id', '!=', cert._origin.id or 0)], order='issue_date desc, id desc')
            cert.previous_certificate_id = candidates.filtered(
                lambda c: {_standard_key(s) for s in (c.standards or '').split(',') if s.strip()} == keys)[:1]

    @api.depends('certificate_type', 'issue_date', 'previous_certificate_id.cycle_start_date',
                 'previous_certificate_id.expiry_date')
    def _compute_validity(self):
        for cert in self:
            issue = cert.issue_date
            prev = cert.previous_certificate_id
            if not issue:
                continue
            if cert.certificate_type == 'surveillance' and prev:
                # same certificate, same cycle: only the next surveillance moves on
                cycle_start, expiry = prev.cycle_start_date, prev.expiry_date
            else:
                # initial certification or recertification: a new 3-year cycle
                cycle_start = issue
                expiry = issue + relativedelta(years=CYCLE_YEARS, days=-1)
            cert.cycle_start_date = cycle_start
            cert.expiry_date = expiry
            if cycle_start:
                cert.surveillance_1_date = cycle_start + relativedelta(months=SURVEILLANCE_MONTHS)
                cert.surveillance_2_date = cycle_start + relativedelta(months=2 * SURVEILLANCE_MONTHS)
                upcoming = [d for d in (cert.surveillance_1_date, cert.surveillance_2_date)
                            if d > issue and (not expiry or d < expiry)]
                cert.next_surveillance_date = upcoming[0] if upcoming else False

    @api.depends('certificate_type', 'expiry_date', 'next_surveillance_date')
    def _compute_validity_note(self):
        for cert in self:
            if cert.certificate_type == 'surveillance':
                cert.validity_note = _('Confirmed for 1 year after surveillance; next surveillance %s, '
                                       'certificate expires %s', cert.next_surveillance_date or '-',
                                       cert.expiry_date or '-') if cert.next_surveillance_date else \
                    _('Confirmed until expiry %s - recertification due before then', cert.expiry_date or '-')
            else:
                cert.validity_note = _('Valid 3 years until %s, subject to annual surveillance audits',
                                       cert.expiry_date or '-')

    # ------------------------------------------------------------------
    # Confirm the prepared certificate
    # ------------------------------------------------------------------
    def _confirm_problems(self):
        self.ensure_one()
        missing = [label for value, label in (
            (self.partner_id, _('Certificate Holder')), (self.standards, _('Standard(s)')),
            (self.ea_code_ids, _('EA Code')), (self.scope, _('Certified Scope')),
            (self.issue_date, _('Issue Date')), (self.expiry_date, _('Expiry Date')),
        ) if not value]
        problems = [_('missing %s', ', '.join(missing))] if missing else []
        if self.certificate_type == 'surveillance':
            prev = self.previous_certificate_id
            if not prev:
                problems.append(_('a surveillance continues an existing certificate: pick the previous one'))
            elif prev.expiry_date and self.issue_date and self.issue_date > prev.expiry_date:
                problems.append(_('the previous certificate expired on %s - this has to be a recertification',
                                  prev.expiry_date))
        return problems

    def action_confirm_certificate(self):
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_planning_team')
                or user.has_group('base.group_system')):
            raise UserError(_('Only the planning team can confirm a certificate.'))
        for cert in self:
            if cert.state != 'preparation':
                raise UserError(_('%s is not in preparation.', cert.name))
            problems = cert._confirm_problems()
            if problems:
                raise UserError(_('The certificate cannot be confirmed:\n- %s', '\n- '.join(problems)))
            # still all three conditions of 5.1 at this moment
            blockers = cert.project_id._certificate_blockers()
            if blockers:
                raise UserError(_('The certificate cannot be confirmed: %s.', '; '.join(blockers)))
            if cert.certificate_number:
                number = cert.certificate_number    # returned by the approver: keeps its number
            elif cert.certificate_type == 'surveillance':
                number = cert.previous_certificate_id.certificate_number
            else:
                number = self.env['ir.sequence'].next_by_code('tuv.certificate.number')
            cert.write({'certificate_number': number, 'state': 'prepared',
                        'prepared_on': fields.Datetime.now(), 'prepared_by': user.id})
            # the order already carries the certificate fields: keep them in step
            cert.project_id.md_sale_order_id.sudo().write({
                'certificate_no': number,
                'certification_standard': cert.standards,
                'scope_of_certification': cert.scope,
                'ea_code_ids': [(6, 0, cert.ea_code_ids.ids)],
                'issue_date': cert.issue_date,
                'expiry_date': cert.expiry_date,
                'next_surveillance': cert.next_surveillance_date,
                'certificate_status': _('Valid'),
            })
            cert.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Certificate prepared.'))
            body = _('Certificate %(number)s prepared (%(type)s): issued %(issue)s, expires %(expiry)s%(next)s.',
                     number=number, type=dict(cert._fields['certificate_type'].selection)[cert.certificate_type],
                     issue=cert.issue_date, expiry=cert.expiry_date,
                     next=_(', next surveillance %s', cert.next_surveillance_date) if cert.next_surveillance_date else '')
            cert.message_post(body=body)
            cert.project_id.sudo().message_post(body=body)
        return True
