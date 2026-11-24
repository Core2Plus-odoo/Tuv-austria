"""MDC / ATJF Word forms (Mandays Calculation) filled from the project.

The three client templates (static/docx/) are filled cell by cell from the project's
Mandays Calculation tab and given back as .docx, not PDF. They are printed from the
project's Print (gear) menu:
- PNAC                  -> when the order's document type is "PNAC-Contract"
- 2 ESYD/Austrian forms -> when the order's document type is "ESYD/Austrian Contract"

Boxes of the forms that had no project field yet are the ``mdc_*`` fields below,
shown in the Mandays Calculation tab ("MDC / ATJF Word Forms" section).
"""
import base64
import io
import re
import zipfile
from collections import defaultdict

from lxml import etree
from PIL import Image

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import file_open

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{%s}' % W_NS
W14 = '{http://schemas.microsoft.com/office/word/2010/wordml}'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
BOX, BOX_TICKED = '☐', '☒'
SIGNATURE_REL_ID = 'rIdTuvSignature'
SIGNATURE_PATH = 'word/media/tuv_signature.png'

# report_name -> (template file, download name)
MDC_TEMPLATES = {
    'tuv_audit_reports.mdc_pnac': (
        'mdc_pnac.docx', 'MDC or ATJF Format for PNAC'),
    'tuv_audit_reports.mdc_esyd_fssc': (
        'mdc_esyd_fssc.docx', 'MDC or ATJF Format for AUSTRIAN & FSSC 22000 (ESYD)'),
    'tuv_audit_reports.mdc_esyd_ims': (
        'mdc_esyd_ims.docx', 'MDC or ATJF Format for ESYD-Integrated Management System & ISO 50001'),
}

# project md_audit_type -> the "Audit Type" pick of the ESYD IMS form
IMS_AUDIT_TYPE = {
    'certification': 'Initial Certification',
    '1st_surveillance': '1. Surveillance Audit',
    '2nd_surveillance': '2. Surveillance Audit',
    'recertification': 'Re-Certification-Audit',
    'pre_audit': 'Pre-Audit',
    'extension': 'Extension',
}
# project md_audit_kind -> the "Audit Method" pick of the ESYD IMS form
IMS_AUDIT_METHOD = {
    'combined': 'Combined Audit',
    'integrated': 'Integrated Audit',
    'joint_audit': 'Others',
}


# ----------------------------------------------------------------------------
# Word helpers
# ----------------------------------------------------------------------------
def _row_cells(tr):
    """Cells of a row, including cells wrapped in a content control."""
    cells = []
    for el in tr:
        if el.tag == W + 'tc':
            cells.append(el)
        elif el.tag == W + 'sdt':
            content = el.find(W + 'sdtContent')
            if content is not None:
                cells += [c for c in content if c.tag == W + 'tc']
    return cells


def _text(el):
    return ''.join(t.text or '' for t in el.iter(W + 't'))


def _norm(text):
    text = (text or '').replace('’', "'").replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip().rstrip(':').strip().lower()


PLACEHOLDER_TEXTS = ('click here to enter', 'click or type here', 'choose an item',
                     'enter date', 'enter standard')


def _has_placeholder(cell):
    return cell.find('.//' + W + 'showingPlcHdr') is not None or any(
        _norm(_text(cell)).startswith(p) for p in PLACEHOLDER_TEXTS)


