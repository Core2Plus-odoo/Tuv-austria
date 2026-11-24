from odoo import api, fields, models

from .application_annex_catalog import ANNEX_ROWS, ANNEX_TYPES

# The food-chain categories of "Annex - ISO 22000 / FSSC 22000" (KFM-002b, Rev.01).
# They are the printed form itself, not data, so they are laid down here and the
# rows are created empty: the client only ticks Selection and writes the short
# description, exactly as on paper.
ISO_22000_CATEGORIES = [
    ('A', 'Farming or Handling of Animals'),
    ('B', 'Farming or Handling of Plants'),
    ('C', 'Processing Food for Humans and Animals (pets)'),
    ('D', 'Feed and Animal Food Processing (domestic livestock)'),
    ('E', 'Catering / food service'),
    ('F', 'Provision of Trading, Retail and e-Commerce Services'),
    ('G', 'Provision of Transport and Storage Services'),
    ('H', 'Services'),
    ('I', 'Production of Food Packaging and packaging Material'),
    ('J', 'Equipment manufacturing'),
    ('K', 'Production of (Bio) Chemicals'),
]
# FSSC 22000 version 6 has no A and no B; it starts at BIII.
FSSC_22000_CATEGORIES = [
    ('BIII', 'Pre-process Handling of Plant Products'),
    ('C', 'Processing Food for Humans and Animals (pets)'),
    ('D', 'Feed and Animal Food Processing (domestic livestock)'),
    ('E', 'Catering/food service'),
    ('F', 'Provision of Trading, Retail and e-Commerce Services'),
    ('G', 'Provision of Transport and Storage Services'),
    ('H', 'Services'),
    ('I', 'Production of Food Packaging and packaging Material'),
    ('J', 'Equipment manufacturing'),
    ('K', 'Production of (Bio) Chemicals'),
]

ANNEX_CATEGORIES = {
    'iso22000_fssc22000': [('iso22000', ISO_22000_CATEGORIES), ('fssc22000', FSSC_22000_CATEGORIES)],
}


