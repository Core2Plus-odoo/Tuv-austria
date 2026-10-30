from odoo import fields, models

PARTICIPATION_ROWS = 26  # rows of the Word form; the PDF fills up to this with blank rows


class AuditParticipant(models.Model):
    """A row of the participation list, form FM-TAGMBH-MSZ-005."""

    _name = 'tuv.audit.participant'
    _description = 'Audit Participant'
    _order = 'sequence, id'

    plan_id = fields.Many2one('tuv.audit.plan', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Name', required=True)
    company = fields.Char(string='Company')
    function = fields.Char(string='Function / Department')
    closing_meeting = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                       string='Participation at the Closing Meeting')
    signature = fields.Binary(string='Signature', copy=False)


class AuditPlan(models.Model):
    _name = 'tuv.audit.plan'
    _inherit = 'tuv.audit.plan'

    pl_participant_ids = fields.One2many('tuv.audit.participant', 'plan_id', string='Participants',
                                         copy=True)

    def _pl_rows(self):
        return _participant_rows(self.pl_participant_ids)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    pl_participant_ids = fields.One2many('tuv.audit.participant', 'project_id',
                                         string='Participants', copy=True)

    def _pl_rows(self):
        return _participant_rows(self.pl_participant_ids)


def _participant_rows(participants):
    """The participants, then blank rows up to the 26 of the Word form."""
    rows = list(participants)
    return rows + [False] * max(0, PARTICIPATION_ROWS - len(rows))
