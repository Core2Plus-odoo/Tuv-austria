import base64
import binascii

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..tools import mdc_annex


class MdSchemeImport(models.TransientModel):
    """Upload an MDC annex and let it fill the scheme in.

    The annexes are long (FSSC 22000 alone runs to thirteen pages) and typing them
    in by hand is where mistakes come from, so the file itself is the source: it is
    read the same way for every standard and every tab of the scheme is filled from
    what it actually says.
    """

    _name = 'md.scheme.import'
    _description = 'Import Annex'

    scheme_id = fields.Many2one(
        'md.scheme', string='Update Scheme',
        help='Leave empty to create a new scheme from the file.')
    annex_file = fields.Binary(string='Annex File (.docx)', required=True, attachment=False)
    annex_filename = fields.Char(string='Filename')
    keep_manual_edits = fields.Boolean(
        string='Keep What Is Already There', default=False,
        help='Off: the duration table, risk categories, factors and sections are '
             'replaced by what the file says. On: the file only adds to them.')
    result = fields.Text(string='Result', readonly=True)

    def _parse(self):
        self.ensure_one()
        if not self.annex_file:
            raise UserError(_('Pick the annex file first.'))
        try:
            raw = base64.b64decode(self.annex_file)
        except (binascii.Error, ValueError) as err:
            raise UserError(_('That file could not be read: %s', err))
        if not raw[:2] == b'PK':
            raise UserError(_('This is not a .docx file. Save the annex as Word (.docx) '
                              'and upload it again.'))
        try:
            return mdc_annex.parse_annex(raw, self.annex_filename or '')
        except Exception as err:  # a malformed annex should not show a traceback
            raise UserError(_('The annex could not be read: %s', err))

    def action_import(self):
        self.ensure_one()
        data = self._parse()
        if not data.get('standard'):
            raise UserError(_('No "Standard or certification scheme" row was found in this '
                              'file, so it does not look like an MDC annex.'))
        scheme = self.scheme_id
        values = {
            'name': data['standard'],
            'scheme_type': data.get('ms') or False,
            'document_reference': self.annex_filename or data.get('file') or False,
            'document_code': data.get('code') or False,
            'revision': data.get('revision') or False,
            'annex_file': self.annex_file,
            'annex_filename': self.annex_filename,
        }
        if scheme:
            # the name stays the user's: they may have renamed the scheme on purpose
            values.pop('name')
            scheme.write(values)
        else:
            existing = self.env['md.scheme'].search([('name', '=', data['standard'])], limit=1)
            if existing:
                raise UserError(_('%s is already set up. Open it and import the file from '
                                  'there to refresh it.', data['standard']))
            values.setdefault('short_name', data['standard'])
            scheme = self.env['md.scheme'].create(values)

        if not self.keep_manual_edits:
            # Only what the file actually carries is replaced. ISO 20000 prints its
            # audit time chart as a picture, so its bands were typed in by hand and
            # a re-import must not wipe them.
            if data['sections']:
                scheme.section_ids.unlink()
            if data['duration']:
                scheme.duration_line_ids.unlink()
            if data['risk']:
                scheme.risk_category_ids.unlink()
            if data['factors']:
                scheme.factor_ids.unlink()

        Section = self.env['md.scheme.section']
        for section in data['sections']:
            Section.create({
                'scheme_id': scheme.id,
                'sequence': section['sequence'],
                'name': (section['name'] or _('Section'))[:250],
                'body': section['body'],
            })
        Duration = self.env['md.duration.line']
        for line in data['duration']:
            Duration.create({
                'scheme_id': scheme.id,
                'personnel_label': line['label'],
                'personnel_from': line['from'],
                'personnel_to': line['to'],
                'complexity': line['complexity'],
                'audit_kind': line['kind'],
                'audit_days': line['days'],
            })
        Risk = self.env['md.risk.category']
        for i, line in enumerate(data['risk'], 1):
            Risk.create({
                'scheme_id': scheme.id,
                'sequence': i * 10,
                'category': (line['category'] or '-')[:60],
                'ea_code': line['ea'][:120],
                'nace_codes': line['nace'][:200],
                'business_sector': line['sector'],
            })
        Factor = self.env['md.adjustment.factor']
        for i, line in enumerate(data['factors'], 1):
            Factor.create({
                'scheme_id': scheme.id,
                'sequence': i * 10,
                'factor_type': line['type'],
                'name': line['name'],
            })

        kept = []
        if not data['duration']:
            kept.append(_('the audit duration table (the file has none - a picture, or a formula)'))
        if not data['risk']:
            kept.append(_('the risk / complexity categories'))
        if not data['factors']:
            kept.append(_('the adjustment factors'))
        summary = _(
            'Imported from %(file)s:\n'
            '- %(sections)d sections\n'
            '- %(duration)d audit duration values\n'
            '- %(risk)d risk / complexity lines\n'
            '- %(factors)d adjustment factors',
            file=self.annex_filename or data.get('file') or _('the file'),
            sections=len(data['sections']), duration=len(data['duration']),
            risk=len(data['risk']), factors=len(data['factors']))
        if kept:
            summary += _('\nLeft untouched: %s', ', '.join(kept))
        scheme.message_post(body=summary.replace('\n', '<br/>')) if hasattr(scheme, 'message_post') else None
        return {
            'type': 'ir.actions.act_window',
            'name': scheme.display_name,
            'res_model': 'md.scheme',
            'res_id': scheme.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_preview(self):
        """Show what the file holds without writing anything yet."""
        self.ensure_one()
        data = self._parse()
        self.result = _(
            'Standard      : %(standard)s\n'
            'Management sys: %(ms)s\n'
            'Form code     : %(code)s   %(revision)s\n\n'
            'Sections      : %(sections)d\n'
            'Duration values: %(duration)d\n'
            'Risk lines    : %(risk)d\n'
            'Factors       : %(factors)d\n\n'
            'Sections found:\n%(names)s',
            standard=data.get('standard') or '-', ms=data.get('ms') or '-',
            code=data.get('code') or '-', revision=data.get('revision') or '',
            sections=len(data['sections']), duration=len(data['duration']),
            risk=len(data['risk']), factors=len(data['factors']),
            names='\n'.join(' - %s' % s['name'] for s in data['sections']))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'md.scheme.import',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
