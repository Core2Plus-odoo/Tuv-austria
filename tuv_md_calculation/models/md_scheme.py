from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


# The order the annexes print their complexity columns in
COMPLEXITY_ORDER = ('High', 'Medium', 'Low', 'Limited')


def _sorted_complexities(values):
    known = [c for c in COMPLEXITY_ORDER if c in values]
    return known + [c for c in values if c and c not in known]


class MdScheme(models.Model):
    """One certification scheme and the man-day rules that come with it.

    Each scheme mirrors one annex of `VB-BA-ZET-MS-All-003` (the MDC annexes):
    the audit duration table plus the factors that may shorten or lengthen the
    audit time.
    """

    _name = 'md.scheme'
    _description = "Certification Scheme (MD's Calculation)"
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(string='Standard / Scheme', required=True,
                       help='As printed on the annex, e.g. ISO/IEC 20000-1:2018.')
    short_name = fields.Char(string='Short Name', help='e.g. ISO 20000')
    scheme_type = fields.Char(string='Management System',
                              help='What the standard manages, e.g. IT Service MS.')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # where the rules come from
    document_reference = fields.Char(
        string='Annex Document',
        help='File name of the annex, e.g. VB-BA-ZET-MS-All-003-Ann-MDC-20000-EN.docx')
    document_code = fields.Char(string='Form Code', help='e.g. KFM-002b, Rev.01')
    revision = fields.Char(string='Revision')
    annex_file = fields.Binary(string='Annex File', attachment=True)
    annex_filename = fields.Char(string='Annex Filename')

    # The annexes print their duration table as a picture, so the original image is
    # kept next to the typed-in bands for anyone who wants to check them.
    time_chart_image = fields.Image(string='Auditor Time Chart (original)', max_width=1200, max_height=1200)

    duration_basis = fields.Char(
        string='Duration Table Header', default='Audit time: Stage 1 + Stage 2 (days)',
        help='What the days column of the audit duration table counts.')
    duration_intro = fields.Text(
        string='Audit Duration Table Note',
        help='The sentence the annex prints above the table.')
    multi_site_note = fields.Text(string='Organization With Multiple Sites')

    section_ids = fields.One2many(
        'md.scheme.section', 'scheme_id', string='Annex Sections', copy=True,
        help='The annex read top to bottom, one record per grey row of the document.')
    risk_category_ids = fields.One2many(
        'md.risk.category', 'scheme_id', string='Risk / Complexity Categories', copy=True)
    duration_line_ids = fields.One2many(
        'md.duration.line', 'scheme_id', string='Audit Duration Table', copy=True)
    factor_ids = fields.One2many(
        'md.adjustment.factor', 'scheme_id', string='Factors For Adjustment Of Audit Time', copy=True)

    # The annex rendered the way the Word file reads: grey label on the left, content
    # on the right, with the duration and risk tables drawn where the document has them.
    annex_preview = fields.Html(string='Annex', compute='_compute_annex_preview', sanitize=False)

    duration_line_count = fields.Integer(compute='_compute_counts')
    factor_count = fields.Integer(compute='_compute_counts')
    risk_category_count = fields.Integer(compute='_compute_counts')
    section_count = fields.Integer(compute='_compute_counts')
    complexity_levels = fields.Char(compute='_compute_complexity_levels',
                                    string='Complexity Levels')

    # Odoo 19 declares constraints on the model, not in _sql_constraints
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'This standard is already set up: open the existing scheme instead of adding a second one.',
    )

    @api.depends('duration_line_ids', 'factor_ids', 'risk_category_ids', 'section_ids')
    def _compute_counts(self):
        for scheme in self:
            scheme.duration_line_count = len(scheme.duration_line_ids)
            scheme.factor_count = len(scheme.factor_ids)
            scheme.risk_category_count = len(scheme.risk_category_ids)
            scheme.section_count = len(scheme.section_ids)

    @api.depends('duration_line_ids.complexity')
    def _compute_complexity_levels(self):
        for scheme in self:
            levels = _sorted_complexities(dict.fromkeys(scheme.duration_line_ids.mapped('complexity')))
            scheme.complexity_levels = ', '.join(levels)

    @api.depends('section_ids.body', 'section_ids.name', 'duration_line_ids', 'risk_category_ids',
                 'name', 'scheme_type', 'document_reference')
    def _compute_annex_preview(self):
        for scheme in self:
            scheme.annex_preview = scheme._render_annex()

    def _render_annex(self):
        """Build the read-only view of the annex."""
        self.ensure_one()
        esc = lambda t: (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        grey = ('background-color:#D9D9D9;color:#000000;font-weight:bold;width:22%;'
                'vertical-align:top;padding:6px;')
        cell = 'padding:6px;vertical-align:top;color:#000000;background-color:#FFFFFF;'
        html = ['<div style="background-color:#FFFFFF;color:#000000;padding:8px;">',
                '<table style="width:100%;border-collapse:collapse;border:1px solid #000;'
                'background-color:#FFFFFF;color:#000000;">']
        html.append('<tr><td colspan="2" style="%stext-align:center;">%s</td></tr>'
                    % (grey, esc('Calculation of Audit Person Days for %s' % (self.scheme_type or ''))))
        html.append('<tr><td style="%sborder:1px solid #000;">Standard or certification scheme</td>'
                    '<td style="%sborder:1px solid #000;">%s</td></tr>'
                    % (grey, cell + 'background-color:#F2F2F2;', esc(self.name)))
        for section in self.section_ids:
            body = esc(section.body or '')
            if '[Audit duration table' in body:
                body = body.split('[Audit duration table')[0] + self._render_duration_html()
            elif '[Risk / complexity table' in body:
                body = body.split('[Risk / complexity table')[0] + self._render_risk_html()
            else:
                body = self._render_body(body)
            html.append('<tr><td style="%sborder:1px solid #000;">%s</td>'
                        '<td style="%sborder:1px solid #000;">%s</td></tr>'
                        % (grey, esc(section.name), cell, body))
        if self.duration_line_ids and not any('[Audit duration table' in (s.body or '')
                                              for s in self.section_ids):
            html.append('<tr><td style="%sborder:1px solid #000;">Audit Duration Table</td>'
                        '<td style="%sborder:1px solid #000;">%s</td></tr>'
                        % (grey, cell, self._render_duration_html()))
        factors = self.factor_ids
        if factors:
            rows = []
            for kind, label in (('increase', 'Potential increase factors'),
                                ('decrease', 'Potential decrease factors')):
                items = factors.filtered(lambda f: f.factor_type == kind)
                if items:
                    rows.append('<b>%s</b><ul>%s</ul>' % (label, ''.join(
                        '<li>%s</li>' % esc(f.name) for f in items)))
            html.append('<tr><td style="%sborder:1px solid #000;">Factors for adjustment of audit time</td>'
                        '<td style="%sborder:1px solid #000;">%s</td></tr>'
                        % (grey, cell, ''.join(rows)))
        html.append('</table></div>')
        return ''.join(html)

    def _render_body(self, body):
        """Turn the stored text back into something that reads like the annex.

        Tables inside a grey row are kept as "cell | cell | cell" lines, so any run of
        such lines is drawn as a real table again; everything else is plain text.
        """
        td = 'border:1px solid #000;padding:4px;color:#000000;background-color:#FFFFFF;'
        out, table = [], []

        def flush():
            if not table:
                return
            widest = max(len(r) for r in table)
            rows = []
            for i, cells in enumerate(table):
                cells = cells + [''] * (widest - len(cells))
                style = td + ('background-color:#F2F2F2;font-weight:bold;' if i == 0 else '')
                rows.append('<tr>%s</tr>' % ''.join(
                    '<td style="%s">%s</td>' % (style, c) for c in cells))
            out.append('<table style="border-collapse:collapse;margin:4px 0;width:100%%;">%s</table>'
                       % ''.join(rows))
            table.clear()

        for line in (body or '').split('\n'):
            if ' | ' in line:
                table.append([c.strip() for c in line.split('|')])
            else:
                flush()
                if line.strip():
                    out.append(line + '<br/>')
        flush()
        return ''.join(out)

    def _render_duration_html(self):
        self.ensure_one()
        lines = self.duration_line_ids
        complexities = _sorted_complexities(dict.fromkeys(lines.mapped('complexity')))
        kinds = [k for k in dict.fromkeys(lines.mapped('audit_kind')) if k]
        kind_label = dict(self.env['md.duration.line']._fields['audit_kind'].selection)
        th = ('border:1px solid #000;padding:4px;background-color:#F2F2F2;color:#000000;'
              'font-weight:bold;text-align:center;')
        td = 'border:1px solid #000;padding:4px;text-align:center;color:#000000;background-color:#FFFFFF;'
        head = ['<th style="%s">Effective number of personnel</th>' % th]
        cols = []
        for kind in kinds:
            for cx in (complexities or ['']):
                label = cx or (self.duration_basis or 'Audit days')
                if len(kinds) > 1:
                    label = '%s<br/>%s' % (kind_label.get(kind, kind), cx)
                head.append('<th style="%s">%s</th>' % (th, label))
                cols.append((kind, cx))
        rows = []
        seen = []
        for line in lines.sorted(lambda l: (l.personnel_from, l.id)):
            if line.personnel_label in seen:
                continue
            seen.append(line.personnel_label)
            cells = ['<td style="%s">%s</td>' % (td, line.personnel_label or line.band)]
            for kind, cx in cols:
                match = lines.filtered(lambda l: l.personnel_label == line.personnel_label
                                       and l.audit_kind == kind and (l.complexity or '') == cx)
                value = ('%g' % match[0].audit_days) if match else ''
                cells.append('<td style="%s">%s</td>' % (td, value))
            rows.append('<tr>%s</tr>' % ''.join(cells))
        return ('<table style="border-collapse:collapse;margin-top:4px;"><tr>%s</tr>%s</table>'
                % (''.join(head), ''.join(rows)))

    def _render_risk_html(self):
        self.ensure_one()
        esc = lambda t: (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        th = ('border:1px solid #000;padding:4px;background-color:#F2F2F2;color:#000000;'
              'font-weight:bold;')
        td = 'border:1px solid #000;padding:4px;color:#000000;background-color:#FFFFFF;'
        rows = ['<tr><th style="%s">Risk category</th><th style="%s">EA sector</th>'
                '<th style="%s">NACE codes</th><th style="%s">Business sector</th></tr>'
                % (th, th, th, th)]
        for line in self.risk_category_ids:
            rows.append('<tr><td style="%s">%s</td><td style="%s">%s</td><td style="%s">%s</td>'
                        '<td style="%s">%s</td></tr>'
                        % (td, esc(line.category), td, esc(line.ea_code), td,
                           esc(line.nace_codes), td, esc(line.business_sector)))
        return '<table style="border-collapse:collapse;margin-top:4px;">%s</table>' % ''.join(rows)

    # ------------------------------------------------------------------
    # The lookup the rest of the system asks for
    # ------------------------------------------------------------------
    def get_audit_days(self, personnel, complexity=None, audit_kind='certification'):
        """Audit days the scheme prescribes for that many effective personnel.

        Some annexes split the table by complexity (ISO 14001, 45001, 50001) and
        by the kind of audit (ISO 50001), hence the two extra arguments. Returns 0
        when no band covers the number: the annexes stop at their last band and
        anything above it is agreed by hand, which the table says in so many words.
        """
        self.ensure_one()
        lines = self.duration_line_ids.filtered(
            lambda l: l.personnel_from <= personnel
            and (not l.personnel_to or personnel <= l.personnel_to)
            and (not audit_kind or l.audit_kind == audit_kind))
        if complexity:
            lines = lines.filtered(lambda l: (l.complexity or '').lower() == complexity.lower())
        return lines[:1].audit_days

    def action_import_annex(self):
        """Open the wizard with this scheme preselected."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Annex - %s', self.display_name),
            'res_model': 'md.scheme.import',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scheme_id': self.id},
        }

    def action_open_duration_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Duration Table - %s', self.name),
            'res_model': 'md.duration.line',
            'view_mode': 'list',
            'domain': [('scheme_id', '=', self.id)],
            'context': {'default_scheme_id': self.id},
        }


class MdDurationLine(models.Model):
    """One band of the Auditor Time Chart."""

    _name = 'md.duration.line'
    _description = 'Audit Duration Table Line'
    _order = 'scheme_id, audit_kind, personnel_from, complexity, id'

    scheme_id = fields.Many2one('md.scheme', string='Scheme', required=True, ondelete='cascade')
    personnel_label = fields.Char(
        string='Personnel (as printed)',
        help='The band exactly as the annex prints it, e.g. "1-5", "876~1,175", ">10700".')
    personnel_from = fields.Integer(string='Personnel From', required=True)
    personnel_to = fields.Integer(
        string='Personnel To',
        help='Leave empty for the last, open ended band.')
    complexity = fields.Char(
        string='Complexity',
        help='Only for the annexes whose table is split by complexity (High / Medium / Low / Limited).')
    audit_kind = fields.Selection([
        ('certification', 'Certification (Stage 1 + Stage 2)'),
        ('surveillance', 'Surveillance'),
        ('recertification', 'Recertification'),
    ], string='Audit', default='certification', required=True)
    audit_days = fields.Float(string='Audit Days', digits=(4, 2))
    days_note = fields.Char(
        string='Instead Of A Number',
        help='What the annex prints when it gives no number, e.g. "Follow progression above".')
    band = fields.Char(string='Effective Number Of Client Personnel', compute='_compute_band', store=True)

    @api.depends('personnel_from', 'personnel_to')
    def _compute_band(self):
        for line in self:
            if line.personnel_to:
                line.band = '%d-%d' % (line.personnel_from, line.personnel_to)
            else:
                line.band = '%d and above' % line.personnel_from

    @api.constrains('personnel_from', 'personnel_to')
    def _check_band(self):
        for line in self:
            if line.personnel_to and line.personnel_to < line.personnel_from:
                raise ValidationError(_('"Personnel To" cannot be smaller than "Personnel From".'))


class MdAdjustmentFactor(models.Model):
    """A reason the annex gives for shortening or lengthening the audit time."""

    _name = 'md.adjustment.factor'
    _description = 'Audit Time Adjustment Factor'
    _order = 'scheme_id, factor_type desc, sequence, id'

    scheme_id = fields.Many2one('md.scheme', string='Scheme', required=True, ondelete='cascade')
    factor_type = fields.Selection([
        ('decrease', 'Potential Decrease Factor'),
        ('increase', 'Potential Increase Factor'),
    ], string='Type', required=True, default='decrease')
    name = fields.Text(string='Factor', required=True)
    sequence = fields.Integer(default=10)


class MdSchemeSection(models.Model):
    """One grey row of the annex, kept in the order the document prints it.

    The annexes do not share a structure: one has a risk category table, another
    explains how to count equivalent personnel, a third adds transition audit time.
    Rather than invent a field per case, the whole annex is kept readable here, and
    only the parts that have to be calculated with (duration bands, risk categories,
    factors) get their own table.
    """

    _name = 'md.scheme.section'
    _description = 'Annex Section'
    _order = 'scheme_id, sequence, id'

    scheme_id = fields.Many2one('md.scheme', string='Scheme', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Section', required=True,
                       help='The label printed in the grey column of the annex.')
    body = fields.Text(string='Content')
    image = fields.Image(string='Figure', max_width=1400, max_height=1400)


class MdRiskCategory(models.Model):
    """A line of the risk / complexity classification table (IAF MD 5)."""

    _name = 'md.risk.category'
    _description = 'Risk / Complexity Category Line'
    _order = 'scheme_id, sequence, id'

    scheme_id = fields.Many2one('md.scheme', string='Scheme', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    category = fields.Char(string='Risk Category', required=True, help='High / Medium / Low / Limited')
    ea_code = fields.Char(string='EA Sector / Subsector')
    nace_codes = fields.Char(string='NACE Codes')
    business_sector = fields.Text(string='Business Sector')
