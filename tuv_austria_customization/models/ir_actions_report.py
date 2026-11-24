from odoo import api, models

# Standard print entries the client does not want in the sale order gear menu. The
# certification documents (Application Form, Review Form, Proposal, the contracts)
# are the only things sales should be printing from there.
UNBOUND_REPORTS = [
    'sale.action_report_saleorder',                        # PDF Quote
    'sale_pdf_quote_builder.action_report_saleorder_raw',  # Quotation / Order
    'sale_timesheet.timesheet_report_sale_order',          # Timesheets
]


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _tuv_unbind_gear_reports(self):
        """Take the listed reports out of the Print menu.

        Clearing binding_model_id leaves the report itself intact - it can still be
        rendered from code or from a button - it only stops appearing in the gear.
        A report whose module is not installed is simply skipped.
        """
        for xml_id in UNBOUND_REPORTS:
            report = self.env.ref(xml_id, raise_if_not_found=False)
            if report and report.binding_model_id:
                report.sudo().write({'binding_model_id': False})
