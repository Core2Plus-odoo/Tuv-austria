"""Read an MDC annex (.docx) and hand back everything the module stores.

The annexes of `VB-BA-ZET-MS-All-003` do not share a layout: one prints its audit
duration table split by complexity, another by the kind of audit, a third has no
personnel bands at all. So the file is read the way it is written - the grey rows
of the document become sections, and the tables that are calculated with (duration
bands, risk / complexity categories, adjustment factors) are recognised by their own
headers and returned separately.

Nothing here touches Odoo: it is plain parsing over the Word XML, which keeps it
testable and lets the import wizard stay thin.
"""

import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
V = '{urn:schemas-microsoft-com:vml}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

NUM = re.compile(r'^\s*(?:≥\s*)?([\d.,]+)\s*(?:[-–—~～]|to)\s*([\d.,]+)\s*$')
OPEN_UP = re.compile(r'^\s*(?:>|≥|more than|over)\s*([\d.,]+)')


def txt_of(p):
    out = ''
    for n in p.iter():
        if n.tag == W + 't':
            out += n.text or ''
        elif n.tag == W + 'tab':
            out += ' '
    return re.sub(r'\s+', ' ', out).strip()


def cell_lines(tc):
    return [t for t in (txt_of(p) for p in tc.findall(W + 'p')) if t]


def table_rows(tbl):
    rows = []
    for tr in tbl.findall(W + 'tr'):
        cells = []
        for tc in tr.findall(W + 'tc'):
            span = tc.find(W + 'tcPr/' + W + 'gridSpan')
            n = int(span.get(W + 'val')) if span is not None else 1
            cells.append((' '.join(cell_lines(tc)).strip(), n))
        rows.append(cells)
    return rows


def to_int(s):
    s = s.replace(',', '').replace('.', '').strip()
    return int(s) if s.isdigit() else 0


def to_days(s):
    s = s.strip().replace(',', '.')
    return float(s) if re.match(r'^\d+(\.\d+)?$', s) else None


def parse_band(label):
    """'1-5' / '876～1,175' / '≥ 426' / '>10700' -> (from, to)"""
    label = label.replace(' ', ' ').strip()
    m = NUM.match(label)
    if m:
        return to_int(m.group(1)), to_int(m.group(2))
    m = OPEN_UP.match(label)
    if m:
        return to_int(m.group(1)), 0
    if re.match(r'^\d+$', label.replace(',', '')):
        v = to_int(label)
        return v, v
    return None


def expand(row, ncols=None):
    """Give every grid column its own slot, so header and body line up."""
    slots = []
    for text, span in row:
        slots += [text] * span
    if ncols:
        slots += [''] * (ncols - len(slots))
    return slots


def duration_lines_from(rows):
    """Pull (band, complexity, audit kind, days) out of any of the annex tables.

    The annexes print their tables two-up (left half / right half) and split the
    columns by complexity or by the kind of audit, so the header is read column by
    column and every band takes the values that follow it.
    """
    ncols = max(sum(n for _t, n in r) for r in rows)
    grid = [expand(r, ncols) for r in rows]
    head = [g for g in grid if not any(parse_band(c) for c in g)]
    body = [g for g in grid if any(parse_band(c) for c in g)]
    if not body:
        return [], []
    labels, label_parts = [], []
    for col in range(ncols):
        parts = []
        for h in head:
            v = h[col].strip()
            if v and v not in parts:
                parts.append(v)
        label_parts.append(parts)
        labels.append(' / '.join(parts))
    # which columns hold the personnel band: the header says so
    # "Number of Man Days" also says "number of", so a band column is one that talks
    # about people and not about days
    # A band column is one whose own header cell names the people. The test runs per
    # header cell, because a table title such as "AUDIT MANDAYS CALCULATION" sits on
    # top of every column and would otherwise disqualify them all.
    def names_people(parts):
        return any(re.search(r'personnel|employee', p, re.I)
                   and not re.search(r'day|time|\bmd\b', p, re.I) for p in parts)
    band_cols = [c for c, parts in enumerate(label_parts) if names_people(parts)]
    if not band_cols:
        band_cols = [c for c in range(ncols) if any(parse_band(g[c]) for g in body)][:1]
    out, notes = [], []
    for g in body:
        for idx, col in enumerate(band_cols):
            band = parse_band(g[col])
            if not band:
                continue
            stop = band_cols[idx + 1] if idx + 1 < len(band_cols) else ncols
            for j in range(col + 1, stop):
                label = labels[j]
                low = label.lower()
                value = g[j].strip()
                if not value:
                    continue
                days = to_days(value)
                complexity = ''
                for lvl in ('high', 'medium', 'low', 'limited'):
                    if re.search(r'\b%s\b' % lvl, low):
                        complexity = lvl.capitalize()
                kind = 'certification'
                if 'surveillance' in low:
                    kind = 'surveillance'
                elif 'recert' in low:
                    kind = 'recertification'
                if days is None:
                    notes.append([g[col], value[:90]])
                    continue
                rec = {'label': g[col], 'from': band[0], 'to': band[1], 'days': days,
                       'complexity': complexity, 'kind': kind}
                if rec not in out:
                    out.append(rec)
    return out, notes


