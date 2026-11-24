#!/usr/bin/env python3
"""Turn the body of a TUV Austria Word form into JSON the PDF templates can draw.

Development tool, not loaded by Odoo. It reads a .docx and writes the blocks of its body in
document order: tables (every cell with its text, column/row span, grey or red fill, bold, and
whether it is a tick box), paragraphs and page breaks. The checklists are built from it:

    python3 tools/docx_forms.py           (from the module folder)

writes data/checklists/<key>.json for every checklist listed in CHECKLISTS below. Tick boxes
become "elements": one per box row (clause + the three audit types CA/RA, 1. SA, 2. SA), a grey
box marking the audit type for which the clause is mandatory; the project stores the ticks.
"""
import json
import pathlib
import re
import zipfile

from lxml import etree

MODULE = pathlib.Path(__file__).resolve().parent.parent
CUSTOM = MODULE.parent.parent  # the folders of Word forms sit next to Tuv-austria
FORMS = CUSTOM / 'ODOO_AUSTRIAN_CERT'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
AUDIT_TYPE_LABELS = ('CA/RA', '1. SA', '2. SA')
GREY = {'D9D9D9', 'BFBFBF', 'D8D8D8', 'E7E6E6', 'F2F2F2', 'C0C0C0', 'A6A6A6'}
RED = {'C00000', 'FF0000'}

# key: Word file, header title / subtitle, footer form code, and the variants of sections 1 and 2
# (see form_sections_company_audit in report/common_templates.xml). Revision and VKL are read
# from the Word footer unless given.
_CAT = 'Category (ISO 22003/ISO 13485):'
_CAT3 = 'Category (ISO 22003/ISO 13485/ISO 50003):'
_CHECKLIST_SECTIONS = dict(show_email=False, scope_label=False, duration_label='acc. plan',
                           category_label=_CAT)
