import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# The Sales Tax Invoice follows the commercial invoice within this many hours.
STI_HOURS = 48


class ResPartner(models.Model):
    _inherit = 'res.partner'

    strn = fields.Char(string='STRN', help='Sales Tax Registration Number')


class SalesTaxInvoice(models.Model):
    """The Sales Tax Invoice issued by the Finance / Tax Manager for a commercial invoice."""

    _name = 'tuv.sales.tax.invoice'
    _description = 'Sales Tax Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='STI Number', required=True, copy=False, readonly=True, default='/')
    commercial_invoice_id = fields.Many2one('account.move', string='Commercial Invoice', required=True,
                                            readonly=True, ondelete='restrict', index=True)
    project_id = fields.Many2one('project.project', string='Audit Project', readonly=True, index=True)
    company_id = fields.Many2one(related='commercial_invoice_id.company_id', store=True)
    partner_id = fields.Many2one(related='commercial_invoice_id.partner_id', string='Buyer', store=True)
    buyer_ntn = fields.Char(related='partner_id.vat', string='Buyer NTN')
    buyer_cnic = fields.Char(related='partner_id.cnic', string='Buyer CNIC')
    buyer_strn = fields.Char(related='partner_id.strn', string='Buyer STRN', readonly=False)
    supplier_ntn = fields.Char(related='company_id.partner_id.vat', string='Supplier NTN')
    supplier_strn = fields.Char(related='company_id.partner_id.strn', string='Supplier STRN')

    currency_id = fields.Many2one(related='commercial_invoice_id.currency_id', store=True)
    invoice_date = fields.Date(related='commercial_invoice_id.invoice_date', string='Commercial Invoice Date')
    amount_untaxed = fields.Monetary(related='commercial_invoice_id.amount_untaxed',
                                     string='Value Excluding Sales Tax', store=True)
    amount_tax = fields.Monetary(related='commercial_invoice_id.amount_tax', string='Sales Tax', store=True)
    amount_total = fields.Monetary(related='commercial_invoice_id.amount_total',
                                   string='Value Including Sales Tax', store=True)
    tax_name = fields.Char(string='Sales Tax', compute='_compute_tax', store=True)
    tax_rate = fields.Float(string='Rate %', compute='_compute_tax', store=True)
    description = fields.Char(compute='_compute_tax', store=True, string='Description')

    state = fields.Selection([
        ('draft', 'To Issue'),
        ('issued', 'Issued'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    due_on = fields.Datetime(string='Due By', readonly=True,
                             help='%s hours after the commercial invoice.' % STI_HOURS)
    issued_on = fields.Datetime(string='Issued On', readonly=True, copy=False)
    issued_by = fields.Many2one('res.users', string='Issued By (Tax Manager)', readonly=True, copy=False)
    issued_on_time = fields.Boolean(string='Issued Within 48 Hours', readonly=True, copy=False)
    tax_period = fields.Char(string='Tax Period', compute='_compute_tax_period', store=True,
                             help='Month of the sales tax return this invoice belongs to.')
    sent_to_client = fields.Boolean(string='Sent To Client', readonly=True, copy=False)
    is_overdue = fields.Boolean(compute='_compute_is_overdue', search='_search_is_overdue', string='Overdue')
    overdue_notified = fields.Boolean(copy=False)
    notes = fields.Text(string='Tax Manager Notes')

    # one serial, one Sales Tax Invoice - drafts all carry '/' until issued
    _unique_name = models.UniqueIndex(
        "(company_id, name) WHERE (name != '/')",
        'This Sales Tax Invoice number is already used.',
    )

    @api.depends('commercial_invoice_id.invoice_line_ids.tax_ids',
                 'commercial_invoice_id.invoice_line_ids.name')
    def _compute_tax(self):
        for sti in self:
            lines = sti.commercial_invoice_id.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            taxes = lines.tax_ids.filtered(lambda t: t.amount_type == 'percent' and t.amount > 0)
            sti.tax_name = ', '.join(taxes.mapped('name')) or False
            sti.tax_rate = taxes[:1].amount
            sti.description = lines[:1].name

    @api.depends('issued_on')
    def _compute_tax_period(self):
        for sti in self:
            sti.tax_period = sti.issued_on.strftime('%Y-%m') if sti.issued_on else False

    @api.depends('state', 'due_on')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for sti in self:
            sti.is_overdue = sti.state == 'draft' and bool(sti.due_on) and sti.due_on < now

    def _search_is_overdue(self, operator, value):
        domain = [('state', '=', 'draft'), ('due_on', '<', fields.Datetime.now())]
        # a boolean filter arrives as ('in', [True]) in Odoo 19
        values = value if isinstance(value, (list, tuple, set)) else [value]
        positive = any(values)
        if operator in ('!=', 'not in'):
            positive = not positive
        return domain if positive else ['!', '&'] + domain

    @api.model
    def _tax_managers(self):
        group = self.env.ref('tuv_austria_customization.group_tax_manager', raise_if_not_found=False)
        return self.env['res.users'].search([('all_group_ids', 'in', group.id)]) if group else self.env['res.users']

    @api.model_create_multi
    def create(self, vals_list):
        stis = super().create(vals_list)
        managers = self._tax_managers()
        for sti in stis:
            for user in managers or self.env.user:
                sti.activity_schedule(
                    'mail.mail_activity_data_todo', user_id=user.id, date_deadline=sti.due_on.date(),
                    summary=_('Issue Sales Tax Invoice for %(inv)s by %(due)s',
                              inv=sti.commercial_invoice_id.name, due=fields.Datetime.to_string(sti.due_on)))
        return stis

    # ------------------------------------------------------------------
    # Issue
    # ------------------------------------------------------------------
    def _issue_problems(self):
        self.ensure_one()
        problems = []
        if self.commercial_invoice_id.state != 'posted':
            problems.append(_('the commercial invoice is not posted'))
        if not self.amount_tax:
            problems.append(_('the commercial invoice carries no sales tax'))
        if not (self.buyer_ntn or self.buyer_cnic):
            problems.append(_('the buyer has neither NTN nor CNIC'))
        if not self.supplier_strn:
            problems.append(_('the company STRN is missing (Settings > Companies > contact)'))
        if not self.supplier_ntn:
            problems.append(_('the company NTN is missing'))
        return problems

    def action_issue(self):
        user = self.env.user
        if not (user.has_group('tuv_austria_customization.group_tax_manager')
                or user.has_group('base.group_system')):
            raise UserError(_('Only the Finance / Tax Manager can issue a Sales Tax Invoice.'))
        for sti in self:
            if sti.state != 'draft':
                raise UserError(_('%s is not waiting to be issued.', sti.name))
            problems = sti._issue_problems()
            if problems:
                raise UserError(_('The Sales Tax Invoice cannot be issued:\n- %s', '\n- '.join(problems)))
            now = fields.Datetime.now()
            sti.write({
                'name': self.env['ir.sequence'].next_by_code('tuv.sales.tax.invoice') or '/',
                'state': 'issued', 'issued_on': now, 'issued_by': user.id,
                'issued_on_time': not sti.due_on or now <= sti.due_on,
            })
            sti.activity_feedback(['mail.mail_activity_data_todo'], feedback=_('Sales Tax Invoice issued.'))
            timing = _('within 48 hours') if sti.issued_on_time else _('after the 48 hours')
            for record in (sti, sti.commercial_invoice_id, sti.project_id):
                if record:
                    record.sudo().message_post(body=_(
                        'Sales Tax Invoice %(sti)s issued by %(user)s %(timing)s for commercial invoice '
                        '%(inv)s (sales tax %(tax)s).', sti=sti.name, user=user.name, timing=timing,
                        inv=sti.commercial_invoice_id.name, tax=sti.amount_tax))
            sti._send_to_client()
        return True

    def _send_to_client(self):
        template = self.env.ref('tuv_austria_customization.mail_template_sales_tax_invoice')
        for sti in self:
            if not sti.partner_id.email:
                sti.message_post(body=_('Not e-mailed: the client has no e-mail address.'))
                continue
            sti.message_post_with_source(template, partner_ids=sti.partner_id.ids,
                                         subtype_xmlid='mail.mt_comment', message_type='comment')
            sti.sent_to_client = True

    def action_send_to_client(self):
        self.filtered(lambda s: s.state == 'issued')._send_to_client()
        return True

    def action_cancel(self):
        for sti in self:
            if sti.state == 'issued' and not self.env.user.has_group('base.group_system'):
                raise UserError(_('An issued Sales Tax Invoice can only be cancelled by an administrator.'))
            sti.write({'state': 'cancelled'})
            sti.activity_unlink(['mail.mail_activity_data_todo'])
        return True

    @api.model
    def _cron_sales_tax_invoices(self):
        """Hourly: draft the missing ones and flag those past their 48 hours, once."""
        self.env['project.project'].search([('commercial_invoice_id', '!=', False)])._create_sales_tax_invoices()
        overdue = self.search([('is_overdue', '=', True), ('overdue_notified', '=', False)])
        for sti in overdue:
            sti.message_post(body=_('Overdue: the Sales Tax Invoice was due by %s.', sti.due_on))
            for user in self._tax_managers() or self.env.user:
                sti.activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                                      summary=_('OVERDUE Sales Tax Invoice for %s', sti.commercial_invoice_id.name))
        overdue.write({'overdue_notified': True})
        return len(overdue)


class AccountMove(models.Model):
    _inherit = 'account.move'

    sales_tax_invoice_ids = fields.One2many('tuv.sales.tax.invoice', 'commercial_invoice_id',
                                            string='Sales Tax Invoices')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sales_tax_invoice_ids = fields.One2many('tuv.sales.tax.invoice', 'project_id', string='Sales Tax Invoices')
    # The commercial invoice, as tracked on the project's Invoicing tab
    ci_invoice_date = fields.Date(related='commercial_invoice_id.invoice_date', string='Invoice Date')
    ci_currency_id = fields.Many2one(related='commercial_invoice_id.currency_id')
    ci_amount_total = fields.Monetary(related='commercial_invoice_id.amount_total', string='Total',
                                      currency_field='ci_currency_id')
    ci_amount_tax = fields.Monetary(related='commercial_invoice_id.amount_tax', string='Sales Tax',
                                    currency_field='ci_currency_id')
    ci_state = fields.Selection(related='commercial_invoice_id.state', string='Invoice Status')
    ci_payment_state = fields.Selection(related='commercial_invoice_id.payment_state', string='Payment')
    ci_is_sent = fields.Boolean(related='commercial_invoice_id.is_move_sent', string='Sent To Client')
    ci_created_on = fields.Datetime(related='commercial_invoice_id.create_date', string='Generated On')

    def _create_sales_tax_invoices(self):
        """Draft the Sales Tax Invoice of every taxed commercial invoice that has none."""
        STI = self.env['tuv.sales.tax.invoice'].sudo()
        for project in self.sudo():
            invoice = project.commercial_invoice_id
            if (not invoice or invoice.state != 'posted' or not invoice.amount_tax
                    or invoice.sales_tax_invoice_ids.filtered(lambda s: s.state != 'cancelled')):
                continue
            sti = STI.create({
                'commercial_invoice_id': invoice.id,
                'project_id': project.id,
                'due_on': invoice.create_date + timedelta(hours=STI_HOURS),
            })
            project.message_post(body=_('Sales Tax Invoice drafted for %(inv)s; the Tax Manager has to '
                                        'issue it by %(due)s.', inv=invoice.name,
                                        due=fields.Datetime.to_string(sti.due_on)))

    def _generate_commercial_invoice(self):
        res = super()._generate_commercial_invoice()
        self._create_sales_tax_invoices()
        return res