def _set_cell(cell, value):
    """Put ``value`` in a cell, replacing its text (sample text or placeholder)."""
    if _has_placeholder(cell):
        # the value takes the normal text colour, not the grey of the placeholder
        for color in cell.findall('.//' + W + 'r/' + W + 'rPr/' + W + 'color'):
            color.getparent().remove(color)
    # content controls: show the value, not the grey placeholder
    for flag in cell.findall('.//' + W + 'showingPlcHdr'):
        flag.getparent().remove(flag)
    for style in cell.findall('.//' + W + 'rStyle'):
        if 'placeholder' in (style.get(W + 'val') or '').lower():
            style.getparent().remove(style)
    # sample pictures of the template (e.g. a signature) go with the sample text
    for picture in cell.findall('.//' + W + 'drawing') + cell.findall('.//' + W + 'pict'):
        picture.getparent().remove(picture)
    lines = str(value).split('\n')
    texts = list(cell.iter(W + 't'))
    if texts:
        first = texts[0]
        for t in texts[1:]:
            t.text = ''
    else:
        paragraph = next(cell.iter(W + 'p'), None)
        if paragraph is None:
            paragraph = etree.SubElement(cell, W + 'p')
        run = etree.SubElement(paragraph, W + 'r')
        ppr_rpr = paragraph.find(W + 'pPr/' + W + 'rPr')
        if ppr_rpr is not None:
            rpr = etree.fromstring(etree.tostring(ppr_rpr))
            rpr.tag = W + 'rPr'
            run.append(rpr)
        first = etree.SubElement(run, W + 't')
    first.text = lines[0]
    first.set(XML_SPACE, 'preserve')
    # more lines: line breaks in the same run
    anchor = first
    for line in lines[1:]:
        br = etree.Element(W + 'br')
        anchor.addnext(br)
        t = etree.Element(W + 't')
        t.text = line
        t.set(XML_SPACE, 'preserve')
        br.addnext(t)
        anchor = t


def _tick(cell, index=0):
    """Tick the ``index``-th checkbox of a cell (Word form field, checkbox content
    control or a plain ☐ character)."""
    defaults = cell.findall('.//' + W + 'checkBox/' + W + 'default')
    if defaults:
        if index < len(defaults):
            defaults[index].set(W + 'val', '1')
        return
    boxes = [t for t in cell.iter(W + 't') if (t.text or '').strip() == BOX]
    if index < len(boxes):
        boxes[index].text = BOX_TICKED
        sdt = boxes[index]
        while sdt is not None and sdt.tag != W + 'sdt':
            sdt = sdt.getparent()
        checked = sdt is not None and sdt.find('.//' + W14 + 'checked')
        if checked is not None and checked is not False:
            checked.set(W14 + 'val', '1')


def _set_first_paragraph(cell, value, replace):
    """Value in the (empty) first paragraph of a cell, keeping the lines below it;
    ``replace`` changes texts of those lines ({old: new})."""
    for t in cell.iter(W + 't'):
        for old, new in replace.items():
            if old in (t.text or ''):
                t.text = t.text.replace(old, new, 1)
                t.set(XML_SPACE, 'preserve')
    if not value:
        return
    paragraph = next(cell.iter(W + 'p'), None)
    if paragraph is None or _text(paragraph).strip():
        return
    holder = etree.Element(W + 'tc')
    holder.append(etree.fromstring(etree.tostring(paragraph)))
    _set_cell(holder, value)
    paragraph.getparent().replace(paragraph, holder[0])


def _picture_xml(rel_id, width_emu, height_emu):
    """Inline picture run (DrawingML) showing the image of relationship ``rel_id``."""
    return (
        '<w:r xmlns:w="%(w)s"><w:drawing>'
        '<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
        ' distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%(cx)d" cy="%(cy)d"/><wp:docPr id="%(pid)d" name="Signature %(pid)d"/>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:nvPicPr><pic:cNvPr id="%(pid)d" name="signature.png"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
        ' r:embed="%(rid)s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%(cx)d" cy="%(cy)d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
    ) % {'w': W_NS, 'cx': width_emu, 'cy': height_emu, 'rid': rel_id, 'pid': 9001}


