from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .search_utils import boolean_search_positive, search_values

REGISTER_STATUS = [
    ('valid', 'Valid'),
    ('expired', 'Expired'),
    ('superseded', 'Superseded'),
    ('cancelled', 'Cancelled'),
]
ISSUED_STATES = ('approved', 'printed', 'dispatched')


class CertificateRegister(models.Model):
    """The certificate register: one entry per issued certificate, kept for PNAC.

    Everything a certificate stated is copied in at the moment it is issued, so the
    register keeps showing what was certified even if the client's contact or the
    project changes later. Entries cannot be edited or deleted - by anyone.
    """

    _name = 'tuv.certificate.register'
    _description = 'Certificate Register'
    _order = 'issue_date desc, id desc'

    name = fields.Char(string='Certificate Number', required=True, readonly=True, index=True)
    certificate_id = fields.Many2one('tuv.certificate', string='Certificate', required=True,
                                     readonly=True, ondelete='restrict', index=True)
    project_id = fields.Many2one('project.project', string='Audit Project', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client', readonly=True, index=True)
    certificate_type = fields.Selection([
        ('initial', 'Initial Certification'),
        ('surveillance', 'Surveillance'),
        ('recertification', 'Recertification'),
    ], string='Type', readonly=True)

    standards = fields.Char(string='Standard(s)', readonly=True)
    ea_codes = fields.Char(string='EA Code(s)', readonly=True)
    scope = fields.Text(string='Certified Scope', readonly=True)
    issue_date = fields.Date(string='Issue Date', readonly=True)
    expiry_date = fields.Date(string='Expiry Date', readonly=True)
    cycle_start_date = fields.Date(string='Initial Certification Date', readonly=True)
    next_surveillance_date = fields.Date(string='Next Surveillance Due', readonly=True)

    client_name = fields.Char(string='Client Name', readonly=True)
    client_address = fields.Char(string='Client Address', readonly=True)
    client_city = fields.Char(string='City', readonly=True)
    client_country = fields.Char(string='Country', readonly=True)
    client_ntn = fields.Char(string='NTN', readonly=True)
    client_email = fields.Char(string='Email', readonly=True)
    client_phone = fields.Char(string='Phone', readonly=True)
    site_address = fields.Text(string='Certified Site(s)', readonly=True)

    lead_auditor = fields.Char(string='Lead Auditor', readonly=True)
    approved_by = fields.Char(string='Approved By', readonly=True)
    technical_review = fields.Char(string='Technical Review', readonly=True)
    registered_on = fields.Datetime(string='Registered On', readonly=True)
    superseded_by_id = fields.Many2one('tuv.certificate.register', string='Superseded By', readonly=True)

    # compute_sudo: a read-only register viewer (PNAC) has no access to certificates themselves
    status = fields.Selection(REGISTER_STATUS, string='Status', compute='_compute_status',
                              search='_search_status', compute_sudo=True)
    is_current = fields.Boolean(string='Current Entry', compute='_compute_is_current',
                                search='_search_is_current', compute_sudo=True,
                                help='The latest entry of its certificate number that is not superseded.')
    issue_year = fields.Char(string='Year', compute='_compute_issue_year', store=True)

    _unique_certificate = models.UniqueIndex('(certificate_id)', 'This certificate is already registered.')

    @api.depends('issue_date')
    def _compute_issue_year(self):
        for entry in self:
            entry.issue_year = str(entry.issue_date.year) if entry.issue_date else False

    @api.depends('certificate_id.state', 'superseded_by_id', 'expiry_date')
    def _compute_status(self):
        today = fields.Date.context_today(self)
        for entry in self:
            if entry.certificate_id.state == 'cancelled':
                entry.status = 'cancelled'
            elif entry.superseded_by_id:
                entry.status = 'superseded'
            elif entry.expiry_date and entry.expiry_date < today:
                entry.status = 'expired'
            else:
                entry.status = 'valid'

    def _search_status(self, operator, value):
        today = fields.Date.context_today(self)
        domains = {
            'cancelled': [('certificate_id.state', '=', 'cancelled')],
            'superseded': [('certificate_id.state', '!=', 'cancelled'), ('superseded_by_id', '!=', False)],
            'expired': [('certificate_id.state', '!=', 'cancelled'), ('superseded_by_id', '=', False),
                        ('expiry_date', '<', today)],
            'valid': [('certificate_id.state', '!=', 'cancelled'), ('superseded_by_id', '=', False),
                      '|', ('expiry_date', '=', False), ('expiry_date', '>=', today)],
        }
        ids = set()
        for val in search_values(value):
            if val in domains:
                ids |= set(self.sudo().search(domains[val]).ids)
        if operator in ('!=', 'not in'):
            return [('id', 'not in', list(ids))]
        return [('id', 'in', list(ids))]

    def _current_ids(self):
        # the newest entry of every certificate number that has not been superseded
        self.env.cr.execute("""
            SELECT MAX(id) FROM tuv_certificate_register GROUP BY name
        """)
        latest = {row[0] for row in self.env.cr.fetchall()}
        return set(self.browse(list(latest)).filtered(lambda e: not e.superseded_by_id).ids)

    def _compute_is_current(self):
        current = self._current_ids()
        for entry in self:
            entry.is_current = entry.id in current

    def _search_is_current(self, operator, value):
        positive = boolean_search_positive(operator, value)
        return [('id', 'in' if positive else 'not in', list(self._current_ids()))]

    # ------------------------------------------------------------------
    # The register is append-only
    # ------------------------------------------------------------------
    def write(self, vals):
        if not self.env.context.get('tuv_register_internal') or set(vals) - {'superseded_by_id'}:
            raise UserError(_('The certificate register cannot be changed: it is the record kept for '
                              'accreditation (PNAC) review.'))
        return super().write(vals)

    def unlink(self):
        raise UserError(_('Entries of the certificate register can never be deleted.'))

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    @api.model
    def _register_certificates(self, certificates):
        """Register issued certificates that are not in the register yet."""
        created = self.browse()
        for cert in certificates.sudo():
            if cert.state not in ISSUED_STATES or self.sudo().search_count([('certificate_id', '=', cert.id)]):
                continue
            client = cert.partner_id
            entry = self.sudo().create({
                'name': cert.certificate_number,
                'certificate_id': cert.id,
                'project_id': cert.project_id.id,
                'partner_id': client.id,
                'certificate_type': cert.certificate_type,
                'standards': cert.standards,
                'ea_codes': ', '.join(n.strip() for n in cert.ea_code_ids.mapped('name')),
                'scope': cert.scope,
                'issue_date': cert.issue_date,
                'expiry_date': cert.expiry_date,
                'cycle_start_date': cert.cycle_start_date,
                'next_surveillance_date': cert.next_surveillance_date,
                'client_name': client.name,
                'client_address': ', '.join(p for p in (client.street, client.street2) if p),
                'client_city': client.city,
                'client_country': client.country_id.name,
                'client_ntn': client.vat,
                'client_email': client.email,
                'client_phone': client.phone,
                'site_address': cert.site_address,
                'lead_auditor': cert.lead_auditor_id.name,
                'approved_by': cert.approved_by.name,
                'technical_review': cert.technical_review_id.name,
                'registered_on': fields.Datetime.now(),
            })
            # a recertification replaces the previous certificate in the register
            if cert.certificate_type == 'recertification' and cert.previous_certificate_id:
                old = self.sudo().search([('name', '=', cert.previous_certificate_id.certificate_number),
                                          ('superseded_by_id', '=', False), ('id', '!=', entry.id)])
                old.with_context(tuv_register_internal=True).write({'superseded_by_id': entry.id})
            cert.message_post(body=_('Entered in the certificate register (%s).', entry.name))
            created |= entry
        return created

    @api.model
    def _cron_register_completeness(self):
        """Daily: no issued certificate may be missing from the register."""
        issued = self.env['tuv.certificate'].sudo().search([('state', 'in', ISSUED_STATES)])
        return len(self._register_certificates(issued))

    def action_print_register(self):
        records = self or self.search([])
        return self.env.ref('tuv_austria_customization.action_report_certificate_register').report_action(records)


class TuvCertificate(models.Model):
    _inherit = 'tuv.certificate'

    register_ids = fields.One2many('tuv.certificate.register', 'certificate_id', string='Register Entry')

    def action_approve_certificate(self):
        res = super().action_approve_certificate()
        # approved = issued: it goes into the register at once
        self.env['tuv.certificate.register']._register_certificates(self)
        return res
