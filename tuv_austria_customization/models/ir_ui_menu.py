from odoo import api, models

# Root (app-switcher) menus renamed for the client.  A menu is located by any of
# its candidate XML ids; ``labels`` is a last resort used when a module ships the
# root menu under an id we do not know about.
APP_MENU_RENAMES = [
    {
        'name': 'Client List-Business Insurance',
        'xml_ids': ['contacts.menu_contacts'],
        'labels': ['Contacts'],
    },
    {
        'name': 'Planning-Business Insurance',
        'xml_ids': ['project.menu_main_pm'],
        'labels': ['Project'],
    },
    {
        'name': 'Database-Business Insurance',
        'xml_ids': ['documents.menu_root'],
        'labels': ['Documents'],
    },
    {
        # ``accountant`` (Enterprise) replaces the Invoicing root menu with its
        # own Accounting one, so both have to be renamed.
        'name': 'Invoicing Business Insurance',
        'xml_ids': ['account.menu_finance', 'accountant.menu_accounting'],
        'labels': ['Invoicing', 'Accounting'],
    },
    {
        'name': 'Organogram -Business Insurance',
        'xml_ids': ['hr.menu_hr_root'],
        'labels': ['Employees'],
    },
]


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _tuv_rename_app_menus(self):
        """Apply the client specific app menu labels.

        Called from data on every install/upgrade of this module so the labels
        are restored even if a core module reloads its own menu definition.
        Menus of modules that are not installed are simply skipped.
        """
        langs = [code for code, _name in self.env['res.lang'].get_installed()]
        for rename in APP_MENU_RENAMES:
            menus = self.browse()
            for xml_id in rename['xml_ids']:
                menus |= self.env.ref(xml_id, raise_if_not_found=False) or self.browse()
            if not menus:
                menus = self.search([
                    ('parent_id', '=', False),
                    ('name', 'in', rename['labels']),
                ])
            for lang in langs:
                # ``name`` is translatable: write every installed language so no
                # stale translation keeps showing the original label.
                menus.with_context(lang=lang).sudo().write({'name': rename['name']})