def is_duration_table(rows):
    head = ' '.join(c for r in rows[:5] for c, n in r).lower()
    return (('personnel' in head or 'employees' in head) and
            ('day' in head or 'md' in head or 'time' in head))


def is_risk_table(rows):
    head = ' '.join(c for r in rows[:2] for c, n in r).lower()
    return 'ea sector' in head or 'nace' in head or 'iaf/ ea code' in head or 'iaf/ea code' in head


def risk_lines_from(rows):
    """Read a risk / complexity table whatever order its columns are printed in."""
    header = [c.lower() for c, n in rows[0]]
    used = set()
    def col(*words):
        # "EA SECTOR" also contains "sector", so a column is claimed only once
        for i, h in enumerate(header):
            if i not in used and any(w in h for w in words):
                used.add(i)
                return i
        return None
    i_cat = col('risk categ', 'risk level', 'category', 'risk')
    i_ea = col('ea sector', 'ea code', 'iaf', 'ea ')
    i_nace = col('nace')
    i_sector = col('activity', 'business', 'sector')
    if i_cat is None or i_ea is None:
        i_cat, i_ea, i_nace, i_sector = 0, 1, 2, 3
    out, current = [], ''
    for r in rows[1:]:
        flat = [c for c, n in r]
        if len(flat) < 3:
            continue
        pick = lambda i: flat[i].strip() if i is not None and i < len(flat) else ''
        cat = pick(i_cat)
        if cat and cat.lower() in ('high', 'medium', 'low', 'limited'):
            current = cat
        out.append({'category': cat or current, 'ea': pick(i_ea), 'nace': pick(i_nace),
                    'sector': pick(i_sector)})
    return out


def factors_from(lines):
    """Split a factors cell into increase / decrease lists.

    A line starts a list only when it reads like a heading ("Indicative factors for
    increase of M/D", "Example factors permitting less audit time:"); a sentence that
    merely mentions a decrease ("Decrease of audit time cannot be more than 20%") is a
    factor in its own right and stays in the list.
    """
    inc, dec, mode, intro = [], [], None, []
    for t in lines:
        low = t.lower()
        heading = len(t) < 130 and (
            'factor' in low or re.search(r'(additional|less|more) audit time', low))
        if heading:
            if re.search(r'increase|additional', low):
                mode = 'increase'
                continue
            if re.search(r'decrease|less|reduction', low):
                mode = 'decrease'
                continue
        if mode == 'increase':
            inc.append(t)
        elif mode == 'decrease':
            dec.append(t)
        else:
            intro.append(t)
    return inc, dec, intro


