r"""Embed the weapon data and assets into docs/index.html.

    python scripts/build.py [path\to\mh3u-collection-tracker] [path\to\mhgu-weapon-trees]

Both default to sibling folders of this repo. Nothing is read from the game here: every weapon, stat,
recipe and upgrade link comes from the MH3U Collection Tracker's generated docs/data/ (which reads the
game -- see that repo's scripts/build_data.py), along with its rarity icons, coating icons, monster
icons, note icons, textures and font. The MHGU Weapon Trees page is only a fallback, for tracker data
that predates the game's own coating and note icons: its coating icons and its note glyph.

Only the block between the DATA:BEGIN / DATA:END markers in docs/index.html is rewritten, so the
app's code stays hand-edited in place.

MH3U has no weapon levels, so the trees are built from the tracker's parent/children links: every
weapon is a node, and a "line" is a run of upgrades -- the first upgrade the game lists for a weapon
carries its line on, any others start lines of their own that branch off it. Lines only decide how
the tree is laid out (one straight lane per line); nothing in the game depends on them.
"""
import base64, io, json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(HERE)
TRACKER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PARENT, 'mh3u-collection-tracker')
GU_TREES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PARENT, 'mhgu-weapon-trees')
TDOCS = os.path.join(TRACKER, 'docs')
INDEX = os.path.join(HERE, 'docs', 'index.html')

BEGIN = '<!-- DATA:BEGIN (written by scripts/build.py; do not edit by hand) -->'
END = '<!-- DATA:END -->'

# Theme names -> the icon file each one shows (the tracker's THEMES table; same 31 hexes family-wide).
THEME_ICONS = {
    'Volvidon': 'Volvidon', 'Rathalos': 'Rathalos', 'R. Duramboros': 'Rust Duramboros',
    'Agnaktor': 'Agnaktor', 'Uragaan': 'Uragaan', 'G. Rathian': 'Gold Rathian',
    'G. Nargacuga': 'Green Nargacuga', 'G. Plesioth': 'Green Plesioth', 'Deviljho': 'Deviljho',
    'Rathian': 'Rathian', 'S. Uragaan': 'Steel Uragaan', 'Zinogre': 'Zinogre',
    'A. Lagiacrus': 'Abyssal Lagiacrus', 'G. Agnaktor': 'Glacial Agnaktor', 'Nargacuga': 'Nargacuga',
    'Plesioth': 'Plesioth', 'Brachydios': 'Brachydios', 'Lagiacrus': 'Lagiacrus',
    'Great Wroggi': 'Great Wroggi', 'Great Jaggi': 'Great Jaggi', 'H. Jhen Mohran': 'Hallowed Jhen Mohran',
    'P. Ludroth': 'Purple Ludroth', 'P. Rathian': 'Pink Rathian', 'Qurupeco': 'Qurupeco',
    'Duramboros': 'Duramboros', 'Diablos': 'Diablos', 'Barroth': 'Barroth', 'Bullfango': 'Bullfango',
    'S. Rathalos': 'Silver Rathalos', 'Barioth': 'Barioth', 'Forbidden': 'Question Mark',
}
# Hunting Horn notes in older tracker data: its names and by-eye colours (its old styles.css .note-*),
# drawn with the MHGU app's glyph. Newer data carries the game's own note icons and colours instead.
# (The names for codes 3-8 in that older data are wrong -- fitted to Kiranico, which permutes them.)
NOTE_COLOURS = {'White': '#f2f2f2', 'Purple': '#a05ad0', 'Blue': '#4a7ff0', 'Red': '#e04848',
                'Yellow': '#e8d23a', 'Orange': '#ef8f2e', 'Green': '#4caf50', 'Sky': '#7fd6f5'}
# Older tracker data names coatings only; those take the MHGU app's coating icon (by colour), and Paint,
# which has none there, stays text. Newer data carries the game's own bottle icon and colour instead.
COATING_ICON = {'Power': 'Red', 'C-Range': 'White', 'Poison': 'Purple', 'Paralysis': 'Yellow',
                'Sleep': 'Light_Blue', 'Exhaust': 'Blue'}
GUNNER = {'light_bowgun', 'heavy_bowgun', 'bow'}


def data_uri(path, mime):
    with open(path, 'rb') as fh:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(fh.read()).decode())


def png_uri(img):
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def load_catalog():
    s = open(os.path.join(TDOCS, 'data', 'catalog.js'), encoding='utf-8').read()
    return json.loads(s[s.index('=') + 1:].strip().rstrip(';'))