class ApplicationAnnex(models.Model):
    """An application annex the client attaches to an offer application.

    The application form asks for a separate annex for a number of standards
    (marked * on the form). Each annex is kept here as its own record, so a new
    one - ISO 13485, IFS, BRC ... - is a new annex_type with its own fields, and
    the sales user simply picks the one that belongs on his order.
    """

    _name = 'tuv.application.annex'
    _description = 'Application Annex'
    _order = 'name'

    name = fields.Char(required=True)
    annex_type = fields.Selection(
        ANNEX_TYPES, string='Annex', required=True, default='iso22000_fssc22000')
    active = fields.Boolean(default=True)
    note = fields.Char(string='Internal Note')

    # ------------------------------------------------------------------
    # ADDITIONAL INFORMATION
    # ------------------------------------------------------------------
    coid = fields.Char(string='COID')
    haccp_studies = fields.Char(string='Number of HACCP studies')
    production_lines = fields.Char(string='Number of production lines')
    blackout_date = fields.Char(string='Blackout Date')
    blackout_reason = fields.Char(string='Reason for Blackout')

    # ------------------------------------------------------------------
    # SCOPE DETAILS
    # ------------------------------------------------------------------
    products = fields.Char(string='Product(s)')
    packaging_method = fields.Char(string='Packaging Method (Plastic, Glass etc.)')
    main_processes = fields.Char(string='Main Processes')
    scope_exclusions = fields.Char(string='Exclusions of Scope')
    off_site_activities = fields.Char(string='Off Site Activities')
    seasonal_products = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Are There Any Seasonal Products?')
    seasonal_period = fields.Char(string='If Yes, What Period?')

    # ------------------------------------------------------------------
    # PRODUCT CATEGORY tables
    # ------------------------------------------------------------------
    category_line_ids = fields.One2many(
        'tuv.application.annex.line', 'annex_id', string='Annex Rows')
    # Two tables print side by side, so each gets a field of its own with the filter
    # on the field rather than on the view: two views over one field share the same
    # records in the client, and a row typed into one appears in the other.
    category_iso22000_ids = fields.One2many(
        'tuv.application.annex.line', 'annex_id', string='ISO 22000 Categories',
        domain=[('scheme', '=', 'iso22000')], context={'default_scheme': 'iso22000'})
    category_fssc22000_ids = fields.One2many(
        'tuv.application.annex.line', 'annex_id', string='FSSC 22000 Categories',
        domain=[('scheme', '=', 'fssc22000')], context={'default_scheme': 'fssc22000'})

    # "10. EN15343_OK Recycled_ESYD_Application Form.docx" prints two product tables
    # the client fills row by row, so they are their own lines rather than a catalogue.
    product_line_ids = fields.One2many(
        'tuv.application.annex.product', 'annex_id', string='Product Data')
    product_individual_ids = fields.One2many(
        'tuv.application.annex.product', 'annex_id', string='Individual Products',
        domain=[('table', '=', 'individual')], context={'default_table': 'individual'})
    product_group_ids = fields.One2many(
        'tuv.application.annex.product', 'annex_id', string='Group Products',
        domain=[('table', '=', 'group')], context={'default_table': 'group'})
    terms_confirmed = fields.Boolean(
        string="I confirm that I have read and agree to abide by all "
               "TUV AUSTRIA's Terms and Conditions")

    def _category_line_values(self, annex_type):
        """The rows the chosen annex prints, empty and in the printed order."""
        values = []
        for scheme, categories in ANNEX_CATEGORIES.get(annex_type, []):
            for code, label in categories:
                values.append({
                    'sequence': len(values) + 1,
                    'line_type': 'category',
                    'scheme': scheme,
                    'code': code,
                    'name': label,
                })
        for row in ANNEX_ROWS.get(annex_type, []):
            row = dict(row)
            row.setdefault('line_type', 'text')
            row['sequence'] = len(values) + 1
            values.append(row)
        return values

    def row(self, key):
        """The printed row with this key - the report addresses rows by name."""
        self.ensure_one()
        return self.category_line_ids.filtered(lambda l: l.key == key)[:1]

    def rows_of(self, section):
        """Every row of one printed band, in order."""
        self.ensure_one()
        return self.category_line_ids.filtered(lambda l: l.section == section).sorted('sequence')

    @api.onchange('annex_type')
    def _onchange_annex_type(self):
        for annex in self:
            annex.category_line_ids = [(5, 0, 0)] + [
                (0, 0, vals) for vals in annex._category_line_values(annex.annex_type)
            ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('category_line_ids'):
                vals['category_line_ids'] = [
                    (0, 0, line) for line in self._category_line_values(
                        vals.get('annex_type', 'iso22000_fssc22000'))
                ]
        return super().create(vals_list)

    def action_reset_category_lines(self):
        """Put the printed category rows back, keeping nothing of the old ones."""
        for annex in self:
            annex.category_line_ids.unlink()
            annex.category_line_ids = [
                (0, 0, vals) for vals in annex._category_line_values(annex.annex_type)
            ]
        return True

    def line_ids_of(self, scheme):
        """The rows of one table, in printed order - used by the report."""
        self.ensure_one()
        return self.category_line_ids.filtered(lambda l: l.scheme == scheme).sorted('sequence')


class ApplicationAnnexLine(models.Model):
    _name = 'tuv.application.annex.line'
    _description = 'Application Annex Product Category'
    _order = 'sequence, id'

    annex_id = fields.Many2one('tuv.application.annex', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    # The key is how the printed form addresses this row; the report asks for it by
    # name, so a row can be moved in the list without breaking the layout.
    key = fields.Char(index='btree_not_null')
    section = fields.Char(string='Section')
    line_type = fields.Selection([
        ('category', 'Product Category'),
        ('check', 'Checkbox'),
        ('text', 'Text'),
        ('check_text', 'Checkbox + Text'),
        ('grade', 'Grade'),
        ('note', 'Free Text'),
        ('band', 'Section Band'),
    ], default='category', required=True)
    scheme = fields.Selection([
        ('iso22000', 'ISO 22000'),
        ('fssc22000', 'FSSC 22000'),
    ])
    code = fields.Char(string='Category')
    name = fields.Char(string='Food Chain Category')
    selected = fields.Boolean(string='Selection')
    description = fields.Char(
        string='Give Short Description of Products Produced or Services')


class ApplicationAnnexProduct(models.Model):
    """A row of the EN 15343 / OK Recycled product tables."""

    _name = 'tuv.application.annex.product'
    _description = 'Application Annex Product Data'
    _order = 'sequence, id'

    annex_id = fields.Many2one('tuv.application.annex', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    table = fields.Selection([
        ('individual', 'A. Individual Products'),
        ('group', 'B. Group Products'),
    ], required=True, default='individual')
    # A/A on the individual table, Group on the group one
    reference = fields.Char(string='A/A - Group')
    product_type = fields.Char(string='Product Type (Intended Use, size, thickness etc)')
    raw_material = fields.Char(
        string='Raw material Used (Aluminium, Plastic -PET, PP, PS, PVC etc - Fabric etc)')
    supplier = fields.Char(string='Supplier of the Recycled material')
    waste_type = fields.Char(string='Pre or Post Consumer Waste')
    production_method = fields.Char(string='Production Method')
    recycled_percentage = fields.Char(string='Recycled Content Percentage (%)')
    quantity = fields.Char(string='Quantity Produced during the Reporting Period (t)')

    def lines_of(self, table):
        return self.filtered(lambda p: p.table == table).sorted('sequence')