def _write(cell, value):
    """None: leave the cell as it is. '': clear sample text (keep empty placeholders).
    ('check', n): tick the n-th checkbox. ('first_paragraph', text, {old: new}).
    ('picture', rel_id, cx, cy): an image instead of the cell's content."""
    if value is None or cell is None:
        return
    if isinstance(value, tuple):
        if value[0] == 'picture':
            _set_cell(cell, '')
            paragraph = next(cell.iter(W + 'p'))
            paragraph.append(etree.fromstring(_picture_xml(*value[1:])))
        elif value[0] == 'check':
            _tick(cell, value[1])
        elif value[0] == 'first_paragraph':
            _set_first_paragraph(cell, value[1], value[2])
        return
    if value == '' and _has_placeholder(cell):
        return
    _set_cell(cell, value)


def _fill_table(tbl, plan, skip_rows=()):
    """``plan``: list of (label, value). For each row, a cell whose text equals a label
    gets its value in the next cell(s). A label used several times in the table is
    filled in document order. A value can be a list: one item per following cell.
    Labels ending with '*' match the beginning of the cell text. Label '#N' fills row
    N of the table from its first cell (rows without a label)."""
    queues = defaultdict(list)
    prefix = []
    for label, value in plan:
        queues[label].append(value)
        if label.endswith('*') and label not in prefix:
            prefix.append(label)
    for row_index, tr in enumerate(tbl.findall(W + 'tr')):
        if tr in skip_rows:
            continue
        cells = _row_cells(tr)
        by_index = queues.get('#%d' % row_index)
        if by_index:
            for col, item in enumerate(by_index[0]):
                if col < len(cells):
                    _write(cells[col], item)
            continue
        i = 0
        while i < len(cells) - 1:
            text = _norm(_text(cells[i]))
            key = text if text in queues else next(
                (p for p in prefix if text.startswith(p[:-1])), None)
            if not text or key is None or not queues[key]:
                i += 1
                continue
            value = queues[key].pop(0)
            values = value if isinstance(value, list) else [value]
            for offset, item in enumerate(values, start=1):
                if i + offset < len(cells):
                    _write(cells[i + offset], item)
            i += len(values) + 1


