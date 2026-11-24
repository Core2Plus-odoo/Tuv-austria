#!/usr/bin/env python3
"""Turn the AQG audit questionnaires / checklists (ESYD, PNAC, SAAC) into JSON the PDF draws.

Development tool, not loaded by Odoo:

    python3 tools/aqg_forms.py           (from the module folder)

writes data/checklists/aqg_<form>.json for every form of AQG_FORMS. Unlike tools/docx_forms.py
it keeps the paragraphs of a cell (a cell of these forms holds a whole list of tick boxes) and
the tables nested in a cell (the "list of required mandatory documents").

What the auditor fills in becomes an input:
* tick boxes and text cells become "lines" (model tuv.form.aqg.line), referenced from the
  blocks as {"in": [sequence, "box_1" | "text_1" ...]}; the Word text is the line's default
  (the "CHECKLIST-EXAMPLES" forms come with example evidence the auditor overwrites);
* the cells of sections 1 and 2 are bound to the ap_* fields: {"ap": key};
* the notes boxes are bound to the form's text fields: {"f": "notes" | "hints" | "findings"}.

The big "Standard requirements" row (tick list on the left, nested table on the right) is
split into one row per nested-table row, the tick list spread over them, so the PDF can break
pages between rows; the left cells lose their inner borders and still look like one cell.
"""
import json
import math
import pathlib
import re
import sys
import zipfile

from lxml import etree

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import docx_forms as dx  # noqa: E402  (sdt-aware children, tick box and footer helpers)

W = dx.W
W14 = '{http://schemas.microsoft.com/office/word/2010/wordml}'
MODULE = pathlib.Path(__file__).resolve().parent.parent
CUSTOM = MODULE.parent.parent
ESYD = CUSTOM / 'ODOO_ESYD'
PNAC = CUSTOM / 'ODOO_PNAC'
SAAC = CUSTOM / 'ODOO_SAAC'

# key: Word file, footer form code (the Word footer shows a FILENAME field, whose cached text
# is out of date), page orientation of the PDF, paragraphs that start a new page.
AQG_FORMS = {
    'aqg_esyd_27001': dict(
        file=ESYD / 'FM-BA-ZET-MS-All-008-AQG-27001-EN.docx',
        code='FM-BA-ZET-MS-All-008-AQG-27001-EN_CHECKLIST', landscape=False,
        break_before=['ANNEX A']),
    'aqg_esyd_9001_14001_45001': dict(
        file=ESYD / 'FM-BA-ZET-MS-All-008-AQG-9001-14001-45001-EN_CHECKLIST-EXAMPLES.docx',
        code='FM-BA-ZET-MS-All-008-AQG-9001-14001-45001-EN_CHECKLIST-EXAMPLES', landscape=True),
    'aqg_esyd_9001_14001': dict(
        file=ESYD / 'FM-BA-ZET-MS-All-008-AQG-9001-14001-EN_CHECKLIST-EXAMPLES.docx',
        code='FM-BA-ZET-MS-All-008-AQG-9001-14001-EN_CHECKLIST-EXAMPLES', landscape=True),
    # byte-identical copy in ODOO_PNAC: one form, two cards
    'aqg_9001_22000': dict(
        file=ESYD / 'FM-BA-ZET-MS-All-008-AQG-9001-22000-EN_CHECKLIST-EXAMPLES.docx',
        code='FM-BA-ZET-MS-All-008-AQG-9001-22000-EN_CHECKLIST-EXAMPLES', landscape=True),
    'aqg_pnac_22000': dict(
        file=PNAC / 'FM-BA-ZET-MS-All-008-AQG-22000-EN_CHECKLIST.docx',
        code='FM-BA-ZET-MS-All-008-AQG-22000-EN_CHECKLIST', landscape=True),
    'aqg_saac_9001': dict(
        file=SAAC / 'ISO 9001' / "ENG-Form 'FM-BA-ZET-MS-All-009b-AQG-Audit-Checkliste-9001' [English].docx",
        code='FM-BA-ZET-MS-All-009b-AQG-Audit-checklist-9001', landscape=True),
}

# Word's prompts in empty fields: never printed
PLACEHOLDERS = re.compile('|'.join([
    r'Click or (?:type|tap) here to enter text\.?', r'Chose Audit Type', r'Please chose',
    r'Selection of Scopes', r'\bChoose\b', r'\bSelect\b',
    r'Enter (?:date|stage|audit method|standard|audit type|audit team member)',
    r'dd\.mm\.yyyy', r'\bxx\b', r'yes / no / partly',
    # example dates of the ESYD forms' audit dates
    r'\d{2}\.\d{2}\.\d{4}(?:\s+until\s+\d{2}\.\d{2}\.\d{4})?',
]))