def _parts(data):
    """The parts of the .docx we need, as text."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        out = {'headers': [], 'footers': []}
        out['document'] = zf.read('word/document.xml')
        out['rels'] = zf.read('word/_rels/document.xml.rels') if 'word/_rels/document.xml.rels' in names else b''
        for name in sorted(names):
            base = os.path.basename(name)
            if re.match(r'header\d+\.xml$', base):
                out['headers'].append(zf.read(name))
            elif re.match(r'footer\d+\.xml$', base):
                out['footers'].append(zf.read(name))
    return out


def parse_annex(data, filename=''):
    parts = _parts(data)
    root = ET.fromstring(parts['document'])
    body = root.find(W + 'body')
    tables = [c for c in body if c.tag == W + 'tbl']
    tbl = tables[0]
    rels = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                           parts['rels'].decode('utf-8', 'replace')))
    data = {'file': filename, 'sections': [], 'duration': [],
            'risk': [], 'factors': [], 'notes': []}
    # header / footer give the annex title and the revision
    for raw in parts['headers']:
        t = ' '.join(txt_of(p) for p in ET.fromstring(raw).iter(W + 'p'))
        if 'Annex' in t:
            data['header'] = re.sub(r'\s+', ' ', t).strip()
            m = re.search(r'(KFM-\S+,\s*Rev\.\S+)', t)
            if m:
                data['code'] = m.group(1)
    for raw in parts['footers']:
        t = ' '.join(txt_of(p) for p in ET.fromstring(raw).iter(W + 'p'))
        m = re.search(r'(Revision:\s*\S+)', t)
        if m:
            data['revision'] = m.group(1)
    seq = 0
    for tr in tbl.findall(W + 'tr'):
        tcs = tr.findall(W + 'tc')
        label = ' '.join(cell_lines(tcs[0])).strip() if tcs else ''
        if len(tcs) == 1:
            if 'Calculation of Audit Person Days' in label:
                data['title'] = label
                data['ms'] = label.split('for', 1)[-1].strip()
            continue
        content_tc = tcs[1]
        lines = cell_lines(content_tc)
        if label.lower().startswith('standard or certification'):
            data['standard'] = ' '.join(lines)
            continue
        seq += 10
        section = {'sequence': seq, 'name': label, 'body': '\n'.join(lines)}
        for nt in content_tc.findall(W + 'tbl'):
            rows = table_rows(nt)
            if is_duration_table(rows):
                lines_, notes = duration_lines_from(rows)
                # FSSC 22000 has no personnel bands at all - it is a formula with a
                # category table - so a handful of parsed rows means we misread it.
                if len({l['label'] for l in lines_}) < 6:
                    lines_, notes = [], []
                data['duration'] += lines_
                data['notes'] += notes
                if lines_:
                    section['body'] += '\n[Audit duration table: %d values]' % len(lines_)
                else:
                    section['body'] += '\n' + '\n'.join(
                        ' | '.join(c for c, n in r) for r in rows)
            elif is_risk_table(rows):
                data['risk'] += risk_lines_from(rows)
                section['body'] += '\n[Risk / complexity table: %d lines]' % len(risk_lines_from(rows))
            else:
                section['body'] += '\n' + '\n'.join(
                    ' | '.join(c for c, n in r) for r in rows)
        if 'factor' in label.lower():
            inc, dec, intro = factors_from(lines)
            for t in inc:
                data['factors'].append({'type': 'increase', 'name': t})
            for t in dec:
                data['factors'].append({'type': 'decrease', 'name': t})
            if inc or dec:
                section['body'] = '\n'.join(intro)
        # a figure inside the row
        for sh in content_tc.iter(V + 'shape'):
            im = sh.find(V + 'imagedata')
            if im is not None:
                section['image'] = rels.get(im.get(R + 'id'), '')
        # a stray character left in the Word file is not content
        body = section['body'].strip()
        if len(body.split('\n')[0].strip()) < 3 and '\n' in body:
            section['body'] = body.split('\n', 1)[1]
        elif len(body) < 3:
            section['body'] = ''
        if section['name'].strip() or section['body'].strip():
            data['sections'].append(section)
    # ISO 45001 keeps its complexity table as a second table of the document
    for extra in tables[1:]:
        rows = table_rows(extra)
        title = ' '.join(c for c, n in rows[0]).strip()
        if is_risk_table(rows) or is_risk_table(rows[1:]):
            head = rows[1:] if is_risk_table(rows[1:]) else rows
            data['risk'] += risk_lines_from(head)
            seq += 10
            data['sections'].append({'sequence': seq, 'name': title[:250] or 'Complexity categories',
                                     'body': '[Risk / complexity table: %d lines]' % len(data['risk'])})
        else:
            seq += 10
            data['sections'].append({'sequence': seq, 'name': title[:250] or 'Table',
                                     'body': '\n'.join(' | '.join(c for c, n in r) for r in rows[1:])})
    return data