def _fill_standards(tbl, values):
    """Header row "Standard 1 | Standard 2 | Standard 3 | Other": the values go in the
    row below, same column. The cell after "Other" in the header (the FSSC 22000 pick
    of the ESYD forms) gets ``values['fssc']`` when it is a placeholder.
    Returns the two rows, which the label filling must leave alone."""
    rows = tbl.findall(W + 'tr')
    for index, tr in enumerate(rows[:-1]):
        header_cells = _row_cells(tr)
        header = [_norm(_text(c)) for c in header_cells]
        if 'standard 1' not in header:
            continue
        below = _row_cells(rows[index + 1])
        for col, name in enumerate(header):
            key = {'standard 1': 's1', 'standard 2': 's2', 'standard 3': 's3',
                   'other': 'other', 'fssc': 'fssc'}.get(name)
            if key and col < len(below):
                _write(below[col], values.get(key, ''))
        if 'other' in header:
            col = header.index('other') + 1
            if col < len(header_cells) and _has_placeholder(header_cells[col]):
                _write(header_cells[col], values.get('fssc', ''))
        return [tr, rows[index + 1]]
    return []


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    report_type = fields.Selection(selection_add=[('docx', 'Word (DOCX)')],
                                   ondelete={'docx': 'set default'})

    def _render_mdc_docx(self, res_ids):
        """(file content, file name) of a MDC/ATJF Word form for one project."""
        self.ensure_one()
        if self.report_name not in MDC_TEMPLATES:
            raise UserError(self.env._('No Word template for the report "%s".', self.name))
        project = self.env[self.model].browse(res_ids[:1])
        project.check_access('read')
        return project._mdc_docx(self.report_name)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # ---- boxes of the Word forms with no project field before ----
    # company / audit information
    mdc_effective_employees = fields.Char(string='Effective Number of Employees')
    mdc_rgn = fields.Char(string='RGN')
    mdc_risk_category = fields.Selection(
        [('high', 'HIGH'), ('medium', 'MEDIUM'), ('low', 'LOW')], string='Risk Category')
    mdc_scope_change = fields.Selection(
        [('no_changes', 'No Changes'), ('adjustment', 'Adjustment required')],
        string='Certificate Scope Change')
    mdc_audit_method = fields.Selection([
        ('single', 'Single Audit'),
        ('combined', 'Combined Audit'),
        ('integrated', 'Integrated Audit'),
        ('multi_site', 'Mulit-Site-Audit / Matrixaudit'),
        ('others', 'Others'),
    ], string='Audit Method')
    mdc_announced = fields.Selection(
        [('announced', 'Announced'), ('unannounced', 'Unannounced')],
        string='Announced / Unannounced')
    mdc_comments = fields.Text(string='Comments (if any)')
    # audit team
    mdc_stage1_md = fields.Char(string='Stage 01 MD')
    mdc_stage2_md = fields.Char(string='Stage 02 MD')
    mdc_la_md = fields.Char(string='Lead Auditor MD')
    mdc_la_technical_area = fields.Char(string='Lead Auditor Technical Area')
    mdc_ca_md = fields.Char(string='Co-Auditor MD')
    mdc_ca_technical_area = fields.Char(string='Co-Auditor Technical Area')
    mdc_planned_audit_date = fields.Date(string='Planned Audit Date')
    mdc_no_stage1_justification = fields.Text(string='Justification for Not Conducting Stage 1')
    # multi-site facilities
    mdc_sampling_square_root = fields.Boolean(string='Sampling: Square-root')
    mdc_sampling_all_facilities = fields.Boolean(
        string='Sampling: Certification/Recertification - All facilities')
    mdc_appendix_1 = fields.Char(string='Appendix 1')
    mdc_appendix_2 = fields.Char(string='Appendix 2')
    mdc_appendix_3 = fields.Char(string='Appendix 3')
    # auditor's approval
    mdc_approval_place = fields.Char(string='Approval Place')
    mdc_approval_date = fields.Date(string='Approval Date')
    # Annex I: ISO 20121 (events)
    mdc_event_scope = fields.Char(string='Scope of certification (single event / series of events)')
    mdc_event_min_md = fields.Char(string='Minimum number of audit MDs (guideline)')
    mdc_events_per_year = fields.Char(string='Number of events per year')
    mdc_suppliers = fields.Char(string='Number of suppliers')
    mdc_org_locations = fields.Char(string="Number of organization's locations")
    mdc_event_locations = fields.Char(string='Number of event locations')
    # final M/D calculation
    mdc_ims_reduction = fields.Char(string='Applicable IMS reduction (%) as per IAF MD 11')

    # ---------------------------------------------------------------- values
    def _mdc_sel(self, field):
        return self._fields[field].convert_to_export(self[field], self) or ''

    @staticmethod
    def _mdc_date(value):
        return value.strftime('%d/%m/%Y') if value else ''

    def _mdc_signature_png(self):
        """(png bytes, width, height) of the Mandays signature (md4_signature), or None."""
        if not self.md4_signature:
            return None
        try:
            image = Image.open(io.BytesIO(base64.b64decode(self.md4_signature)))
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
        except (OSError, ValueError):
            return None  # not a picture (e.g. a PDF): leave the box empty
        return buffer.getvalue(), image.width, image.height

    @staticmethod
    def _mdc_check(flag, index=0):
        return ('check', index) if flag else None

    def _mdc_common(self):
        """Values shared by the three forms (Mandays Calculation tab of the project)."""
        address = ', '.join(p for p in (
            self.md_street, self.md_street2, self.md_city, self.md_zip,
            self.md_state_id.name, self.md_country_id.name) if p)
        duration = (self.md_audit_duration or '').strip()
        return {
            'name': self.md_company_name or self.partner_id.name or '',
            'address': address,
            'sites': self.md_other_sites or '',
            'representative': self.md_company_representative or '',
            'description': self.md_company_description or '',
            'employees': self.mdc_effective_employees or '',
            'st1': self._mdc_date(self.md_audit_date_st1),
            'st2': self._mdc_date(self.md_audit_date_st2),
            'surveillance': self._mdc_date(self.md_audit_date_surveillance),
            'recert': self._mdc_date(self.md_audit_date_recert),
            'duration': duration,
            'scope': self.md_certification_scope or '',
            'ea': ', '.join(self.ea_code_ids.mapped('name')),
            'nace': self.md_nace or '',
            'category': self.md_category or '',
            'other_code': self.md_other_code or '',
            'remote': self.md_remote_auditing or '',
            'audit_type': self._mdc_sel('md_audit_type'),
            'audit_kind': self._mdc_sel('md_audit_kind'),
            'language': self._mdc_sel('md_audit_language'),
            'standards': {
                's1': self._mdc_sel('md_standard_1'),
                's2': self._mdc_sel('md_standard_2'),
                's3': self._mdc_sel('md_standard_3'),
                'other': self.md_standard_other or '',
                'fssc': self._mdc_sel('md_fssc_22000'),
            },
            'la': self.auditor_id.name or '',
            'ca': self.md_co_auditor_id.name or '',
            'te': self.aea_technical_expert_id.name or '',
            'tr': self.md_trainee_id.name or '',
            'participants': self.md_other_participants or '',
        }

    def _mdc_annex1_plan(self):
        p = self
        return [
            ('applicable management system', p.md1_applicable_system or ''),
            ('complexity / risk ranking', p.md1_complexity_ranking or ''),
            ('justification of*', p.md1_justification or ''),
            ('total number of personnel', p.md1_total_personnel or ''),
            ('number of employees on shifts', p.md1_employees_on_shifts or ''),
            ('number of employees without shifts', p.md1_employees_without_shifts or ''),
            ('number of shifts', p.md1_number_of_shifts or ''),
            ('permanent contracted personnel', p.md1_permanent_contracted or ''),
            ('seasonal personnel', p.md1_seasonal or ''),
            ('part time personnel*', p.md1_part_time or ''),
            ('months of employment', p.md1_months_employment or ''),
            ('temporary unskilled personnel', p.md1_temporary_unskilled or ''),
            ('equivalent number of personnel', p.md1_equivalent_personnel or ''),
            ('final md calculation based*', p.md1_final_md or ''),
            ('scope of certification (single event*', [
                p.mdc_event_scope or '',
                'Therefore, the minimum number of audit MDs according to the guideline is: %s'
                % (p.mdc_event_min_md or '')]),
            ('number of events per year*', p.mdc_events_per_year or ''),
            ('number of suppliers', p.mdc_suppliers or ''),
            ("number of organization's locations", p.mdc_org_locations or ''),
            ('number of event locations', p.mdc_event_locations or ''),
            ('ds = (td + th + tfte)', 'Ds = %s' % (p.md1_ds_equation or '')),
            ('c = (fec*', 'C = %s' % (p.md1_c_equation or '')),
            ('name of the activity', p.md1_activity_name or ''),
            ('number of personnel for this activity', p.md1_activity_personnel or ''),
            ('reduction of the number of personnel', p.md1_personnel_reduction or ''),
            ('non-repetitive activity', self._mdc_check(p.md1_non_repetitive)),
            ('non repetitive activity', self._mdc_check(p.md1_non_repetitive)),
            ('repetitive activity', self._mdc_check(p.md1_repetitive)),
            ('risk level', p._mdc_sel('md1_risk_level')),
            ('remaining*', p.md1_remaining_personnel or ''),
            ('other standard (fill in)', p.md1_other_standard or ''),
            ('final man-days calculation', p.md1_final_mandays or ''),
            ('final mandays calculation', p.md1_final_mandays or ''),
            ('observations', p.md1_observations or ''),
        ]

    def _mdc_annex2_plan(self):
        p = self
        plan = [
            ('applicable management system', p.md2_applicable_system or ''),
            ('total number of personnel', p.md2_total_personnel or ''),
            ('number of employees on shifts', p.md2_employees_on_shifts or ''),
            ('number of employees without shifts', p.md2_employees_without_shifts or ''),
            ('number of shifts', p.md2_number_of_shifts or ''),
            ('permanent contracted personnel', p.md2_permanent_contracted or ''),
            ('seasonal personnel', p.md2_seasonal or ''),
            ('part time personnel*', p.md2_part_time or ''),
            ('months of employment', p.md2_months_employment or ''),
            ('temporary unskilled personnel', p.md2_temporary_unskilled or ''),
            ('equivalent number of personnel', p.md2_equivalent_personnel or ''),
        ]
        for n in range(1, 5):
            plan += [
                ('complexity / risk ranking', p['md2_sys%d_complexity' % n] or ''),
                ('man-days according to relevant table', p['md2_sys%d_mandays' % n] or ''),
            ]
        # "System N | factor | %": first the increase block, then the decrease block
        for kind in ('inc', 'dec'):
            for n in range(1, 5):
                plan.append(('system %d' % n, [p['md2_%s_sys%d' % (kind, n)] or '',
                                               p['md2_%s_sys%d_pct' % (kind, n)] or '']))
        return plan

    def _mdc_final_plan(self, integration, signoff):
        """``integration``: text of the "Level of integration" cell (System 1 row)."""
        p = self
        plan = []
        for n, letter in enumerate('ABCD', start=1):
            plan.append(('system %d' % n, [
                '%s= %s' % (letter, p['md4_sys%d_md' % n] or ''),
                integration if n == 1 else None,
                p['md4_sys%d_cert' % n] or '', p['md4_sys%d_surv1' % n] or '',
                p['md4_sys%d_surv2' % n] or '']))
        plan += [
            ('total', [p.md4_total_md or '', None, p.md4_total_cert or '',
                       p.md4_total_surv1 or '', p.md4_total_surv2 or '']),
            ('t = a + 0.5 b*', 'T = %s' % (p.md4_t_equation or '')),
            ('t = a + 0,5 b*', 'T = %s' % (p.md4_t_equation or '')),
            ('observations', p.md4_observations or ''),
        ]
        return plan + signoff

    def _mdc_esyd_integration(self):
        p = self
        return ('Level of integration %%: %s\nDue to: - %s - %s\n'
                'Ability to perform combined audit %% = %s' % (
                    p._mdc_sel('md4_level_of_integration'), p.md4_due_to_1 or '',
                    p.md4_due_to_2 or '', p.md4_combined_audit_pct or ''))

    # ---------------------------------------------------------------- forms
    def _mdc_plans_pnac(self, v):
        p = self
        lead = p.md4_lead_auditor or v['la']
        company = [
            ('company name', v['name']),
            ('address*', v['address']),
            ('other audited sites*', v['sites']),
            ('company representative', v['representative']),
            ('description of the company', ('first_paragraph', v['description'], {
                'Employees: ': 'Employees: %s ' % v['employees'] if v['employees'] else 'Employees: '})),
            ('st.1', v['st1']), ('st.2', v['st2']),
            ('surveillance', v['surveillance']), ('recertification', v['recert']),
            ('total audit duration*', ('MD %s' % v['duration']) if v['duration'] else None),
            ('certificationscope', v['scope']),
            ('iaf code', v['ea']),
            ('risk category', p._mdc_sel('mdc_risk_category')),
            ('category*', v['category']),
            ('audit type', v['audit_type']),
            ('audit kind', v['audit_kind']),
            ('audit language', v['language']),
            ('la', v['la']), ('ca', v['ca']), ('te', v['te']),
            ('md', 'MD %s' % (p.mdc_stage1_md or '')),
            ('la', v['la']), ('ca', v['ca']), ('te', v['te']),
            ('md', 'MD %s' % (p.mdc_stage2_md or '')),
            ('other participants*', v['participants']),
        ]
        integration = (
            'Integration Level %% = %s\nCombined audit capability %% = %s\n'
            'Applicable IMS reduction (%%) as per IAF MD 11 = %s' % (
                p._mdc_sel('md4_level_of_integration'), p.md4_combined_audit_pct or '',
                p.mdc_ims_reduction or ''))
        signoff = [
            # Mandays signature picture; without one the box stays as it is
            ('signature', v.get('signature')),
            ('proposed by', [lead, 'Date: %s' % self._mdc_date(p.md4_date)]),
            ('approved by*', [p.atjf_reviewed_by.name or '',
                              'Date: %s' % self._mdc_date(p.atjf_reviewed_on)]),
        ]
        return [company, self._mdc_annex1_plan(), self._mdc_annex2_plan(),
                self._mdc_final_plan(integration, signoff)]

    def _mdc_plans_esyd_fssc(self, v):
        p = self
        company = [
            ('company name', v['name']),
            ('full address*', v['address']),
            ('other audited sites*', v['sites']),
            ('company representative', v['representative']),
            ('description of the company*', ('first_paragraph', v['description'], {
                '= |': ('= %s |' % v['employees']) if v['employees'] else '= |',
                'RGN: ': ('RGN: %s' % p.mdc_rgn) if p.mdc_rgn else 'RGN: '})),
            ('st.1', v['st1']), ('st.2', v['st2']),
            ('surveillance', v['surveillance']), ('recertification', v['recert']),
            ('audit duration (mandays)', ('%s MD' % v['duration']) if v['duration'] else None),
            ('certification scope', v['scope']),
            ('ea code', v['ea']),
            ('nace', v['nace']),
            ('category', v['category']),
            ('other', v['other_code'] or None),
            ('use of remote auditing*', v['remote']),
            ('audit type', v['audit_type']),
            ('audit kind', v['audit_kind']),
            ('audit language', v['language']),
            ('la', v['la']), ('ca', v['ca']), ('tr', v['tr']),
            ('other participants*', v['participants']),
        ]
        signoff = [
            # Mandays signature picture; without one the box stays as it is
            ('signature', v.get('signature')),
            ('lead auditor', p.md4_lead_auditor or v['la']),
            ('date', self._mdc_date(p.md4_date)),
        ]
        return [company, self._mdc_annex1_plan(), self._mdc_annex2_plan(),
                self._mdc_final_plan(self._mdc_esyd_integration(), signoff)]

    def _mdc_plans_esyd_ims(self, v):
        p = self
        std = v['standards']
        audit_type = IMS_AUDIT_TYPE.get(p.md_audit_type) or ('Others' if p.md_audit_type else '')
        # "Audit Type" under each audited standard
        types = [audit_type if std[key] else None for key in ('s1', 's2', 's3', 'other')]
        types[0] = audit_type
        # audit team: roles in the "Lead Auditor" row, names in the row below
        team = [(name, role) for name, role in (
            (v['ca'], 'Auditor'), (v['te'], 'Technical expert'), (v['tr'], 'Trainee')) if name]
        method = p._mdc_sel('mdc_audit_method') or IMS_AUDIT_METHOD.get(p.md_audit_kind, '')
        company = [
            ('company name', v['name']),
            ('full address*', v['address']),
            ('other audited sites', v['sites']),
            ('company representative', v['representative']),
            ('description of company*', v['description']),
            ('stage 1', v['st1']), ('stage 2', v['st2']),
            ('surveillance', v['surveillance']), ('recertification', v['recert']),
            ('audit duration (md)', v['duration']),
            ('no. of employees relevant for the scope',
             v['employees'] or p.md1_total_personnel or ''),
            ('certificate scope', v['scope']),
            # " | ☐ No Changes ☐ Adjustment required | Other | code"
            ('#12', [None, self._mdc_check(p.mdc_scope_change,
                                           0 if p.mdc_scope_change == 'no_changes' else 1),
                     None, v['other_code']]),
            ('ea code', v['ea']),
            ('nace', v['nace']),
            ('category', v['category']),
            ('audit method', method),
            ('use of remote auditing activities', v['remote'] or None),
            ('audit language', v['language'] or None),
            ('audit type', types),
            ('comments (if any)', [p.mdc_comments or '', p._mdc_sel('mdc_announced')]),
            ('lead auditor', [role for _name, role in team]),
            ('#20', [v['la']] + [name for name, _role in team]),
        ]
        multi_site = [
            ('square-root', self._mdc_check(p.mdc_sampling_square_root)),
            ('certification/recertification - all*', self._mdc_check(p.mdc_sampling_all_facilities)),
            ('appendix 1', p.mdc_appendix_1 or ''),
            ('appendix 2', p.mdc_appendix_2 or ''),
            ('appendix 3', p.mdc_appendix_3 or ''),
        ]
        planned_team = [
            ('lead auditor', [v['la'], p.mdc_la_md or '', p.mdc_la_technical_area or '']),
            ('co-auditor', [v['ca'], p.mdc_ca_md or '', p.mdc_ca_technical_area or '']),
            ('planned audit date', self._mdc_date(p.mdc_planned_audit_date)),
            ('#7', [p.mdc_no_stage1_justification or '']),
        ]
        place_date = ', '.join(x for x in (
            p.mdc_approval_place, self._mdc_date(p.mdc_approval_date)) if x)
        approval = [('#1', [place_date])]
        signoff = [
            # Mandays signature picture; without one the box stays as it is
            ('signature', v.get('signature')),
            ('lead auditor', p.md4_lead_auditor or v['la']),
            ('date', self._mdc_date(p.md4_date)),
        ]
        # tables: 0 company/audit, 1 multi-site, 2 planned team, 3 approval,
        #         4 annex I, 5 annex II, 6 final M/D
        return [company, multi_site, planned_team, approval, self._mdc_annex1_plan(),
                self._mdc_annex2_plan(),
                self._mdc_final_plan(self._mdc_esyd_integration(), signoff)]

    def _mdc_docx(self, report_name):
        """Fill the Word template of ``report_name``: (content, file name)."""
        self.ensure_one()
        template, title = MDC_TEMPLATES[report_name]
        with file_open('tuv_audit_reports/static/docx/' + template, 'rb') as f:
            source = f.read()
        values = self._mdc_common()
        signature = self._mdc_signature_png()
        if signature:
            png, width, height = signature
            # about 1.5 cm high, as a hand signature on the form
            cy = 540000
            cx = int(cy * width / height) if height else cy * 3
            values['signature'] = ('picture', SIGNATURE_REL_ID, min(cx, 2700000), cy)
        plans = getattr(self, '_mdc_plans_' + report_name.split('.mdc_')[1])(values)

        zin = zipfile.ZipFile(io.BytesIO(source))
        root = etree.fromstring(zin.read('word/document.xml'))
        # top-level tables only (a nested table would shift the numbering)
        tables = [t for t in root.iter(W + 'tbl')
                  if not any(a.tag == W + 'tbl' for a in t.iterancestors())]
        skip_rows = _fill_standards(tables[0], values['standards'])
        for tbl, plan in zip(tables, plans):
            if plan:
                _fill_table(tbl, plan, skip_rows)

        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == 'word/document.xml':
                    data = etree.tostring(root, xml_declaration=True, encoding='UTF-8',
                                          standalone=True)
                elif signature and item.filename == 'word/_rels/document.xml.rels':
                    data = data.replace(b'</Relationships>', (
                        '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
                        'officeDocument/2006/relationships/image" Target="%s"/>'
                        '</Relationships>' % (SIGNATURE_REL_ID, SIGNATURE_PATH[5:])).encode())
                elif signature and item.filename == '[Content_Types].xml' \
                        and b'Extension="png"' not in data:
                    data = data.replace(b'<Default ', b'<Default Extension="png" '
                                        b'ContentType="image/png"/><Default ', 1)
                zout.writestr(item, data)
            if signature:
                zout.writestr(SIGNATURE_PATH, signature[0])
        name = '%s - %s.docx' % (title, self.name or '')
        return out.getvalue(), name.replace('/', '-')