# label cell of sections 1/2 -> ap key of the cell next to it
LABEL_BINDINGS = [
    (r'^Company name', 'partner'), (r'^Address', 'address'), (r'^Other audited sites', 'sites'),
    (r'^Company representative', 'representative'), (r'^Company description', 'scope'),
    (r'^Scope of\s*application', 'scope'),
]
# "Label:" paragraph of sections 1/2 -> ap key of the value printed after it
PARA_BINDINGS = [
    (r'^Stage 1:', 'stage1'), (r'^Stage 2:', 'stage2'), (r'^until:', 'until'),
    (r'^Surveillance:', 'surveillance'), (r'^Recertification:', 'recertification'),
    (r'^Remote:', 'remote'), (r'^Use of remote activities[^:]*:', 'remote'),
    (r'^Audit type:', 'audit_type'), (r'^Audit [Mm]ethod:', 'method'),
    (r'^Number of employees relevant for the Scope:', 'employees_scope'),
    (r'^No\. of employees in scope:', 'employees_scope'), (r'^No\. of employees:', 'employees'),
    (r'^Audit duration:', 'duration'), (r'^Audit language:', 'language'),
    (r'^EAC [Ss]cope:', 'eac'), (r'^NACE [Cc](?:ODE|ode)[^:]*:', 'nace'), (r'^Category[^:]*:', 'category'),
]
STD_HEADER = re.compile(r'^(Standard (\d)|Other \(specify\)|Standard 4 \(further\))')
DEFAULT_SZ = 20  # half-points


