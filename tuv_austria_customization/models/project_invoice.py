import logging
import re
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

# Maximum credit the client gets: payment is due this many days after the audit.
CREDIT_DAYS = 7

# Which contract year and which service product an audit is invoiced with.
AUDIT_INVOICING = {
    'certification': ('y1', 'Initial Certification Audit'),
    '1st_surveillance': ('y2', 'Surveillance Audit — Year 1'),
    '2nd_surveillance': ('y3', 'Surveillance Audit — Year 2'),
    'recertification': ('y1', 'Re-Certification Audit'),
}
# How a province is written on the contract -> how its tax is named in Odoo
PROVINCE_TAX_KEYS = {
    'punjab': 'pun', 'sindh': 'sindh', 'khyber': 'kp', 'kp': 'kp', 'balochistan': 'balo',
    'baluchistan': 'balo', 'islamabad': 'ict', 'ict': 'ict', 'ajk': 'ajk', 'kashmir': 'ajk',
}


def _amount(text):
    """'250,000' / 'PKR 250,000.00' -> 250000.0 (the contract amounts are typed in)."""
    digits = re.sub(r'[^\d.]', '', text or '')
    try:
        return float(digits) if digits else 0.0
    except ValueError:
        return 0.0


class AccountMove(models.Model):
    _inherit = 'account.move'

    tuv_project_id = fields.Many2one('project.project', string='Audit Project', index=True,
                                     copy=False, readonly=True)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    commercial_invoice_id = fields.Many2one('account.move', string='Commercial Invoice',
                                            readonly=True, copy=False)
    commercial_invoice_ids = fields.One2many('account.move', 'tuv_project_id', string='Invoices')
    commercial_invoice_count = fields.Integer(compute='_compute_commercial_invoice_count')
    invoice_blocked_reason = fields.Char(string='Invoice Not Generated', readonly=True, copy=False)

    @api.depends('commercial_invoice_ids')
    def _compute_commercial_invoice_count(self):
        for project in self:
            project.commercial_invoice_count = len(project.commercial_invoice_ids)

    # ------------------------------------------------------------------
    # What the invoice is made of
    # ------------------------------------------------------------------
    def _invoice_terms(self):
        """(product, fee, man-days, tax, contract tax amount) of this audit, from its contract."""
        self.ensure_one()
        order = self.md_sale_order_id
        year, product_name = AUDIT_INVOICING.get(self.md_audit_type or 'certification',
                                                 AUDIT_INVOICING['certification'])
        product = self.env['product.product'].search([('name', '=', product_name)], limit=1)
        fee = _amount(order['contract_fee_%s' % year])
        mandays = order['contract_mandays_%s' % year] or ''
        tax_amount = _amount(order['contract_tax_%s' % year])
        return product, fee, mandays, self._invoice_tax(fee, tax_amount, order.contract_tax_province), tax_amount

    def _invoice_tax(self, fee, tax_amount, province_text):
        """The Odoo sales tax matching the contract: rate from the amounts, province from the label."""
        if not tax_amount:
            return self.env['account.tax']
        rate = round(tax_amount * 100.0 / fee, 1) if fee else 0.0
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', province_text or '')
        if not rate and match:
            rate = float(match.group(1))
        taxes = self.env['account.tax'].search([
            ('type_tax_use', '=', 'sale'), ('amount_type', '=', 'percent'),
            ('company_id', '=', self.company_id.id)]).filtered(
            lambda t: float_compare(t.amount, rate, precision_digits=2) == 0)
        text = (province_text or '').lower()
        for word, key in PROVINCE_TAX_KEYS.items():
            if re.search(r'\b%s\b' % word, text):
                provincial = taxes.filtered(lambda t: key in t.name.lower())
                if provincial:
                    return provincial[:1]
        return taxes[:1]

    def _invoice_problems(self):
        self.ensure_one()
        problems = []
        if not self.md_sale_order_id:
            problems.append(_('the project has no sales order'))
            return problems
        product, fee, *_rest = self._invoice_terms()
        if not product:
            problems.append(_('the service product for this audit type is missing'))
        if not fee:
            problems.append(_('the contract fee for this audit year is empty'))
        return problems

    # ------------------------------------------------------------------
    # Generate, post, send
    # ------------------------------------------------------------------
    def _generate_commercial_invoice(self):
        """Create, post and e-mail the commercial invoice of a completed audit."""
        for project in self.sudo():
            if project.commercial_invoice_id or project.audit_state != 'done':
                continue
            problems = project._invoice_problems()
            if problems:
                reason = '; '.join(problems)
                if project.invoice_blocked_reason != reason:
                    project.invoice_blocked_reason = reason
                    project.message_post(body=_('Commercial invoice NOT generated: %s.', reason))
                    project.activity_schedule(
                        'mail.mail_activity_data_todo', user_id=(project.user_id or self.env.user).id,
                        summary=_('Commercial invoice blocked - %s', project.name), note=reason)
                continue
            product, fee, mandays, tax, contract_tax = project._invoice_terms()
            order = project.md_sale_order_id
            dates = ' / '.join(fields.Date.to_string(d) for d in (
                project.md_audit_date_st1, project.md_audit_date_st2) if d)
            description = '%s - %s%s%s' % (
                product.name, project.atjf_standards or '',
                _(' - audit %s', dates) if dates else '',
                _(' (%s man-days)', mandays) if mandays else '')
            line = {
                'product_id': product.id, 'name': description, 'quantity': 1,
                'price_unit': fee, 'tax_ids': [(6, 0, tax.ids)],
            }
            if project.account_id:
                line['analytic_distribution'] = {str(project.account_id.id): 100}
            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': project.partner_id.id,
                'company_id': project.company_id.id,
                'currency_id': order.currency_id.id,
                'invoice_date': fields.Date.context_today(project),
                # maximum credit: 7 days from the job execution (the audit completion)
                'invoice_payment_term_id': False,
                'invoice_date_due': max(project.audit_completed_on.date() + timedelta(days=CREDIT_DAYS),
                                        fields.Date.context_today(project)),
                # the project usually carries the order's name, then once is enough
                'invoice_origin': order.name if order.name == project.name
                else '%s / %s' % (order.name, project.name),
                'ref': order.tuv_sequence or order.name,
                'business_line': _('Certification - %s', project.atjf_standards or ''),
                'tuv_project_id': project.id,
                'invoice_user_id': (order.user_id or project.user_id).id,
                'invoice_line_ids': [(0, 0, line)],
            })
            invoice.action_post()
            project.write({'commercial_invoice_id': invoice.id, 'invoice_blocked_reason': False})
            note = ''
            if contract_tax and float_compare(invoice.amount_tax, contract_tax, precision_digits=0) != 0:
                note = _(' Sales tax %(odoo)s differs from the contract (%(contract)s): check the tax.',
                         odoo=invoice.amount_tax, contract=contract_tax)
            project.message_post(body=_('Commercial invoice %(name)s generated: %(amount)s %(cur)s.%(note)s',
                                        name=invoice.name, amount=invoice.amount_total,
                                        cur=invoice.currency_id.name, note=note))
            project._send_commercial_invoice()

    def _send_commercial_invoice(self):
        template = self.env.ref('tuv_austria_customization.mail_template_commercial_invoice')
        for project in self.sudo():
            invoice = project.commercial_invoice_id
            if not invoice.partner_id.email:
                project.message_post(body=_('Commercial invoice %s was not e-mailed: the client has no '
                                            'e-mail address.', invoice.name))
                project.activity_schedule(
                    'mail.mail_activity_data_todo', user_id=(project.user_id or self.env.user).id,
                    summary=_('Send commercial invoice %s to the client', invoice.name))
                continue
            invoice.message_post_with_source(
                template, partner_ids=invoice.partner_id.ids,
                subtype_xmlid='mail.mt_comment', message_type='comment')
            invoice.is_move_sent = True
            project.message_post(body=_('Commercial invoice %(name)s sent to %(email)s.',
                                        name=invoice.name, email=invoice.partner_id.email))

    def _generate_commercial_invoice_safe(self):
        """Generate without ever failing the caller.

        Invoicing rides on the audit completion and on the hourly job: an accounting or
        mailing problem must not stop the auditor from completing the audit, nor one
        project stop the others. It is logged on the project and the job retries.
        """
        for project in self:
            try:
                with self.env.cr.savepoint():
                    project._generate_commercial_invoice()
            except Exception as err:  # noqa: BLE001 - reported on the project, retried hourly
                _logger.exception('Commercial invoice of %s failed', project.name)
                project.sudo().message_post(body=_(
                    'Commercial invoice could not be generated or sent: %s. It will be retried '
                    'by the hourly job.', err))

    def action_audit_complete(self):
        res = super().action_audit_complete()
        self._generate_commercial_invoice_safe()
        return res

    def action_generate_commercial_invoice(self):
        """Button: generate now (e.g. once a missing contract fee has been filled in)."""
        self.invoice_blocked_reason = False
        self._generate_commercial_invoice()
        return True

    def action_view_commercial_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_out_invoice_type')
        action['domain'] = [('tuv_project_id', '=', self.id)]
        action['context'] = {'default_move_type': 'out_invoice'}
        if self.commercial_invoice_count == 1:
            action.update(views=[(False, 'form')], res_id=self.commercial_invoice_ids.id)
        return action

    @api.model
    def _cron_generate_commercial_invoices(self):
        """Hourly safety net: every completed audit is invoiced within 24 hours."""
        projects = self.search([('audit_state', '=', 'done'), ('commercial_invoice_id', '=', False),
                                ('audit_completed_on', '!=', False)])
        projects._generate_commercial_invoice_safe()
        late = projects.filtered(lambda p: not p.commercial_invoice_id and
                                 p.audit_completed_on < fields.Datetime.now() - timedelta(hours=24))
        return len(projects.filtered('commercial_invoice_id')), len(late)
