from odoo import fields, models


class SaleDocumentPreview(models.TransientModel):
    """The popup of the Preview Document buttons: the tab's document as a PDF, shown in a
    dialog over the sale order (closed with its X / Close button, the order stays open)."""

    _name = 'tuv.sale.document.preview'
    _description = 'Sale Order Document Preview'

    order_id = fields.Many2one('sale.order', string='Order', readonly=True)
    name = fields.Char(string='Document', readonly=True)
    pdf = fields.Binary(string='Preview', readonly=True, attachment=False)
    pdf_name = fields.Char(readonly=True)