# ----------------------------------------------------------------------------------------
# Word -> paragraphs and tables
# ----------------------------------------------------------------------------------------
class Doc:
    def __init__(self, path):
        self.zip = zipfile.ZipFile(path)
        self.root = etree.fromstring(self.zip.read('word/document.xml'))
        self.numbering = {'_fmt': dx._numbering_formats(self.zip)}
        self.style_sz, self.default_sz = self._styles()

    def _styles(self):
        styles = etree.fromstring(self.zip.read('word/styles.xml'))
        default = styles.find('.//' + W + 'rPrDefault/' + W + 'rPr/' + W + 'sz')
        default_sz = int(default.get(W + 'val')) if default is not None else DEFAULT_SZ
        raw, based = {}, {}
        for st in styles.findall(W + 'style'):
            sid = st.get(W + 'styleId')
            sz = st.find(W + 'rPr/' + W + 'sz')
            raw[sid] = int(sz.get(W + 'val')) if sz is not None else None
            parent = st.find(W + 'basedOn')
            based[sid] = parent.get(W + 'val') if parent is not None else None
            if st.get(W + 'type') == 'paragraph' and st.get(W + 'default') == '1':
                raw['_default'] = sid

        def resolve(sid, depth=0):
            if sid is None or depth > 10:
                return default_sz
            return raw.get(sid) or resolve(based.get(sid), depth + 1)
        out = {sid: resolve(sid) for sid in raw if sid != '_default'}
        return out, out.get(raw.get('_default'), default_sz)

    # ---- paragraphs ------------------------------------------------------------------
    def para(self, p):
        """{'parts': [[box, text], ...], 'sz', 'b', 'c', 'al', 'pb'}; box None (no box) or
        the box's checked state."""
        parts = [[None, '']]
        state = {'pb': False}

        def add(text):
            parts[-1][1] += text

        def walk(el):
            for n in el:
                tag = n.tag
                if tag == W + 'sdt':
                    pr = n.find(W + 'sdtPr')
                    if pr is not None and pr.find(W14 + 'checkbox') is not None:
                        checked = pr.find(W14 + 'checkbox/' + W14 + 'checked')
                        parts.append([checked is not None and checked.get(W14 + 'val') in ('1', 'true'), ''])
                        continue
                    content = n.find(W + 'sdtContent')
                    if content is not None:
                        walk(content)
                elif tag == W + 'r':
                    va = n.find(W + 'rPr/' + W + 'vertAlign')
                    sup = va is not None and va.get(W + 'val') == 'superscript'
                    for c in n:
                        if c.tag == W + 't':
                            add((c.text or '').translate(dx.SUPERSCRIPT) if sup else (c.text or ''))
                        elif c.tag == W + 'tab':
                            add(' ')
                        elif c.tag == W + 'br':
                            if c.get(W + 'type') == 'page':
                                state['pb'] = True
                            else:
                                add('\n')
                        elif c.tag == W + 'fldChar' and c.find(W + 'ffData/' + W + 'checkBox') is not None:
                            box = c.find(W + 'ffData/' + W + 'checkBox')
                            value = box.find(W + 'checked')
                            if value is None:
                                value = box.find(W + 'default')
                            parts.append([value is not None and value.get(W + 'val') in (None, '1', 'true'), ''])
                elif tag in (W + 'hyperlink', W + 'smartTag', W + 'ins', W + 'customXml', W + 'fldSimple'):
                    walk(n)
        walk(p)
        for part in parts:
            part[1] = part[1].replace('☐', '').replace('☒', '')
        parts = [pt for i, pt in enumerate(parts) if pt[0] is not None or pt[1] or i == len(parts) - 1]
        if parts:
            parts[0][1] = parts[0][1].lstrip('\n ')
            parts[-1][1] = parts[-1][1].rstrip()
        out = {'parts': parts}
        if p.find(W + 'pPr/' + W + 'pageBreakBefore') is not None:
            state['pb'] = True
        if state['pb']:
            out['pb'] = True
        # numbering ("1." of the audit objectives); tick-box lists are not numbered
        num = p.find(W + 'pPr/' + W + 'numPr')
        text = ''.join(pt[1] for pt in parts)
        if num is not None and text.strip() and all(pt[0] is None for pt in parts):
            num_id = num.find(W + 'numId')
            key = num_id.get(W + 'val') if num_id is not None else '0'
            if key != '0':
                self.numbering[key] = self.numbering.get(key, 0) + 1
                if self.numbering['_fmt'].get(key) == 'decimal':
                    parts[0][1] = '%d. ' % self.numbering[key] + parts[0][1]
                else:
                    parts[0][1] = '• ' + parts[0][1]
        run = next((r for r in p.iter(W + 'r') if ''.join(t.text or '' for t in r.iter(W + 't')).strip()), None)
        sz = None
        rpr = run.find(W + 'rPr') if run is not None else None
        if rpr is not None and rpr.find(W + 'sz') is not None:
            sz = int(rpr.find(W + 'sz').get(W + 'val'))
        if sz is None:
            mark = p.find(W + 'pPr/' + W + 'rPr/' + W + 'sz')
            pstyle = p.find(W + 'pPr/' + W + 'pStyle')
            if mark is not None:
                sz = int(mark.get(W + 'val'))
            elif pstyle is not None:
                sz = self.style_sz.get(pstyle.get(W + 'val'))
        out['sz'] = sz or self.default_sz
        if dx._bold(p):
            out['b'] = True
        color = rpr.find(W + 'color') if rpr is not None else None
        if color is not None and (color.get(W + 'val') or '').upper() not in ('AUTO', '000000', ''):
            out['c'] = color.get(W + 'val').upper()
        jc = p.find(W + 'pPr/' + W + 'jc')
        if jc is not None and jc.get(W + 'val') in ('center', 'right', 'both'):
            out['al'] = {'center': 'c', 'right': 'r', 'both': 'j'}[jc.get(W + 'val')]
        return out

    # ---- tables ----------------------------------------------------------------------
    def cell_items(self, el):
        items = []
        for ch in el:
            if ch.tag == W + 'p':
                items.append(self.para(ch))
            elif ch.tag == W + 'tbl':
                items.append({'tbl': self.table(ch)})
            elif ch.tag == W + 'sdt':
                content = ch.find(W + 'sdtContent')
                if content is not None:
                    items.extend(self.cell_items(content))
        return items

    def table(self, tbl):
        grid = [int(g.get(W + 'w') or 0) for g in tbl.findall(W + 'tblGrid/' + W + 'gridCol')]
        rows = []
        head = 0
        for tr in dx._children(tbl, 'tr'):
            trpr = tr.find(W + 'trPr')
            col = 0
            row = {'cells': []}
            if trpr is not None:
                before = trpr.find(W + 'gridBefore')
                if before is not None:
                    col += int(before.get(W + 'val'))
                height = trpr.find(W + 'trHeight')
                if height is not None and int(height.get(W + 'val') or 0) > 300:
                    row['h'] = round(int(height.get(W + 'val')) / 20.0, 1)
                if trpr.find(W + 'tblHeader') is not None and head == len(rows):
                    head += 1
            for tc in dx._children(tr, 'tc'):
                pr = tc.find(W + 'tcPr')
                cell = {'col': col, 'cs': 1}
                if pr is not None:
                    gs = pr.find(W + 'gridSpan')
                    cell['cs'] = int(gs.get(W + 'val')) if gs is not None else 1
                    vm = pr.find(W + 'vMerge')
                    if vm is not None:
                        cell['vm'] = vm.get(W + 'val') or 'continue'
                    shd = pr.find(W + 'shd')
                    fill = (shd.get(W + 'fill') or '').upper() if shd is not None else ''
                    if fill and fill not in ('AUTO', 'FFFFFF'):
                        cell['bg'] = fill
                    va = pr.find(W + 'vAlign')
                    if va is not None and va.get(W + 'val') in ('center', 'bottom'):
                        cell['va'] = va.get(W + 'val')
                if tc.get('tuvbox'):
                    cell['box'] = bool(tc.get('tuvchecked'))
                cell['items'] = self.cell_items(tc)
                row['cells'].append(cell)
                col += cell['cs']
            rows.append(row)
        for i, row in enumerate(rows):
            for cell in row['cells']:
                if cell.get('vm') == 'continue':
                    cell['skip'] = True
                elif cell.get('vm') == 'restart':
                    rs = 1
                    for nxt in rows[i + 1:]:
                        below = next((c for c in nxt['cells'] if c['col'] == cell['col']), None)
                        if below is None or below.get('vm') != 'continue':
                            break
                        rs += 1
                    if rs > 1:
                        cell['rs'] = rs
        # a table made only of "repeat header" rows repeats nothing (SAAC process table)
        if head >= len(rows):
            head = 0
        return {'type': 'table', 'grid': grid, 'head': head, 'rows': rows}

    def body(self):
        blocks = []

        def walk(el):
            for ch in el:
                if ch.tag == W + 'tbl':
                    blocks.append(self.table(ch))
                elif ch.tag == W + 'p':
                    p = self.para(ch)
                    if p.get('pb') or ch.find(W + 'pPr/' + W + 'sectPr') is not None:
                        blocks.append({'type': 'pagebreak'})
                    if _ptext(p).strip() or any(pt[0] is not None for pt in p['parts']):
                        blocks.append({'type': 'p', 'p': p})
                elif ch.tag == W + 'sdt':
                    content = ch.find(W + 'sdtContent')
                    if content is not None:
                        walk(content)
        walk(self.root.find(W + 'body'))
        return blocks

    def header_lines(self):
        for name in sorted(n for n in self.zip.namelist() if re.match(r'word/header\d*\.xml', n)):
            root = etree.fromstring(self.zip.read(name))
            rows = [[c for c in tr.iter(W + 'tc')] for tr in root.iter(W + 'tr')]
            if rows:
                return ['\n'.join(t for t in (''.join(x.text or '' for x in p.iter(W + 't')).strip()
                                              for p in row[0].iter(W + 'p')) if t) for row in rows]
        return []