def gu_blobs():
    """The window.* assignments embedded in the MHGU Weapon Trees page, as dicts."""
    line = next(l for l in open(os.path.join(GU_TREES, 'docs', 'index.html'), encoding='utf-8')
                if l.startswith('<script>window.THEME_ASSETS='))
    out = {}
    for part in line.strip().split('</script><script>'):
        part = part.replace('<script>', '').replace('</script>', '')
        name, body = part.split('=', 1)
        if name in ('window.COATS', 'window.NOTE_ICONS'):
            out[name[7:]] = json.loads(body.rstrip(';'))
    return out


class Strings:
    """Per-class string table, so repeated labels are stored once (the MHGU app's `str`)."""
    def __init__(self):
        self.list, self.ix = [], {}

    def __call__(self, s):
        if s not in self.ix:
            self.ix[s] = len(self.list)
            self.list.append(s)
        return self.ix[s]


AMMO_LV = re.compile(r'^(.*?)\s+Lv(\d+)$')


def extra(cls, st, S):
    """Class-specific payload (L[7]); the page's unpack() reads it back."""
    if cls == 'switch_axe':
        return [S(re.sub(r'\s*Phial$', '', st['phial']))]
    if cls == 'hunting_horn':
        # Newer tracker data: notes [label, icon, colour] and songs [[note indexes into those three], effect].
        # Plain-string notes (no songs) are the older shape.
        notes = [n[0] if isinstance(n, list) else n for n in st['notes']]
        return [[S(n) for n in notes], [[seq, S(effect)] for seq, effect in st.get('songs', [])]]
    if cls == 'gunlance':
        return [S(st['shell'])]
    if cls == 'bow':
        # The tracker's newer shape: charges [name, loadUp], coatings [label, icon, colour].
        # Plain strings are the older shape, still read so an older tracker checkout builds.
        charges = [c if isinstance(c, list) else [c, 0] for c in st['charges']]
        return [S(st['arc']) if st.get('arc') else -1,
                [[S(re.sub(r' L(\d)$', r' Lv\1', name)), load_up] for name, load_up in charges],
                [S(c[0] if isinstance(c, list) else c) for c in st['coatings']]]
    if cls in ('light_bowgun', 'heavy_bowgun'):
        groups, order = {}, []
        for name, cap in st['ammo']:          # in the game's item order: Normal S Lv1, Lv2, ...
            m = AMMO_LV.match(name)
            base, lv = (m.group(1), int(m.group(2))) if m else (name, 1)
            if base not in groups:
                groups[base] = {}
                order.append(base)
            groups[base][lv] = cap
        ammo = [[S(b), [groups[b].get(lv, 0) for lv in range(1, max(groups[b]) + 1)]] for b in order]
        return [S(st['reload']), S(st['recoil']), S(st['deviation']), ammo]
    return []


