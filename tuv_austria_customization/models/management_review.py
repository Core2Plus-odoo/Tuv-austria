from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .client_feedback import FEEDBACK_QUESTIONS


class ManagementReview(models.TransientModel):
    """Continuous improvement figures of a period, for the BA Division management review
    and accreditation reporting - all read straight from what Odoo recorded."""

    _name = 'tuv.management.review'
    _description = 'Management Review Report'

    date_from = fields.Date(string='From', required=True,
                            default=lambda self: fields.Date.context_today(self).replace(month=1, day=1))
    date_to = fields.Date(string='To', required=True, default=fields.Date.context_today)

    def action_print(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('"From" has to be before "To".'))
        return self.env.ref('tuv_austria_customization.action_report_management_review').report_action(self)

    def _review_data(self):
        self.ensure_one()
        env = self.env
        d_from, d_to = self.date_from, self.date_to
        dt_from, dt_to = datetime.combine(d_from, time.min), datetime.combine(d_to, time.max)

        def pct(part, whole):
            return round(part * 100.0 / whole, 1) if whole else 0.0

        def avg(values):
            values = [v for v in values if v]
            return round(sum(values) / len(values), 2) if values else 0.0

        # certificates
        Reg = env['tuv.certificate.register']
        issued = Reg.search([('issue_date', '>=', d_from), ('issue_date', '<=', d_to)])
        current = Reg.search([('is_current', '=', True)])
        status_counts = {s: len(current.filtered(lambda e: e.status == s))
                         for s in ('valid', 'suspended', 'withdrawn', 'expired')}
        Notice = env['tuv.certificate.notice']
        notices = Notice.search([('notice_date', '>=', d_from), ('notice_date', '<=', d_to)])

        # client feedback
        fbs = env['tuv.client.feedback'].search([('answered_on', '>=', dt_from), ('answered_on', '<=', dt_to)])
        feedback = {
            'count': len(fbs),
            'questions': [(label, avg([int(f[field]) for f in fbs if f[field]])) for field, label in FEEDBACK_QUESTIONS],
            'average': avg(fbs.mapped('average_score')),
            'low': len(fbs.filtered('needs_attention')),
            'reviewed_pct': pct(len(fbs.filtered(lambda f: f.state == 'reviewed')), len(fbs)),
        }

        # corrective / improvement actions
        Action = env['tuv.improvement.action']
        actions = Action.search([('create_date', '>=', dt_from), ('create_date', '<=', dt_to)])
        actions_data = {
            'corrective': len(actions.filtered(lambda a: a.action_type == 'corrective')),
            'improvement': len(actions.filtered(lambda a: a.action_type == 'improvement')),
            'verified': len(actions.filtered(lambda a: a.state == 'verified')),
            'open': len(actions.filtered(lambda a: a.state in ('open', 'in_progress', 'done'))),
            'overdue_now': Action.search_count([('is_overdue', '=', True)]),
        }

        # nonconformities raised at audits
        NC = env['tuv.audit.nonconformity']
        ncs = NC.search([('raised_on', '>=', d_from), ('raised_on', '<=', d_to)])
        closed = ncs.filtered(lambda n: n.state == 'closed')
        nc_data = {
            'major': len(ncs.filtered(lambda n: n.grade == 'major_nc')),
            'minor': len(ncs.filtered(lambda n: n.grade == 'minor_nc')),
            'closed': len(closed),
            'closed_on_time_pct': pct(len(closed.filtered('closed_on_time')), len(closed)),
            'overdue_now': NC.search_count([('is_overdue', '=', True)]),
        }

        # audit process
        Project = env['project.project']
        audits = Project.search([('audit_completed_on', '>=', dt_from), ('audit_completed_on', '<=', dt_to)])
        reported = audits.filtered(lambda p: p.report_state == 'submitted')
        reviews = env['tuv.technical.review'].search([('reviewed_on', '>=', dt_from), ('reviewed_on', '<=', dt_to),
                                                      ('state', 'in', ('approved', 'returned'))])
        process = {
            'audits': len(audits),
            'reports_on_time_pct': pct(len(reported.filtered('report_on_time')), len(reported)),
            'reviews': len(reviews),
            'reviews_returned': len(reviews.filtered(lambda r: r.state == 'returned')),
            'first_pass_pct': pct(len(reviews.filtered(lambda r: r.state == 'approved')), len(reviews)),
        }

        # auditor performance
        perf = env['tuv.auditor.performance'].search([('closed_on', '>=', d_from), ('closed_on', '<=', d_to),
                                                      ('state', '=', 'confirmed')])
        auditors = []
        for auditor in perf.auditor_id:
            recs = perf.filtered(lambda r: r.auditor_id == auditor)
            auditors.append((auditor.name, len(recs), avg(recs.mapped('job_score')),
                             avg(recs.mapped('client_rating_auditor'))))
        auditors.sort(key=lambda row: -row[2])

        return {
            'issued': len(issued),
            'issued_by_type': [(label, len(issued.filtered(lambda e, k=key: e.certificate_type == k)))
                               for key, label in Reg._fields['certificate_type'].selection],
            'status_counts': status_counts,
            'suspensions': len(notices.filtered(lambda n: n.notice_type == 'suspension')),
            'withdrawals': len(notices.filtered(lambda n: n.notice_type == 'withdrawal')),
            'lifted': len(notices.filtered(lambda n: n.state == 'lifted')),
            'feedback': feedback,
            'actions': actions_data,
            'nc': nc_data,
            'process': process,
            'auditors': auditors,
        }