def _ptext(p):
    return ''.join(pt[1] for pt in p.get('parts', []))


def _ctext(cell):
    return '\n'.join(_ptext(it) for it in cell.get('items', []) if 'parts' in it and _ptext(it).strip()).strip()


def _clean(text):
    return re.sub(r'\s+', ' ', PLACEHOLDERS.sub('', text)).strip()


def _first_text(table):
    for row in table['rows']:
        for cell in row['cells']:
            if _ctext(cell):
                return _ctext(cell)
    return ''


# ----------------------------------------------------------------------------------------
# Inputs
# ----------------------------------------------------------------------------------------
class Builder:
    def __init__(self, key, spec):
        self.key, self.spec = key, spec
        self.doc = Doc(spec['file'])
        self.lines = []

    def line(self, list_key, label='', section='', ref='', box=(), mand=(), text=()):
        self.lines.append({
            'list': list_key, 'label': label.strip(), 'section': section.strip(), 'ref': ref.strip(),
            'box': (list(box) + [False] * 3)[:3], 'mand': (list(mand) + [False] * 3)[:3],
            'text': (list(text) + [''] * 3)[:3],
        })
        return len(self.lines) - 1

    # ---- sections 1 and 2 ----------------------------------------------------------------
    def bind_sections(self, table):
        std_cols, team_hdr = None, None
        for row in table['rows']:
            cells = [c for c in row['cells'] if not c.get('skip')]
            texts = [_ctext(c) for c in cells]
            if team_hdr is not None:
                for c in cells:
                    if c['col'] in team_hdr:
                        c['ap'] = team_hdr[c['col']]
                team_hdr = None
                continue
            if texts and texts[0] == 'Lead Auditor':
                labels = [t for t in texts]
                n_aud = sum(1 for t in labels[1:] if t in ('Auditor', 'Enter audit team member'))
                team_hdr, i = {}, 0
                for c, t in zip(cells, labels):
                    if t == 'Lead Auditor':
                        team_hdr[c['col']] = 'lead'
                    elif t in ('Auditor', 'Enter audit team member'):
                        team_hdr[c['col']] = 'team:%d:%d' % (i, n_aud)
                        i += 1
                        if t != 'Auditor':
                            c['items'] = [dict(c['items'][0], parts=[[None, 'Auditor']])]
                    elif t == 'Expert':
                        team_hdr[c['col']] = 'expert'
                    else:
                        team_hdr[c['col']] = 'other'
                continue
            header = {}
            for c, t in zip(cells, texts):
                m = STD_HEADER.match(t)
                if m:
                    header[c['col']] = m.group(2) or 'more'
            if len(header) >= 2:
                last = max(int(n) for n in header.values() if n != 'more')
                std_cols = {col: ('%d+' % (last + 1) if n == 'more' else n) for col, n in header.items()}
                continue
            if std_cols:
                first = row['cells'][0]
                label = '' if first.get('skip') or first['col'] in std_cols else _ctext(first)
                kind = ('std' if not label or label.startswith('Audit standard') else
                        'stdtype' if label.startswith('Audit type') else
                        'stdreg' if label.startswith('Registration') else None)
                if kind:
                    for c in cells:
                        rest = _clean(_ctext(c))
                        if c['col'] in std_cols and (not rest or rest.endswith(':')):
                            c['ap'] = '%s:%s' % (kind, std_cols[c['col']])
                            c['bound'] = True
                    continue
                std_cols = None
            if texts and texts[0].startswith('Audit date(s)'):
                k = 0
                for c, t in zip(cells[1:], texts[1:]):
                    if t.startswith('Enter date'):
                        k += 1
                        c['ap'] = 'pdate:%d' % k
                    elif t.startswith('Enter stage'):
                        c['ap'] = 'pstage:%d' % k
                    c['bound'] = True
                continue
            for j, c in enumerate(cells[:-1]):
                if not c.get('bg'):
                    continue
                for pattern, key in LABEL_BINDINGS:
                    if re.match(pattern, re.sub(r'\s+', ' ', texts[j])) and not _clean(texts[j + 1]) \
                            and not any(pt[0] is not None for it in cells[j + 1]['items'] for pt in it.get('parts', [])):
                        cells[j + 1]['ap'] = key
                        cells[j + 1]['bound'] = True
            for c in cells:
                if c.get('bg') or c.get('bound'):
                    continue
                for p in c['items']:
                    if 'parts' not in p:
                        continue
                    for part in p['parts']:
                        if part[0] is None:
                            continue
                        label = part[1].strip()
                        if label.lower().startswith('no changes'):
                            part[0] = {'ap': 'scope_nochange'}
                        elif label.lower().startswith('adjustment required'):
                            part[0] = {'ap': 'scope_adjust'}
                        else:
                            part[0] = {'in': [self.line('objective', label, 'Audit Objective',
                                                        box=[part[0]]), 'box_1']}
                    text = _ptext(p).strip()
                    for pattern, key in PARA_BINDINGS:
                        m = re.match(pattern, text)
                        if m:
                            rest = _clean(text[m.end():])
                            if rest in ('', '0'):
                                p['parts'] = [[None, m.group(0)]]
                                p['ap'] = key
                            break
                # a label wrapped over two paragraphs ("NACE code (only for" / "EMAS):")
                paras = [p for p in c['items'] if 'parts' in p]
                if paras and not any(p.get('ap') or any(pt[0] is not None for pt in p['parts'])
                                     for p in paras):
                    text = re.sub(r'\s+', ' ', ' '.join(_ptext(p) for p in paras)).strip()
                    for pattern, key in PARA_BINDINGS:
                        m = re.match(pattern, text)
                        if m and _clean(text[m.end():]) in ('', '0'):
                            c['items'] = [dict(paras[0], parts=[[None, m.group(0)]], ap=key)]
                            break
        # what is left of Word's prompts goes
        for row in table['rows']:
            for c in row['cells']:
                for p in c['items']:
                    for part in p.get('parts', []):
                        part[1] = re.sub(r'[ ]{2,}', ' ', PLACEHOLDERS.sub('', part[1])).strip(' ') \
                            if part[0] is None else part[1]
                kept = [p for p in c['items'] if 'tbl' in p or _ptext(p).strip()
                        or any(pt[0] is not None for pt in p['parts'])]
                # an emptied field keeps one (empty) paragraph: its size is the value's size
                c['items'] = kept or c['items'][:1]
                c.pop('bound', None)

    # ---- legislative requirements ---------------------------------------------------------
    def bind_legal(self, table):
        for row in table['rows'][1:]:
            cells = [c for c in row['cells'] if not c.get('skip')]
            if len(cells) == 2:
                seq = self.line('legal', _ctext(cells[0]), text=[_ctext(cells[1])])
                cells[1]['in'] = [seq, 'text_1']

    # ---- standard requirements ------------------------------------------------------------
    def bind_requirements(self, table):
        """Left cell: tick list (one line per box); right cell: nested tables whose evidence
        cells (columns under an "ISO ..." header, or after "Objective evidences:") are inputs."""
        body = table['rows'][1]
        left, right = [c for c in body['cells'] if not c.get('skip')][:2]
        section, last = '', None
        for p in left['items']:
            if 'parts' not in p:
                continue
            text = _ptext(p).strip()
            boxes = [pt for pt in p['parts'] if pt[0] is not None]
            if boxes:
                for part in boxes:
                    label = part[1].strip()
                    if p.get('b') or p.get('c'):
                        section = label
                    seq = self.line('clause', label, section, box=[part[0]])
                    part[0] = {'in': [seq, 'box_1']}
                    last = seq
            elif text and (p.get('b') or p.get('c') or text.isupper()):
                section, last = text, None
            elif text and last is not None:
                self.lines[last]['label'] += ' ' + text
        section = ''
        for item in right['items']:
            if 'parts' in item:
                # "Clauses 4 - 10", "ANNEX A"; not "List of required mandatory documents:"
                if _ptext(item).strip() and len(_ptext(item)) < 40 and not _ptext(item).strip().endswith(':'):
                    section = _ptext(item).strip()
                continue
            nested = item['tbl']
            header = nested['rows'][0]['cells']
            std_cols = {c['col']: i for i, c in enumerate(
                [c for c in header if re.match(r'^ISO\s*\d', _ctext(c))])}
            sub = section
            for r, row in enumerate(nested['rows']):
                cells = [c for c in row['cells'] if not c.get('skip')]
                if r == 0 and std_cols:
                    continue
                if len(cells) == 1 and _ctext(cells[0]) and not std_cols:
                    sub = _ctext(cells[0])
                    continue
                if std_cols:
                    inputs = [c for c in cells if c['col'] in std_cols]
                    if not inputs:
                        continue
                    ref = ' / '.join(_ctext(c).replace('\n', ' ') for c in cells
                                     if c['col'] not in std_cols and _ctext(c))
                    texts = [''] * 3
                    for c in inputs:
                        texts[std_cols[c['col']]] = _ctext(c)
                    seq = self.line('evidence', ref=ref, section=sub, text=texts)
                    for c in inputs:
                        c['in'] = [seq, 'text_%d' % (std_cols[c['col']] + 1)]
                    continue
                for c in cells:
                    for p in c['items']:
                        if 'parts' in p and _ptext(p).strip().startswith('Objective evidence'):
                            ref = _ctext(cells[0]).replace('\n', ' ')
                            p['in'] = [self.line('evidence', ref=ref, section=sub), 'text_1']

    def bind_elements(self, table):
        """SAAC: a row with three tick boxes (CA/RA, 1. SA, 2. SA); grey = mandatory."""
        for row in table['rows']:
            cells = [c for c in row['cells'] if not c.get('skip')]
            boxes = [c for c in cells if 'box' in c]
            label = _ctext(cells[0]) if cells else ''
            if len(boxes) >= 3 and label:
                seq = self.line('element', label, box=[c['box'] for c in boxes[:3]],
                                mand=[bool(c.get('bg')) for c in boxes[:3]])
                for i, c in enumerate(boxes[:3]):
                    c['in'] = [seq, 'box_%d' % (i + 1)]

    # ---- layout ------------------------------------------------------------------------
    def flatten(self, table):
        """Split the requirements row: one outer row per chunk of the right cell (paragraphs,
        or rows of a nested table tied by merges), the tick list spread to match heights."""
        grid = table['grid']
        body = table['rows'][1]
        left, right = [c for c in body['cells'] if not c.get('skip')][:2]
        lw = sum(grid[left['col']:left['col'] + left['cs']])
        rw = sum(grid[right['col']:right['col'] + right['cs']])
        chunks = []  # (items for the right cell, height, marker text)
        paras = []
        for item in right['items']:
            if 'parts' in item:
                if _ptext(item).strip():
                    paras.append(item)
                continue
            if paras:
                chunks.append((paras, sum(_height(p, rw) for p in paras), _ptext(paras[0]).strip()))
                paras = []
            nested = item['tbl']
            total = sum(nested['grid']) or 1
            groups, cur, reach = [], [], 0
            for r, row in enumerate(nested['rows']):
                cur.append(row)
                reach = max([reach] + [r + c.get('rs', 1) - 1 for c in row['cells'] if not c.get('skip')])
                if reach <= r:
                    groups.append(cur)
                    cur = []
            if cur:
                groups.append(cur)
            for group in groups:
                height = 0
                for row in group:
                    hs = [sum(_height(p, rw * sum(nested['grid'][c['col']:c['col'] + c['cs']]) / total)
                              for p in c['items'] if 'parts' in p) + 4
                          for c in row['cells'] if not c.get('skip')]
                    height += max(hs + [row.get('h', 0)])
                chunks.append(([{'tbl': dict(nested, rows=group, head=0)}], height, ''))
        if paras:
            chunks.append((paras, sum(_height(p, rw) for p in paras), _ptext(paras[0]).strip()))
        lefts = [p for p in left['items'] if 'parts' in p and (_ptext(p).strip() or
                                                                 any(pt[0] is not None for pt in p['parts']))]
        # paragraphs in both cells ("ANNEX A") line up
        markers = [c[2] for c in chunks if c[2] and any(_ptext(p).strip() == c[2] for p in lefts)]
        assigned = [[] for _c in chunks]
        start_c, start_l = 0, 0
        for marker in markers + [None]:
            end_c = next((i for i, c in enumerate(chunks) if c[2] == marker), len(chunks)) \
                if marker else len(chunks)
            end_l = next((i for i, p in enumerate(lefts) if _ptext(p).strip() == marker), len(lefts)) \
                if marker else len(lefts)
            seg = chunks[start_c:end_c] or chunks[start_c:start_c + 1]
            bounds, acc = [], 0
            for c in seg:
                acc += c[1]
                bounds.append(acc)
            pos = 0
            for p in lefts[start_l:end_l]:
                k = next((i for i, b in enumerate(bounds) if pos < b), len(bounds) - 1)
                assigned[min(start_c + k, len(chunks) - 1)].append(p)
                pos += _height(p, lw)
            start_c, start_l = end_c, end_l
        rows = [table['rows'][0]]
        breaks = self.spec.get('break_before', [])
        for i, (items, _h, marker) in enumerate(chunks):
            row = {'cells': [
                dict(left, items=assigned[i], rs=1, bt=(i == 0), bb=(i == len(chunks) - 1)),
                dict(right, items=items, rs=1, pad=0 if 'tbl' in items[0] else None),
            ]}
            if marker and marker in breaks:
                row['pb'] = True
            rows.append(row)
        table['rows'] = rows + table['rows'][2:]
        table['head'] = max(table['head'], 1)
        self.split_header(table, chunks)

    def split_header(self, table, chunks):
        """"Standard requirements      ISO 9001:2015      ISO 14001:2015": the standards over
        their evidence columns."""
        head = table['rows'][0]['cells'][0]
        segments = [s for s in re.split(r'\s{3,}', _ctext(head)) if s]
        nested = next((it['tbl'] for c in chunks for it in c[0] if 'tbl' in it), None)
        if len(segments) < 2 or not nested:
            return
        std = [c for c in nested['rows'][0]['cells'] if re.match(r'^ISO\s*\d', _ctext(c))]
        if len(std) != len(segments) - 1:
            return
        p0 = head['items'][0]
        title = dict(p0, parts=[[None, segments[0]]])
        cells, col = [], 0
        for c, seg in zip(std, segments[1:]):
            if c['col'] > col:
                cells.append({'col': col, 'cs': c['col'] - col, 'items': [], 'nob': True})
            cells.append({'col': c['col'], 'cs': c['cs'], 'items': [dict(p0, parts=[[None, seg]], al='c')], 'nob': True})
            col = c['col'] + c['cs']
        inner = {'tbl': dict(nested, rows=[{'cells': cells}], head=0, nob=True)}
        left = dict(head, items=[title], cs=1)
        right = dict(head, items=[inner], cs=head['cs'] - 1, col=head['col'] + 1, pad=0)
        table['rows'][0] = dict(table['rows'][0], cells=[left, right])

    # ---- the whole form ------------------------------------------------------------------
    def build(self):
        blocks = self.doc.body()
        out = []
        sections_done = False
        i = 0
        while i < len(blocks):
            b = blocks[i]
            i += 1
            if b['type'] != 'table':
                out.append(b)
                continue
            first = _first_text(b)
            # a page break typed at the start of the table's first cell
            p0 = next((p for r in b['rows'][:1] for c in r['cells'] for p in c['items'] if 'parts' in p), None)
            if p0 and p0.pop('pb', False):
                out.append({'type': 'pagebreak'})
            low = first.lower().lstrip('/ ')
            if not sections_done and re.match(r'^[12]\.\s+(company|audit) information', low):
                self.bind_sections(b)
            elif re.match(r'^\d\.\s*legislative', low):
                sections_done = True
                self.bind_legal(b)
            elif low.startswith('standard requirements'):
                sections_done = True
                self.bind_requirements(b)
                self.flatten(b)
            elif low.startswith('process oriented'):
                sections_done = True
                self.bind_elements(b)
            elif low.startswith(('auditor notes', 'notes of auditor')):
                if len(b['rows']) < 2:
                    b['rows'].append({'h': 300, 'cells': [{'col': 0, 'cs': len(b['grid']), 'items': []}]})
                box = b['rows'][1]
                box['cells'][0]['f'] = 'notes'
                # Word sizes the box with empty paragraphs (SAAC): keep that height
                if not box.get('h'):
                    box['h'] = round(sum(_height(p, 10000) for p in box['cells'][0]['items']
                                         if 'parts' in p), 1)
            elif 'improvement hints' in low or 'positive findings' in low:
                b['rows'] = b['rows'][:1]
                out.append(b)
                # the "Xx" / "…" sample bullets under the bar
                while i < len(blocks) and blocks[i]['type'] == 'p' and \
                        _ptext(blocks[i]['p']).strip().strip('•').strip() in ('Xx', '…', '...', ''):
                    i += 1
                out.append({'type': 'checks', 'f': 'hints' if 'hints' in low else 'findings'})
                continue
            sections_done = sections_done or not re.match(r'^[12]\.', low)
            out.append(b)
        # page breaks: never two in a row, none at the ends
        blocks = []
        for b in out:
            if b['type'] == 'pagebreak' and (not blocks or blocks[-1]['type'] == 'pagebreak'):
                continue
            blocks.append(b)
        while blocks and blocks[-1]['type'] == 'pagebreak':
            blocks.pop()
        blocks = [self.finish(b) for b in blocks]
        header = self.doc.header_lines()
        path = self.spec['file']
        meta = {
            'title': header[0] if header else '',
            'subtitle': header[1] if len(header) > 1 else '',
            'code': self.spec['code'],
            'revision': dx._footer_revision(path),
            'vkl': dx._footer_vkl(path),
            'landscape': self.spec['landscape'],
            'sz': self.doc.default_sz,
        }
        return {'key': self.key, 'meta': meta, 'lines': self.lines, 'blocks': blocks}

    # ---- JSON for the template: widths in %, styles as strings ----------------------------
    def finish(self, block):
        if block['type'] == 'p':
            return {'type': 'p', 'p': _pfinish(block['p'], self.doc.default_sz)}
        if block['type'] != 'table':
            return block
        return _tfinish(block, self.doc.default_sz)


