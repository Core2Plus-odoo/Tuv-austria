from odoo import api, models

# The Invoicing page on the project form comes from sale_timesheet. That module is
# not a dependency - not every TUV database has it - so the view that hides the page
# cannot be declared in XML: on a database without sale_timesheet the parent id does
# not resolve and the whole module refuses to install. It is created here instead,
# and only when the parent really exists.
PARENT_XMLID = 'sale_timesheet.project_project_view_form'
VIEW_NAME = 'project_project_view_form_invoicing_tuv_austria_customization'
VIEW_ARCH = """<data>
    <xpath expr="//page[@name='billing_employee_rate']" position="attributes">
        <attribute name="invisible">1</attribute>
    </xpath>
</data>"""


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def _tuv_hide_project_invoicing_page(self):
        """Hide sale_timesheet's Invoicing page, when that module is installed."""
        parent = self.env.ref(PARENT_XMLID, raise_if_not_found=False)
        existing = self.env.ref('tuv_austria_customization.' + VIEW_NAME,
                                raise_if_not_found=False)
        if not parent:
            # sale_timesheet was never installed, or has been removed since
            if existing:
                existing.sudo().unlink()
            return
        values = {
            'name': 'project.project.form.invoicing.custom.operations',
            'model': 'project.project',
            'inherit_id': parent.id,
            'mode': 'extension',
            'arch_db': VIEW_ARCH,
        }
        if existing:
            existing.sudo().write(values)
            view = existing
        else:
            view = self.sudo().create(values)
        # noupdate: at the end of an update Odoo deletes every xml id of the module
        # that was not loaded from a data file, and this one never is - it is made
        # here. noupdate keeps it out of that sweep; the arch above is rewritten on
        # each upgrade anyway, so nothing goes stale.
        data = self.env['ir.model.data'].sudo().search([
            ('module', '=', 'tuv_austria_customization'),
            ('name', '=', VIEW_NAME),
        ], limit=1)
        if data:
            data.write({'res_id': view.id, 'noupdate': True})
        else:
            self.env['ir.model.data'].sudo().create({
                'module': 'tuv_austria_customization',
                'name': VIEW_NAME,
                'model': 'ir.ui.view',
                'res_id': view.id,
                'noupdate': True,
            })
