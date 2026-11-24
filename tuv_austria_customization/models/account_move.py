from odoo import api, fields, models

try:
    from num2words import num2words
except ImportError:
    num2words = None


class AccountMove(models.Model):
    _inherit = 'account.move'

    business_line = fields.Char(string='Business Line')
    amount_in_words = fields.Char(
        string='Amount In Words', compute='_compute_amount_in_words')

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_in_words(self):
        for move in self:
            words = ''
            if move.currency_id and num2words:
                # the commercial invoice spells the rounded total, e.g.
                # "One Thousand Two Hundred and Sixty-Five USD Only"
                spelled = num2words(int(round(move.amount_total)), lang='en')
                spelled = spelled.title().replace(',', '').replace(' And ', ' and ')
                words = '%s %s Only' % (spelled, move.currency_id.name)
            elif move.currency_id:
                words = move.currency_id.amount_to_text(move.amount_total)
            move.amount_in_words = words
