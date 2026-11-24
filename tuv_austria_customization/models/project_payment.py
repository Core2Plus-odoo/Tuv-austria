from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

from .project_invoice import CREDIT_DAYS
from .search_utils import boolean_search_positive

# The client's own stage names: entering either means the certificate is being issued.
CERTIFICATE_STAGE_NAMES = ('Certificate Issuance', 'Feedback & Continuous Improvement')


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    requires_full_payment = fields.Boolean(
        string='Requires Full Payment',
        help='A project can only enter this stage once its commercial invoices are 100% paid. '
             'Certificate Issuance and Feedback & Continuous Improvement are always treated so.')

    def _is_certificate_stage(self):
        self.ensure_one()
        return self.requires_full_payment or self.name in CERTIFICATE_STAGE_NAMES


class ProjectProject(models.Model):
    _inherit = 'project.project'

    payment_status = fields.Selection([
        ('no_invoice', 'No Invoice'),
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ], string='Payment Status', compute='_compute_payment', store=True, tracking=True)
    payment_currency_id = fields.Many2one('res.currency', compute='_compute_payment', store=True)
    amount_invoiced = fields.Monetary(string='Invoiced', compute='_compute_payment', store=True,
                                      currency_field='payment_currency_id')
    amount_paid = fields.Monetary(string='Paid', compute='_compute_payment', store=True,
                                  currency_field='payment_currency_id')
    amount_due = fields.Monetary(string='Outstanding', compute='_compute_payment', store=True,
                                 currency_field='payment_currency_id')
    paid_percent = fields.Float(string='% Paid', compute='_compute_payment', store=True)
    payment_due_date = fields.Date(string='Credit Ends', compute='_compute_payment_due_date', store=True,
                                   help='%s days after the job execution (audit completion).' % CREDIT_DAYS)
    payment_days_overdue = fields.Integer(string='Days Overdue', compute='_compute_payment_overdue')
    payment_overdue = fields.Boolean(string='Credit Overdue', compute='_compute_payment_overdue',
                                     search='_search_payment_overdue')
    payment_overdue_notified = fields.Boolean(copy=False)
    payment_paid_notified = fields.Boolean(copy=False)
    certificate_blocked_reason = fields.Char(string='Certificate Issuance Blocked',
                                             compute='_compute_certificate_blocked_reason')

    @api.depends('commercial_invoice_ids.state', 'commercial_invoice_ids.move_type',
                 'commercial_invoice_ids.payment_state', 'commercial_invoice_ids.amount_total',
                 'commercial_invoice_ids.amount_residual')
    def _compute_payment(self):
        for project in self:
            invoices = project._payment_invoices()
            currency = invoices[:1].currency_id or project.company_id.currency_id
            total = sum(invoices.mapped('amount_total'))
            due = sum(invoices.mapped('amount_residual'))
            project.payment_currency_id = currency
            project.amount_invoiced = total
            project.amount_due = due
            project.amount_paid = total - due
            project.paid_percent = round((total - due) * 100.0 / total, 1) if total else 0.0
            if not invoices:
                project.payment_status = 'no_invoice'
            elif all(inv.payment_state == 'paid' for inv in invoices) and float_is_zero(
                    due, precision_rounding=currency.rounding):
                project.payment_status = 'paid'
            elif due < total:
                project.payment_status = 'partial'
            else:
                project.payment_status = 'not_paid'

    def _payment_invoices(self):
        """The posted customer invoices of the project that still count (not reversed)."""
        self.ensure_one()
        return self.commercial_invoice_ids.filtered(
            lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
            and m.payment_state != 'reversed')

    @api.depends('audit_completed_on')
    def _compute_payment_due_date(self):
        for project in self:
            done = project.audit_completed_on
            project.payment_due_date = done.date() + timedelta(days=CREDIT_DAYS) if done else False

    @api.depends('payment_status', 'payment_due_date')
    def _compute_payment_overdue(self):
        today = fields.Date.context_today(self)
        for project in self:
            late = (project.payment_status in ('not_paid', 'partial') and bool(project.payment_due_date)
                    and project.payment_due_date < today)
            project.payment_overdue = late
            project.payment_days_overdue = (today - project.payment_due_date).days if late else 0

    def _search_payment_overdue(self, operator, value):
        domain = [('payment_status', 'in', ('not_paid', 'partial')),
                  ('payment_due_date', '<', fields.Date.context_today(self))]
        return domain if boolean_search_positive(operator, value) else ['!', '&'] + domain

    # ------------------------------------------------------------------
    # The certificate gate
    # ------------------------------------------------------------------
    def _certificate_blockers(self):
        """Why no certificate may be issued for this project ([] = it may)."""
        self.ensure_one()
        status = self.payment_status
        if status == 'no_invoice':
            return [_('no commercial invoice has been issued yet')]
        if status != 'paid':
            invoices = ', '.join(self._payment_invoices().filtered(
                lambda m: m.payment_state != 'paid').mapped('name'))
            blocker = _('payment is %(pct)s%% received - %(due)s %(cur)s still outstanding on %(inv)s',
                        pct=self.paid_percent, due='{:,.2f}'.format(self.amount_due),
                        cur=self.payment_currency_id.name, inv=invoices)
            if self.payment_overdue:
                blocker += _(' (credit period ended on %(date)s, %(days)s day(s) overdue)',
                             date=self.payment_due_date, days=self.payment_days_overdue)
            return [blocker]
        return []

    @api.depends('payment_status', 'amount_due', 'payment_due_date')
    def _compute_certificate_blocked_reason(self):
        for project in self:
            blockers = project._certificate_blockers() if project.audit_state == 'done' else []
            project.certificate_blocked_reason = '; '.join(blockers) or False

    def _check_certificate_allowed(self):
        """Raise unless 100% payment is confirmed. Every certificate step calls this."""
        for project in self:
            blockers = project._certificate_blockers()
            if blockers:
                raise UserError(_('No certificate can be issued for %(project)s without full payment '
                                  'confirmation: %(why)s.', project=project.name, why='; '.join(blockers)))

    @api.constrains('stage_id')
    def _check_certificate_stage_payment(self):
        # A constraint, not a button condition: it holds for the header buttons, a kanban
        # drag, an import, server code and sudo alike - the control cannot be bypassed.
        for project in self:
            if project.stage_id and project.stage_id._is_certificate_stage():
                blockers = project._certificate_blockers()
                if blockers:
                    raise ValidationError(_(
                        '%(project)s cannot move to "%(stage)s": no certificate can be issued '
                        'without full payment confirmation - %(why)s.', project=project.name,
                        stage=project.stage_id.name, why='; '.join(blockers)))

    # ------------------------------------------------------------------
    # Hourly: tell the team when the credit runs out, and when the money is in
    # ------------------------------------------------------------------
    @api.model
    def _cron_payment_tracking(self):
        overdue = self.search([('payment_overdue', '=', True), ('payment_overdue_notified', '=', False)])
        for project in overdue:
            project.message_post(body=_(
                'Credit period exceeded: payment was due on %(date)s - %(due)s %(cur)s outstanding. '
                'Certificate issuance stays blocked.', date=project.payment_due_date,
                due='{:,.2f}'.format(project.amount_due), cur=project.payment_currency_id.name))
            project.activity_schedule(
                'mail.mail_activity_data_todo', user_id=(project.user_id or self.env.user).id,
                summary=_('Payment overdue - %s', project.name),
                note=_('Recover %(due)s %(cur)s from %(client)s.', due='{:,.2f}'.format(project.amount_due),
                       cur=project.payment_currency_id.name, client=project.partner_id.name))
        overdue.write({'payment_overdue_notified': True})
        paid = self.search([('payment_status', '=', 'paid'), ('payment_paid_notified', '=', False)])
        for project in paid:
            project.message_post(body=_('Full payment confirmed (%(amount)s %(cur)s): certificate issuance '
                                        'is no longer blocked by payment.',
                                        amount='{:,.2f}'.format(project.amount_invoiced),
                                        cur=project.payment_currency_id.name))
        paid.write({'payment_paid_notified': True})
        return len(overdue), len(paid)