CHECKLISTS = {
    'iso9001': dict(
        _CHECKLIST_SECTIONS,
        file="Form 'FM-TAGMBH-MSZ-010_Audit-Checklist-ISO-9001-EN' [English].docx",
        title='Audit checklist ISO 9001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-010_Audit-Checklist-ISO-9001-EN'),
    'iso45001': dict(
        _CHECKLIST_SECTIONS,
        file="Form 'FM-TAGMBH-MSZ-012_Audit-Checklist-ISO-45001-EN' [English].docx",
        title='Audit checklist ISO 45001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-012_Audit-Checklist-ISO-45001-EN'),
    'iso14001': dict(
        _CHECKLIST_SECTIONS, duration_label='hours',
        file="Form 'FM-TAGMBH-MSZ-014_Audit-checklist-ISO-14001-EN' [English].docx",
        title='Audit checklist ISO 14001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-014_Audit-checklist-ISO-14001-EN'),
    'iso50001': dict(
        _CHECKLIST_SECTIONS,
        file="Form 'FM-TAGMBH-MSZ-016_Audit-Checklist-ISO-50001-EN' [English].docx",
        title='Audit checklist ISO 50001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-016_Audit-Checklist-ISO-50001-EN'),
    'iso13485': dict(
        _CHECKLIST_SECTIONS, category_label=_CAT3,
        file="Form 'FM-TAGMBH-MSZ-018_Audit-Checklist-13485-EN' [English] (1).docx",
        title='Audit-Checklist ISO 13485', subtitle='Certification of Managementsystems',
        code='FM-TAGMBH-MSZ-018_Audit-Checklist-13485-EN'),
    'iso20000': dict(
        _CHECKLIST_SECTIONS, scope_label='Company description, business activities',
        duration_label='value',
        file="Formular 'FM-TAGMBH-MSZ-020_Audit-Checklist-20000-1-EN'.docx",
        title='Audit checklist ISO/IEC 20000-1', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-020_Audit-Checklist-20000-1-EN'),
    'iso37301': dict(
        _CHECKLIST_SECTIONS, scope_label='Company description, business activities',
        duration_label='value',
        file="Formular 'FM-TAGMBH-MSZ-025_Audit-Checklist-ISO-37301-EN'.docx",
        title='Audit checklist ISO 37301', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-025_Audit-Checklist-ISO-37301-EN'),
    'combined': dict(
        show_email=True, scope_label='Scope of certification', duration_label='value',
        category_label=_CAT,
        file="Form 'FM-TAGMBH-MSZ-033-Audit-Checklist-combined-QM-EM-HSE-EN-EN' [English].docx",
        title='Audit Checklist Combined QM/EM/HSE/EN', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-033-Audit-Checklist-combined-QM-EM-HSE-EN-EN'),
    # PNAC keeps older revisions of the same TÜV Austria checklists (other numbers for 14001/45001)
    'pnac9001': dict(
        _CHECKLIST_SECTIONS, category_label=_CAT3, folder='ODOO_PNAC',
        file="Form 'FM-TAGMBH-MSZ-010_Audit-Checklist-ISO-9001-EN' [English].docx",
        title='Audit checklist ISO 9001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-010_Audit-Checklist-ISO-9001-EN'),
    'pnac14001': dict(
        _CHECKLIST_SECTIONS, category_label=_CAT3, folder='ODOO_PNAC',
        file="Form 'FM-TAGMBH-MSZ-012_Audit-checklist-ISO-14001-EN' [English].docx",
        title='Audit checklist ISO 14001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-012_Audit-checklist-ISO-14001-EN'),
    'pnac45001': dict(
        _CHECKLIST_SECTIONS, category_label=_CAT3, folder='ODOO_PNAC',
        file="Form 'FM-TAGMBH-MSZ-014_Audit-Checklist-ISO-45001-EN' [English].docx",
        title='Audit checklist ISO 45001', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-014_Audit-Checklist-ISO-45001-EN'),
    'pnaccombined': dict(
        show_email=True, scope_label='Scope of certification', duration_label='value',
        category_label=_CAT, folder='ODOO_PNAC',
        file="Form 'FM-TAGMBH-MSZ-033-Audit-Checklist-combined-QM-EM-HSE-EN-EN' [English].docx",
        title='Audit Checklist Combined QM/EM/HSE/EN', subtitle='Certification of Management Systems',
        code='FM-TAGMBH-MSZ-033-Audit-Checklist-combined-QM-EM-HSE-EN-EN'),
}

# Reference documents printed as they are (nothing to fill in): key -> folder, file, header
DOCUMENTS = {
    'pnac_guide_9001': dict(
        folder='ODOO_PNAC', file="Form 'FM-TAGMBH-MSZ-011_Audit-Guideline-ISO-9001-EN' [English].docx"),
    'pnac_guide_14001': dict(
        folder='ODOO_PNAC', file="Form 'FM-TAGMBH-MSZ-013_Audit-Guidline-ISO-14001-EN' [English].docx"),
    'pnac_guide_45001': dict(
        folder='ODOO_PNAC', file="Form 'FM-TAGMBH-MSZ-015_Audit-Guideline-ISO-45001-EN' [English].docx"),
}


def form_path(spec):
    return CUSTOM / spec.get('folder', 'ODOO_AUSTRIAN_CERT') / spec['file']


# ----------------------------------------------------------------------------------------
# Word body -> blocks
# ----------------------------------------------------------------------------------------
def _children(el, tag):
    """Direct children `tag` of `el`, looking through content controls (<w:sdt>). A cell
    wrapped in a check box control is marked, since the box is declared on the wrapper."""
    out = []
    for ch in el:
        if ch.tag == W + tag:
            out.append(ch)
        elif ch.tag == W + 'sdt':
            content = ch.find(W + 'sdtContent')
            if content is None:
                continue
            inner = _children(content, tag)
            pr = ch.find(W + 'sdtPr')
            if pr is not None and _is_box(pr):
                for node in inner:
                    node.set('tuvbox', '1')
                    if _box_checked(pr):
                        node.set('tuvchecked', '1')
            out.extend(inner)
    return out


def _is_box(el):
    if el.get('tuvbox'):
        return True
    for n in el.iter():
        if n.tag.endswith('}checkbox'):
            return True
        if n.tag == W + 'instrText' and 'FORMCHECKBOX' in (n.text or ''):
            return True
    return False


def _box_checked(el):
    if el.get('tuvchecked'):
        return True
    for n in el.iter():
        if n.tag.endswith('}checked'):
            return n.get('{http://schemas.microsoft.com/office/word/2010/wordml}val') in ('1', 'true')
    return False


SUPERSCRIPT = str.maketrans('0123456789()', '⁰¹²³⁴⁵⁶⁷⁸⁹⁽⁾')


def _run_text(p):
    out = []
    for n in p.iter():
        if n.tag == W + 't':
            run = n.getparent()
            va = run.find(W + 'rPr/' + W + 'vertAlign') if run is not None else None
            if va is not None and va.get(W + 'val') == 'superscript':
                out.append((n.text or '').translate(SUPERSCRIPT))
                continue
            out.append(n.text or '')
        elif n.tag == W + 'tab':
            out.append(' ')
        elif n.tag == W + 'br' and n.get(W + 'type') != 'page':
            out.append('\n')
        elif n.tag == W + 'sym' or (n.tag == W + 't' and False):
            pass
    text = ''.join(out)
    # tick box glyphs belong to the box, not to the text
    return text.replace('☐', '').replace('☒', '')


def _bold(p):
    runs = [r for r in p.iter(W + 'r') if ''.join(t.text or '' for t in r.iter(W + 't')).strip()]
    if not runs:
        return False
    for r in runs:
        b = r.find(W + 'rPr/' + W + 'b')
        if b is None or b.get(W + 'val') in ('0', 'false'):
            # paragraph style may still make it bold; keep it simple
            return False
    return True


def _paragraph(p, numbering):
    text = ' '.join(_run_text(p).split(' ')).strip()
    num = p.find(W + 'pPr/' + W + 'numPr')
    if num is not None and text:
        num_id = num.find(W + 'numId')
        key = num_id.get(W + 'val') if num_id is not None else '0'
        numbering[key] = numbering.get(key, 0) + 1
        bullet = numbering.get('_fmt', {}).get(key, 'bullet')
        text = ('%d. ' % numbering[key] if bullet == 'decimal' else '• ') + text
    return text


MARK_BOLD = False  # build_document: prefix "**" to the bold lines of a partly bold cell


def _cell_text(tc, numbering):
    lines = []
    for p in tc.iter(W + 'p'):
        # skip paragraphs of nested tables twice: iter covers them, fine for these forms
        t = _paragraph(p, numbering)
        if t.strip():
            lines.append((t.strip(), _bold(p)))
    if MARK_BOLD and any(b for _t, b in lines) and not all(b for _t, b in lines):
        return '\n'.join(('**' + t) if b else t for t, b in lines)
    return '\n'.join(t for t, _b in lines)


def table_blocks(tbl, numbering):
    grid_cols = [int(g.get(W + 'w') or 0) for g in tbl.findall(W + 'tblGrid/' + W + 'gridCol')]
    total = sum(grid_cols) or 1
    rows = []
    for tr in _children(tbl, 'tr'):
        col = 0
        trpr = tr.find(W + 'trPr')
        before = trpr.find(W + 'gridBefore') if trpr is not None else None
        if before is not None:
            col += int(before.get(W + 'val'))
        row = []
        for tc in _children(tr, 'tc'):
            pr = tc.find(W + 'tcPr')
            span, vmerge, fill = 1, None, None
            if pr is not None:
                gs = pr.find(W + 'gridSpan')
                span = int(gs.get(W + 'val')) if gs is not None else 1
                vm = pr.find(W + 'vMerge')
                vmerge = (vm.get(W + 'val') or 'continue') if vm is not None else None
                shd = pr.find(W + 'shd')
                fill = (shd.get(W + 'fill') or '').upper() if shd is not None else None
            cell = {'col': col, 'cs': span, 'vm': vmerge}
            if fill in RED:
                cell['bg'] = 'red'
            elif fill in GREY:
                cell['bg'] = 'grey'
            if _is_box(tc):
                cell['box'] = True
                if _box_checked(tc):
                    cell['checked'] = True
            text = _cell_text(tc, numbering)
            if text:
                cell['t'] = text
            if any(_bold(p) for p in tc.iter(W + 'p')) and all(
                    _bold(p) for p in tc.iter(W + 'p') if _run_text(p).strip()):
                cell['b'] = True
            jc = tc.find('.//' + W + 'jc')
            if jc is not None and jc.get(W + 'val') == 'center':
                cell['al'] = 'c'
            row.append(cell)
            col += span
        rows.append(row)
    # row spans: a vMerge "restart" cell spans the following "continue" cells of its column
    for i, row in enumerate(rows):
        for cell in row:
            if cell['vm'] == 'continue':
                cell['skip'] = True
                continue
            if cell['vm'] == 'restart':
                rs = 1
                for nxt in rows[i + 1:]:
                    below = next((c for c in nxt if c['col'] == cell['col']), None)
                    if below is None or below['vm'] != 'continue':
                        break
                    rs += 1
                if rs > 1:
                    cell['rs'] = rs
    out_rows = []
    for row in rows:
        cells = []
        for cell in row:
            if cell.pop('skip', False):
                continue
            cell.pop('vm', None)
            if cell['cs'] == 1:
                cell.pop('cs')
            cells.append(cell)
        out_rows.append(cells)
    widths = [round(100.0 * w / total, 2) for w in grid_cols]
    return {'type': 'table', 'widths': widths, 'rows': out_rows}


def body_blocks(docx_path):
    z = zipfile.ZipFile(docx_path)
    doc = etree.fromstring(z.read('word/document.xml'))
    numbering = {'_fmt': _numbering_formats(z)}
    blocks = []
    body = doc.find(W + 'body')

    def walk(el):
        for ch in el:
            if ch.tag == W + 'tbl':
                blocks.append(table_blocks(ch, numbering))
            elif ch.tag == W + 'p':
                if any(br.get(W + 'type') == 'page' for br in ch.iter(W + 'br')) or \
                        ch.find(W + 'pPr/' + W + 'pageBreakBefore') is not None:
                    blocks.append({'type': 'pagebreak'})
                if ch.find(W + 'pPr/' + W + 'sectPr') is not None:
                    blocks.append({'type': 'pagebreak'})
                text = _paragraph(ch, numbering).strip()
                if text:
                    block = {'type': 'p', 't': text}
                    if _bold(ch):
                        block['b'] = True
                    blocks.append(block)
            elif ch.tag == W + 'sdt':
                content = ch.find(W + 'sdtContent')
                if content is not None:
                    walk(content)
    walk(body)
    # no page break at the very end
    while blocks and blocks[-1]['type'] == 'pagebreak':
        blocks.pop()
    return blocks


def _numbering_formats(z):
    """numId -> 'decimal' or 'bullet' (format of level 0)."""
    try:
        num = etree.fromstring(z.read('word/numbering.xml'))
    except KeyError:
        return {}
    abstract = {}
    for an in num.findall(W + 'abstractNum'):
        lvl = an.find(W + 'lvl')
        fmt = lvl.find(W + 'numFmt') if lvl is not None else None
        abstract[an.get(W + 'abstractNumId')] = fmt.get(W + 'val') if fmt is not None else 'bullet'
    out = {}
    for n in num.findall(W + 'num'):
        aid = n.find(W + 'abstractNumId').get(W + 'val')
        out[n.get(W + 'numId')] = 'decimal' if abstract.get(aid) == 'decimal' else 'bullet'
    return out


# ----------------------------------------------------------------------------------------
# Checklists
# ----------------------------------------------------------------------------------------
def build_checklist(key, spec):
    blocks = body_blocks(form_path(spec))
    # sections 1 and 2 are drawn by the shared template: drop their tables (one or two)
    last_section = max(i for i, b in enumerate(blocks) if b['type'] == 'table' and b['rows']
                       and b['rows'][0] and re.match(r'^[12]\.\s+(company|audit) information',
                                                     (b['rows'][0][0].get('t') or '').strip(), re.I))
    blocks = blocks[last_section + 1:]
    elements = []

    for block in blocks:
        if block['type'] != 'table':
            continue
        header = None  # matrix: (group label, {col: clause})
        for row in block['rows']:
            label = (row[0].get('t') or '').strip() if row else ''
            boxes = [c for c in row if c.get('box')]
            if label in AUDIT_TYPE_LABELS and boxes and header:
                slot = AUDIT_TYPE_LABELS.index(label)
                for cell in boxes:
                    clause = header[1].get(cell['col'], '')
                    idx = next((i for i, e in enumerate(elements)
                                if e['group'] == header[0] and e['clause'] == clause
                                and e.get('_col') == cell['col']), None)
                    if idx is None:
                        elements.append({'group': header[0], 'clause': clause, 'mand': [False] * 3,
                                         '_col': cell['col']})
                        idx = len(elements) - 1
                    elements[idx]['mand'][slot] = cell.get('bg') == 'grey'
                    cell['box'] = [idx, slot]
                    cell.pop('bg', None)
                continue
            if len(boxes) >= 3 and label and label not in AUDIT_TYPE_LABELS:
                elements.append({'group': '', 'clause': label,
                                 'mand': [c.get('bg') == 'grey' for c in boxes[:3]]})
                idx = len(elements) - 1
                for slot, cell in enumerate(boxes[:3]):
                    cell['box'] = [idx, slot]
                    cell.pop('bg', None)
                continue
            if label and not boxes and len(row) > 3 and all(
                    re.match(r'^[\d.]+$', (c.get('t') or '').strip()) for c in row[1:] if c.get('t')):
                header = (label, {c['col']: c.get('t', '').strip() for c in row[1:]})
            # a box that is only a legend ("checked / not checked") stays static
            for cell in boxes:
                if cell.get('box') is True:
                    cell['box'] = 'static'
        for row in block['rows']:
            for cell in row:
                cell.pop('col', None)
    for e in elements:
        e.pop('_col', None)

    # "Notes of auditor(s)": the last table holding only a red title and an empty cell
    notes_title = None
    for i in range(len(blocks) - 1, -1, -1):
        b = blocks[i]
        if b['type'] == 'table' and len(b['rows']) <= 2 and b['rows'][0] \
                and (b['rows'][0][0].get('t') or '').lower().startswith(('notes of', 'auditor notice')):
            notes_title = b['rows'][0][0]['t']
            del blocks[i]
            break
    while blocks and blocks[-1]['type'] == 'pagebreak':
        blocks.pop()

    meta = {k: v for k, v in spec.items() if k not in ('file', 'folder')}
    meta.setdefault('revision', _footer_revision(form_path(spec)))
    meta.setdefault('vkl', _footer_vkl(form_path(spec)))
    return {'key': key, 'meta': meta, 'elements': elements, 'blocks': blocks,
            'notes_title': notes_title or 'Notes of auditor(s)'}


def _footer_cells(path):
    z = zipfile.ZipFile(path)
    for name in sorted(n for n in z.namelist() if re.match(r'word/footer\d*\.xml', n)):
        root = etree.fromstring(z.read(name))
        for tr in root.iter(W + 'tr'):
            cells = [''.join(t.text or '' for t in tc.iter(W + 't')).strip() for tc in tr.iter(W + 'tc')]
            if len(cells) >= 3 and cells[0].startswith(('FM-', 'Formular')):
                return cells
    return []


def _footer_revision(path):
    for c in _footer_cells(path):
        if c.lower().startswith(('revision', 'rev.')):
            return re.sub(r'^(revision:|rev\.)\s*', '', c, flags=re.I).strip()
    return ''


def _footer_vkl(path):
    for c in _footer_cells(path):
        if c.upper().startswith('VKL'):
            return c.split(':', 1)[1].strip()
    return 'Internal'


ISO27001_FILE = "Form 'FM-TAGMBH-MSZ-023_Audit-Checklist-ISO-27001-EN' [English].xlsx"


def build_iso27001():
    """The ISMS checklist is an Excel sheet: one row per chapter or requirement / control,
    with the values the template already holds (rate FC, comments, audit notes...)."""
    import openpyxl
    ws = openpyxl.load_workbook(FORMS / ISO27001_FILE).worksheets[0]

    def text(cell):
        value = ws[cell].value
        return '' if value is None else str(value).strip()

    rows = []
    for r in range(4, ws.max_row + 1):
        sel, ref, req = text('A%d' % r), text('B%d' % r), text('C%d' % r)
        if not (sel or ref or req):
            continue
        rows.append({
            'chapter': sel == 'Chap.',
            'sel': sel, 'ref': ref, 'requirement': req,
            'rate': text('D%d' % r) if text('D%d' % r) in ('FC', 'IM', 'PC', 'NC') else '',
            'evidence': text('E%d' % r), 'findings': text('F%d' % r), 'comments': text('G%d' % r),
            'notes': text('H%d' % r), 'capabilities': text('I%d' % r),
        })
    meta = {'title': text('A1'), 'template': text('A2'),
            'code': 'FM-TAGMBH-MSZ-023_Audit-Checklist-ISO-27001-EN', 'revision': 'Rev.01/17.10.2024'}
    return {'key': 'iso27001', 'meta': meta, 'rows': rows}


def _header_titles(path):
    """(title, subtitle) from the header box of the Word form."""
    z = zipfile.ZipFile(path)
    for name in sorted(n for n in z.namelist() if re.match(r'word/header\d*\.xml', n)):
        root = etree.fromstring(z.read(name))
        rows = [[''.join(t.text or '' for t in tc.iter(W + 't')).strip() for tc in tr.iter(W + 'tc')]
                for tr in root.iter(W + 'tr')]
        texts = [r[0] for r in rows if r and r[0]]
        if texts:
            return texts[0], (texts[1] if len(texts) > 1 else '')
    return '', ''


def build_document(key, spec):
    """A reference document (audit guideline): all of its body, nothing to fill in."""
    global MARK_BOLD
    path = form_path(spec)
    MARK_BOLD = True
    try:
        blocks = body_blocks(path)
    finally:
        MARK_BOLD = False
    for block in blocks:
        if block['type'] == 'table':
            for row in block['rows']:
                for cell in row:
                    cell.pop('col', None)
                    if cell.get('box') is True:
                        cell['box'] = 'static'
    title, subtitle = _header_titles(path)
    footer = _footer_cells(path)
    meta = {'title': title, 'subtitle': subtitle, 'code': footer[0] if footer else '',
            'revision': _footer_revision(path), 'vkl': _footer_vkl(path)}
    return {'key': key, 'meta': meta, 'blocks': blocks}


def main():
    target = MODULE / 'data' / 'checklists'
    target.mkdir(parents=True, exist_ok=True)
    if (FORMS / ISO27001_FILE).exists():
        data = build_iso27001()
        (target / 'iso27001.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
        print('iso27001  %3d rows (%d chapters)' % (len(data['rows']), sum(r['chapter'] for r in data['rows'])))
    for key, spec in DOCUMENTS.items():
        if not form_path(spec).exists():
            print('%-16s skipped: %s not found' % (key, form_path(spec)))
            continue
        data = build_document(key, spec)
        (target / ('%s.json' % key)).write_text(json.dumps(data, ensure_ascii=False, indent=1))
        print('%-16s %3d blocks  %s | %s | rev %s' % (key, len(data['blocks']), data['meta']['title'],
                                                      data['meta']['code'], data['meta']['revision']))
    for key, spec in CHECKLISTS.items():
        if not form_path(spec).exists():
            print('%-10s skipped: %s not found' % (key, form_path(spec)))
            continue
        data = build_checklist(key, spec)
        (target / ('%s.json' % key)).write_text(json.dumps(data, ensure_ascii=False, indent=1))
        print('%-10s %3d elements %3d blocks  rev %s  vkl %s' % (
            key, len(data['elements']), len(data['blocks']),
            data['meta']['revision'], data['meta']['vkl']))


if __name__ == '__main__':
    main()