def _height(p, width):
    """Rough height (pt) of a paragraph in a column `width` twips wide."""
    sz = p.get('sz') or DEFAULT_SZ
    per_line = max(1, width / (sz * 5.0))
    lines = sum(max(1, math.ceil(len(seg) / per_line)) for seg in _ptext(p).split('\n'))
    return lines * sz / 2.0 * 1.2


def _pfinish(p, default_sz):
    st = []
    if p.get('sz') and p['sz'] != default_sz:
        st.append('font-size: %gpt;' % (p['sz'] / 2.0))
    if p.get('b'):
        st.append('font-weight: bold;')
    if p.get('c'):
        st.append('color: #%s;' % p['c'])
    if p.get('al'):
        st.append('text-align: %s;' % {'c': 'center', 'r': 'right', 'j': 'justify'}[p['al']])
    out = {'parts': p['parts']}
    if st:
        out['st'] = ' '.join(st)
    for key in ('ap', 'in'):
        if key in p:
            out[key] = p[key]
    return out


def _tfinish(table, default_sz):
    total = sum(table['grid']) or 1
    rows = []
    for row in table['rows']:
        # a thin empty divider row of Word (SAAC): no text height
        spacer = not row.get('h') and not any(
            'box' in c or any(k in c for k in ('in', 'ap', 'f')) or _ctext(c)
            or any('tbl' in it for it in c['items']) for c in row['cells'] if not c.get('skip'))
        cells = []
        for c in row['cells']:
            if c.get('skip'):
                continue
            st = []
            if c.get('bg'):
                st.append('background: #%s;' % c['bg'])
                # the red bars' white text comes from the table style in some forms
                if c['bg'] in ('C00000', 'CC0000', 'FF0000'):
                    st.append('color: #FFFFFF;')
            st.append('vertical-align: %s;' % {'center': 'middle', 'bottom': 'bottom'}.get(c.get('va'), 'top'))
            if c.get('bt') is False:
                st.append('border-top: none;')
            if c.get('bb') is False:
                st.append('border-bottom: none;')
            if c.get('pad') == 0:
                st.append('padding: 0;')
            if c.get('nob'):
                st.append('border: none;')
            if row.get('h'):
                st.append('height: %gpt;' % row['h'])
            if spacer:
                st.append('height: 3pt; padding: 0;')
            if 'box' in c and 'in' not in c:
                c['items'] = [{'parts': [[c['box'], '']], 'al': 'c'}]
            cell = {'st': ' '.join(st), 'ps': []}
            for item in c['items']:
                if 'tbl' in item:
                    cell['ps'].append({'tbl': _tfinish(item['tbl'], default_sz)})
                else:
                    cell['ps'].append(_pfinish(item, default_sz))
            if c.get('cs', 1) > 1:
                cell['cs'] = c['cs']
            if c.get('rs', 1) > 1:
                cell['rs'] = c['rs']
            for key in ('in', 'ap', 'f'):
                if key in c:
                    cell[key] = c[key]
            cells.append(cell)
        out = {'cells': cells}
        if row.get('pb'):
            out['pb'] = True
        rows.append(out)
    out = {'type': 'table', 'widths': [round(100.0 * w / total, 2) for w in table['grid']],
           'head': table.get('head', 0), 'rows': rows}
    if table.get('nob'):
        out['nob'] = True
    return out


def main():
    target = MODULE / 'data' / 'checklists'
    for key, spec in AQG_FORMS.items():
        data = Builder(key, spec).build()
        (target / ('%s.json' % key)).write_text(json.dumps(data, ensure_ascii=False, indent=0))
        counts = {}
        for line in data['lines']:
            counts[line['list']] = counts.get(line['list'], 0) + 1
        print('%-28s %s  rev %s  vkl %s' % (key, counts, data['meta']['revision'], data['meta']['vkl']))


if __name__ == '__main__':
    main()