def build_class(cls, cat):
    stats = json.load(open(os.path.join(TDOCS, 'data', 'stats', cls + '.json'), encoding='utf-8'))['byId']
    mats = json.load(open(os.path.join(TDOCS, 'data', 'materials', cls + '.json'), encoding='utf-8'))
    S = Strings()
    names = {e[0]: e[1] for e in cat['entries']}
    tree_order = {e[0]: e[4] for e in cat['entries']}
    kids = {i: [c for c in stats[str(i)]['children'] if c in names] for i in names}
    # The tracker gives what the game DISPLAYS. The weapon record stores the true values, and the
    # status screen shows attack as true * the class multiplier (u32 at 0xba2bf8 / 100, floored; READ
    # 0x57bf40) and element / status as true * 10. Both invert exactly: with a multiplier of at least 1
    # only one integer floors to a given display, the smallest one at or above display / multiplier.
    # Checked against the records themselves (record +0xa melee / +4 gunner; element +0xf/+0x11/+0x13,
    # bow +0x15) for every weapon: 1,395 attacks and 1,132 element and status values, no mismatch.
    mult100 = round(cat['mult'] * 100)
    true_raw = lambda shown: -(-100 * shown // mult100)

    def level(i):
        st = stats[str(i)]
        rec = mats['create'].get(str(i), {})
        sharp = st.get('sh') if cls not in GUNNER else None
        return [i, names[i], st['atk'], st['aff'], st['def'], st['slots'],
                [[e[0], e[1], e[2], e[1] // 10] for e in st.get('ele', [])],
                extra(cls, st, S),
                rec['f'][2] if 'f' in rec else None,
                sharp, st['rar'],
                rec.get('d'),
                true_raw(st['atk'])]

    # Lines, depth first in the tracker's tree order so related lines sit together.
    trees = []

    def line_from(start, parent):
        t = {'i': len(trees) + 1, 'n': names[start], 'r': stats[str(start)]['rar'], 'p': parent or 0, 'L': []}
        trees.append(t)
        branches, i = [], start
        while True:
            t['L'].append(level(i))
            ks = kids[i]
            branches += [(i, k) for k in ks[1:]]
            if not ks:
                break
            i = ks[0]
        for at, k in branches:
            line_from(k, at)

    roots = sorted((i for i in names if stats[str(i)]['parent'] not in names), key=lambda i: tree_order[i])
    for r in roots:
        line_from(r, None)
    placed = sum(len(t['L']) for t in trees)
    assert placed == len(names), (cls, placed, len(names))
    return {'label': cat['label'], 'mats': mats['mats'], 'str': S.list, 'trees': trees}


def main():
    from PIL import Image
    cat = load_catalog()
    gu = gu_blobs()

    wdata = {cls: build_class(cls, c) for cls, c in cat['weapons'].items()}

    icons = {}
    for cls in cat['weapons']:
        icons[cls] = {}
        for r in range(1, 11):
            img = Image.open(os.path.join(TDOCS, 'assets', 'icons', 'icon_%s_r%d.png' % (cls, r))).convert('RGBA')
            # 22 px game cells, already doubled by the tracker; doubled again so they hold their pixels
            # at the 80 px the map draws them rather than being smoothed by the browser.
            icons[cls][r] = png_uri(img.resize((88, 88), Image.NEAREST))

    monsters = {name: data_uri(os.path.join(TDOCS, 'assets', 'MonsterIcons',
                                            'MH3U-%s_Icon.png' % icon.replace(' ', '_')), 'image/png')
                for name, icon in THEME_ICONS.items()}

    theme = {
        'font': data_uri(os.path.join(TDOCS, 'fonts', 'mhfu_font.ttf'), 'font/ttf'),
        'rocky': data_uri(os.path.join(TDOCS, 'assets', 'rockyTextureDark2.png'), 'image/png'),
        'banner': data_uri(os.path.join(TDOCS, 'assets', 'banner-background.png'), 'image/png'),
        'title': data_uri(os.path.join(TDOCS, 'assets', 'titlebar-background.png'), 'image/png'),
    }

    game_coats = {}
    for st in json.load(open(os.path.join(TDOCS, 'data', 'stats', 'bow.json'), encoding='utf-8'))['byId'].values():
        for c in st['coatings']:
            if isinstance(c, list):
                game_coats[c[0]] = c
    if game_coats:
        # The game's own coating bottles (44 px, doubled from its 22 px cells by the tracker).
        coats = {'map': {label: icon for label, icon, _ in game_coats.values()},
                 'col': {icon: {'c': col, 'i': data_uri(os.path.join(TDOCS, 'assets', 'coatings', icon + '.png'),
                                                         'image/png')}
                         for _, icon, col in game_coats.values()}}
    else:
        coats = {'map': COATING_ICON, 'col': {k: gu['COATS']['col'][k] for k in set(COATING_ICON.values())}}

    # Note label -> {i: icon, c: colour}.
    game_notes = {}
    for st in json.load(open(os.path.join(TDOCS, 'data', 'stats', 'hunting_horn.json'), encoding='utf-8'))['byId'].values():
        for n in st['notes']:
            if isinstance(n, list):
                game_notes[n[0]] = n
    notes = {}
    if game_notes:
        # The game's own note glyph per note, tinted by the HUD's own colour table (the tracker reads both).
        for label, icon, col in game_notes.values():
            notes[label] = {'c': col, 'i': data_uri(os.path.join(TDOCS, 'assets', 'notes', icon + '.png'), 'image/png')}
    else:
        # Older tracker data: the MHGU app's eighth-note glyph, filled with the tracker's old colours.
        # White keeps its outline.
        white = base64.b64decode(gu['NOTE_ICONS']['White'].split(',', 1)[1]).decode()
        for name, col in NOTE_COLOURS.items():
            svg = white.replace('#F0F4F0', col).replace('White eighth note', name + ' eighth note')
            if name != 'White':
                svg = re.sub(r' stroke="#2A2A2A" stroke-width="[\d.]+"', '', svg)
            notes[name] = {'c': col, 'i': 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()}

    blobs = [('THEME_ASSETS', theme), ('MONSTER_ICONS', monsters), ('ICONS', icons), ('COATS', coats),
             ('NOTE_ICONS', notes), ('RARITY', cat['rarityColors']), ('WDATA', wdata)]
    block = ''.join('<script>window.%s=%s;</script>' % (k, json.dumps(v, ensure_ascii=False, separators=(',', ':')))
                    for k, v in blobs)

    html = open(INDEX, encoding='utf-8').read()
    a, b = html.index(BEGIN) + len(BEGIN), html.index(END)
    html = html[:a] + '\n' + block + '\n' + html[b:]
    with open(INDEX, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(html)

    for cls, d in wdata.items():
        print('%-17s %4d weapons  %3d lines  %3d trees' % (
            cls, sum(len(t['L']) for t in d['trees']), len(d['trees']), sum(1 for t in d['trees'] if not t['p'])))
    print('index.html', os.path.getsize(INDEX), 'bytes')


if __name__ == '__main__':
    main()
