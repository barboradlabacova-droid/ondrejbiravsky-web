#!/usr/bin/env python3
"""Sestaví web ondrejbiravsky.cz z obsahu v content/ do složky dist/.
Spouští ho Netlify při každé změně (i z administrace /admin). Lokálně: python3 build.py"""
import json, os, re, shutil, glob, html
import yaml, markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(ROOT, 'content')
DIST = os.path.join(ROOT, 'dist')
SITE = 'https://ondrejbiravsky.cz'
esc = html.escape

# ---------- načtení obsahu ----------
def jload(name): return json.load(open(os.path.join(C, name), encoding='utf-8'))
def front(path):
    s = open(path, encoding='utf-8').read()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', s, re.S)
    return (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, s)
def md(text): return markdown.markdown(text or '', extensions=['tables', 'sane_lists'])

S = jload('nastaveni.json')
REFS = [r for r in jload('reference.json').get('polozky', []) if (r.get('text') or '').strip()]
SOLD = jload('prodane.json').get('polozky', [])
IG = json.loads(open(os.path.join(C, 'igluu.json'), encoding='utf-8').read().replace('\uf0b7', '•').replace('\\uf0b7', '•'))  # odrážky z Wordu → •
OMNE_FM, OMNE_MD = front(os.path.join(C, 'o-mne.md'))
ARTS = []
for f in glob.glob(os.path.join(C, 'clanky', '*.md')):
    fm, body = front(f)
    if fm.get('skryt'): continue
    fm['slug'] = os.path.splitext(os.path.basename(f))[0]
    fm['body'] = body
    fm['date'] = str(fm.get('date') or '')[:10]
    ARTS.append(fm)
ARTS.sort(key=lambda a: a['date'], reverse=True)

TEL = S['telefon']; TEL_HREF = '+420' + re.sub(r'\D', '', TEL)[-9:]
TOK = {'TEL': TEL, 'TEL_HREF': TEL_HREF, 'EMAIL': S['email'], 'WA': S.get('whatsapp', '420' + re.sub(r'\D', '', TEL)[-9:])}
def tok(s):
    for k, v in TOK.items(): s = s.replace('{{' + k + '}}', v)
    return s
def cz_date(iso):
    try:
        y, m, d = iso.split('-'); return f'{int(d)}. {int(m)}. {y}'
    except Exception: return ''

def slug(t):
    t = t.lower().translate(str.maketrans('áčďéěíňóřšťúůýž', 'acdeeinorstuuyz'))
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

# ---------- příprava výstupu ----------
if os.path.exists(DIST): shutil.rmtree(DIST)
shutil.copytree(os.path.join(ROOT, 'static'), DIST)
sitemap = []

# ---------- nabídka z Igluu ----------
IMG_REMOTE = 'https://live-file-api.igluu.cz/file/{}?isPublic=true'
IGLUU_DIR = os.path.join(ROOT, 'static', 'assets', 'img', 'igluu')
def igimg(fid):
    # Fotky z Igluu stahuje GitHub Action do static/assets/img/igluu/ (trvalá kopie).
    # Dokud tam fotka není, načítá se přímo z Igluu.
    return f'/assets/img/igluu/{fid}.jpg' if os.path.exists(os.path.join(IGLUU_DIR, f'{fid}.jpg')) else IMG_REMOTE.format(fid)
class _Img:
    format = staticmethod(igimg)
IMG = _Img()
def kind2(o):
    k = o['params'].get('kategorie', '')
    if o['deal'] == 'Pronájem': return 'Pronájem'
    if 'Byt' in k: return 'Byty'
    if 'dom' in k.lower() or 'Chat' in k: return 'Domy a chaty'
    return 'Pozemky'
def price_of(o):
    parts = [p.strip() for p in o['price'].split('|') if p.strip()]
    v = next((p for p in parts if 'Kč' in p), '')
    note = ' '.join(p for p in parts if 'Kč' not in p)
    if o['deal'] == 'Pronájem' and v and '/m' not in v: v += '/měs.'
    return v, note
def short_facts(o):
    p = o['params']; f = []
    for k in ('velikost', 'plocha užitná', 'plocha pozemku'):
        if p.get(k): f.append(p[k] if k == 'velikost' else (('pozemek ' if k == 'plocha pozemku' else '') + p[k]))
    return f
def town(o):
    parts = [x.strip() for x in o['addr'].split(',')]
    return re.sub(r'^\d{3}\s?\d{2}\s', '', parts[-1]) if parts else o['addr']
LIST = []
for o in IG['active']:
    o['slug'] = slug(o['title'])[:70].strip('-') + '-' + o['id']
    o['kind'] = kind2(o); o['pv'], o['pnote'] = price_of(o)
    o['status'] = 'Rezervováno' if (o.get('status') or '').lower().startswith('rezerv') else ''
    LIST.append(o)
LIST.sort(key=lambda o: (o['status'] != '', o['kind'] == 'Pozemky'))
def card(o):
    img = IMG.format(o['imgs'][0]) if o['imgs'] else '/assets/img/og.jpg'
    price = o['pv'] or o['status'] or 'Cena na dotaz'
    return f'<li class="lst rv" data-k="{o["kind"]}"><a href="/nabidka/{o["slug"]}" data-ev="click_listing"><figure><img src="{img}" alt="{esc(o["title"])}" loading="lazy" width="900" height="600"><span class="tag">{esc(o["status"] or o["deal"])}</span></figure><div class="meta"><span class="lbl">{esc(o["params"].get("kategorie",""))} · {esc(town(o))}</span><h3 class="h3">{esc(o["title"])}</h3><div class="row"><span>{esc(" · ".join(short_facts(o)[:2]))}</span><b>{esc(price)}</b></div></div></a></li>'

# ---------- úvodní stránka ----------
idx = open(os.path.join(ROOT, 'templates', 'index.html'), encoding='utf-8').read()
stats = ''.join(f'<div class="stat"><b>{esc(c["hodnota"])}' + (f' <small>{esc(c["jednotka"])}</small>' if c.get('jednotka') else '') + f'</b><span>{esc(c["popis"])}</span></div>' for c in S['cisla'])
stats += '<div class="stat"><b class="word">MAKLÉŘ MĚSÍCE</b><span>CENTURY 21, kategorie Master</span></div>'
home_arts = [a for a in ARTS if a.get('na_uvodu')][:3] or ARTS[:3]
posts = ''
for a in home_arts:
    big = esc(str(a.get('velke_cislo') or ''))
    big = re.sub(r'(\d)\s(tis\.|mil\.)', r'\1 <small>\2</small>', big)
    cls = 'big txt' if big and not re.search(r'\d', big) else 'big'
    big = big.replace(' × ', '<br>× ') if 'txt' in cls else big
    txt = f'<p>{esc(a["uvod_text"])}</p>' if a.get('uvod_text') else '<span class="more">Číst článek →</span>'
    posts += f'<a class="post rv" href="/clanek/{a["slug"]}">' + (f'<span class="{cls}">{big}</span>' if big else '') + f'<h3 class="h3">{esc(a.get("uvod_nadpis") or a["title"])}</h3>{txt}</a>'
hr = [r for r in REFS if r.get('na_uvodu')]
txt_refs = [r for r in hr if not r.get('video')][:2]
vid = next((r for r in hr if r.get('video')), None)
refs_html = ''.join(f'<figure class="ref rv"><span class="q" aria-hidden="true">“</span><blockquote>{esc(r.get("kratka_verze") or r["text"])}</blockquote><figcaption>{esc(r["jmeno"].replace(", ", " · ", 1))}</figcaption></figure>' for r in txt_refs)
if vid:
    refs_html += f'<a class="video rv" href="{esc(vid["video"])}" target="_blank" rel="noopener"><span class="lbl">Videoreference · {esc(vid["jmeno"])}</span><blockquote>„{esc(vid.get("kratka_verze") or vid["text"])}“</blockquote><span class="play"><i aria-hidden="true"></i>Přehrát videoreferenci</span></a>'
soc = ''.join(f'<a href="{esc(S[k])}" target="_blank" rel="noopener">{n}</a>' for k, n in [('facebook', 'Facebook'), ('youtube', 'YouTube'), ('linkedin', 'LinkedIn'), ('x', 'X')] if S.get(k))
rep = {'STATS': stats, 'LISTINGS': ''.join(card(o) for o in LIST[:6]), 'NABIDKA_POCET': str(len(LIST)), 'POSTS': posts, 'REFS': refs_html,
       'GOOGLE': esc(S['google_hodnoceni']), 'GOOGLE_POCET': esc(S['google_pocet']), 'REF_POCET': str(len(REFS)), 'NEJVETSI': esc(S['nejvetsi_obchod']),
       'TYM': ''.join(f'<li>{esc(t)}</li>' for t in S.get('tym', [])), 'SOCIAL': soc, 'KANCELAR_BR': '<br>'.join(esc(x.strip()) for x in S['kancelar'].split(',', 1))}
for k, v in rep.items(): idx = idx.replace('{{' + k + '}}', v)
idx = tok(idx)
open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8').write(idx)
sitemap.append('/')

# ---------- šablona podstránek ----------
HEAD_TPL = idx.split('<script type="application/ld+json">')[0]
HEADER = re.search(r'(<a class="skip".*?</header>)', idx, re.S).group(1).replace('href="#', 'href="/#')
FOOTER = re.search(r'(<footer.*?</footer>)', idx, re.S).group(1)
MBAR = re.search(r'(<nav class="mbar".*?</nav>)', idx, re.S).group(1).replace('href="#kontakt"', 'href="/#kontakt"')

def page(path, title, desc, body, og_img=None, noindex=False, extra_head='', main_class=''):
    h = HEAD_TPL
    t_short = title[:-len(' | Ondřej Biravský')] if len(title) > 65 and title.endswith(' | Ondřej Biravský') else title
    h = re.sub(r'<title>.*?</title>', f'<title>{esc(t_short)}</title>', h)
    h = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{esc(desc)}">', h)
    url = SITE + path
    h = h.replace(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{url}">')
    h = re.sub(r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{url}">', h)
    h = re.sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{esc(title)}">', h)
    h = re.sub(r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{esc(desc)}">', h)
    if og_img: h = re.sub(r'<meta property="og:image" content=".*?">', f'<meta property="og:image" content="{SITE if og_img.startswith("/") else ""}{og_img}">', h)
    if noindex: h = h.replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"')
    h += extra_head
    mc = f' class="{main_class}"' if main_class else ''
    doc = h + '</head>\n<body>\n' + HEADER + f'\n<main id="main"{mc}>\n' + tok(body) + '\n</main>\n' + FOOTER + '\n' + MBAR + '\n<script src="/assets/site.js" defer></script>\n</body>\n</html>\n'
    fp = os.path.join(DIST, 'index.html') if path == '/' else os.path.join(DIST, path.strip('/') + '.html')
    if path in ('/nabidka',): fp = os.path.join(DIST, 'nabidka', 'index.html')
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w', encoding='utf-8').write(doc)
    if not noindex: sitemap.append(path)

CTA = '''<section class="dark cta-band"><div class="wrap"><h2 class="h2">Pojďme na kávu. <span class="gold">Rozebereme Váš případ.</span></h2><div class="actions"><a class="btn btn-gold" href="/odhad">Domluvit konzultaci zdarma</a><a class="ulink" href="tel:{{TEL_HREF}}" data-ev="click_phone">{{TEL}}</a></div></div></section>'''
def phead(crumb, label, h1, lead=''):
    c = ' / '.join(f'<a href="{u}">{esc(t)}</a>' if u else esc(t) for t, u in crumb)
    return f'<div class="wrap"><div class="phead"><span class="crumb">{c}</span><span class="lbl">{label}</span><h1 class="h1">{h1}</h1>' + (f'<p class="lead">{lead}</p>' if lead else '') + '</div></div>'

# ---------- statické stránky (šablony) ----------
for f in glob.glob(os.path.join(ROOT, 'templates', 'pages', '*.html')):
    name = os.path.splitext(os.path.basename(f))[0]
    s = open(f, encoding='utf-8').read()
    meta = dict(re.findall(r'<!--(title|desc|noindex|mainclass):(.*?)-->', s))
    lds = re.findall(r'<!--ld:(.*?)-->\n', s, re.S)
    body = re.sub(r'<!--(title|desc|noindex|mainclass|ld):.*?-->\n', '', s, flags=re.S)
    page('/' + name, html.unescape(meta['title']), html.unescape(meta['desc']), body, noindex=meta.get('noindex') == '1', extra_head=''.join(x + '\n' for x in lds), main_class=meta.get('mainclass', '').replace('class="', '').rstrip('"'))
# 404 musí být v kořeni jako 404.html (už je), dekujeme apod. taky

# ---------- články ----------
for a in ARTS:
    body = md(a['body'])
    body = re.sub(r'<blockquote>\s*<p>(.*?)</p>\s*</blockquote>', r'<p class="pull">\1</p>', body, flags=re.S)
    body = re.sub(r'<table>', '<div class="tbl" tabindex="0" role="region" aria-label="Tabulka">\n<table>', body).replace('</table>', '</table></div>')
    body = re.sub(r'<th(\s[^>]*)?>\s*</th>', r'<td\1></td>', body)
    img = a.get('image') or ''
    hero = f'<img class="art-hero" src="{esc(img)}" alt="">' if img else ''
    d = cz_date(a['date'])
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a['title'], "datePublished": a['date'], "author": {"@type": "Person", "name": "Ondřej Biravský"}, "image": (SITE + img) if img.startswith('/') else img, "mainEntityOfPage": SITE + '/clanek/' + a['slug']}
    t = a['title']
    content = phead([('Úvod', '/'), ('Články', '/clanky'), (t[:40] + ('…' if len(t) > 40 else ''), None)], 'Data z trhu' + (f' · {d}' if d else ''), esc(t)) + \
        f'<div class="wrap">{hero}<article class="prose">{body}</article>' + \
        '<aside class="author"><img src="/assets/img/ondrej-avatar.jpg" alt="Ondřej Biravský" width="88" height="88" loading="lazy"><p><b>Ondřej Biravský</b>Realitní makléř CENTURY 21 Dream v Brně, autor e-booku a lektor Akademie CENTURY 21. „Snažím se o kultivaci realitního trhu a férové jednání.“</p></aside></div>' + CTA
    page('/clanek/' + a['slug'], f'{t} | Ondřej Biravský', a.get('perex') or t, content, og_img=img or None, extra_head=f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n')
cards = ''.join(f'''<li class="acard rv"><a href="/clanek/{a['slug']}">''' + (f'<img src="{esc(a["image"])}" alt="" loading="lazy">' if a.get('image') else '') + f'''<span class="art-meta">{cz_date(a['date'])}</span><h2 class="h3">{esc(a['title'])}</h2><p>{esc(a.get('perex') or '')}</p></a></li>''' for a in ARTS)
page('/clanky', 'Články a data z trhu | Ondřej Biravský', 'Analýzy realitního trhu v Brně a na jižní Moravě a praktické rady pro prodávající.',
     phead([('Úvod', '/'), ('Články', None)], 'Data z trhu', 'Rozhoduji podle čísel, <span class="gold-d">ne podle pocitu.</span>', f'Analýzy trhu a praktické rady pro všechny, kdo prodávají, kupují nebo investují. Další komentáře najdete na mém <a class="ulink" href="{esc(S.get("youtube",""))}" target="_blank" rel="noopener">YouTube kanálu</a>.') +
     f'<div class="wrap" style="padding-bottom:var(--sec)"><ul class="alist">{cards}</ul></div>' + CTA)

# ---------- reference ----------
fig = ''.join(f'<figure><blockquote>{esc(r["text"])}</blockquote><figcaption>{esc(r["jmeno"])}' + (f' · <a class="vid" href="{esc(r["video"])}" target="_blank" rel="noopener">videoreference</a>' if r.get('video') else '') + '</figcaption></figure>' for r in REFS)
page('/reference', 'Reference klientů | Ondřej Biravský', f'{len(REFS)} referencí klientů Ondřeje Biravského, realitního makléře v Brně. Hodnocení {S["google_hodnoceni"]} na Googlu.',
     phead([('Úvod', '/'), ('Reference', None)], f'Reference · {esc(S["google_hodnoceni"])} na Googlu ({esc(S["google_pocet"])} hodnocení)', 'Spokojení? <span class="gold-d">Spíš nadšení.</span>', f'{len(REFS)} referencí od klientů, kteří se mnou prodávali, kupovali nebo pronajímali.') +
     f'<div class="wrap" style="padding-bottom:var(--sec)"><div class="reflist">{fig}</div></div>' + CTA)

# ---------- prodané ----------
rl = []
for o in IG['realized']:
    k = o['params'].get('kategorie', '')
    kk = 'Byty' if 'Byt' in k else ('Domy' if ('dom' in k.lower() or 'Chat' in k) else ('Pozemky' if 'ozem' in k else 'Komerce a ostatní'))
    st = 'Pronajato' if o['status'].lower().startswith('pronaj') else 'Prodáno'
    img = f'<img src="{IMG.format(o["imgs"][0])}" alt="{esc(o["title"])}" loading="lazy" width="800" height="640">' if o['imgs'] else ''
    fx = ' · '.join(x for x in [o['params'].get('velikost'), o['params'].get('plocha užitná') or o['params'].get('plocha pozemku')] if x)
    rl.append(f'<li class="rv" data-k="{kk}">{img}<div><span class="badge">{st}</span><h2>{esc(o["title"].rstrip(", "))}</h2><p>{esc(o["addr"])}' + (f' · {esc(fx)}' if fx else '') + '</p></div></li>')
for o in SOLD:
    img = f'<img src="{esc(o["foto"])}" alt="{esc(o["nazev"])}" loading="lazy" width="800" height="640">' if o.get('foto') else ''
    rl.append(f'<li class="rv" data-k="{esc(o.get("typ") or "Komerce a ostatní")}">{img}<div><span class="badge">{esc(o.get("stav") or "Prodáno")}</span><h2>{esc(o["nazev"])}</h2><p>{esc(o.get("popis") or "")}</p></div></li>')
n_sold = len(rl)
filters = '<div class="filters" role="group" aria-label="Filtr typu">' + ''.join(f'<button type="button" data-f="{f}" aria-pressed="{"true" if f=="Vše" else "false"}">{f}</button>' for f in ['Vše', 'Byty', 'Domy', 'Pozemky', 'Komerce a ostatní']) + '</div>'
page('/prodane-nemovitosti', 'Prodané nemovitosti | Ondřej Biravský', f'{n_sold} prodaných a pronajatých nemovitostí v Brně, na jižní Moravě i v Praze.',
     phead([('Úvod', '/'), ('Prodané nemovitosti', None)], 'Archiv · od roku 2018 po dnešek', 'Výsledky, <span class="gold-d">ne sliby.</span>', f'Výběr {n_sold} nemovitostí, které jsem prodal nebo pronajal, od těch nejnovějších.') +
     f'<div class="wrap" style="padding-bottom:var(--sec)">{filters}<ul class="sold" id="sold">{"".join(rl)}</ul></div>' + CTA)

# ---------- o mně ----------
aw = ''.join(f'<li><span>{esc(a["kategorie"])} · {esc(str(a["mesic"]))} {esc(str(a["rok"]))}</span><b>{esc(str(a["misto"]))}. místo v ČR</b></li>' for a in S.get('oceneni', []))
facts = ''.join(f'<div><b>{esc(c["hodnota"])}' + (f' {esc(c["jednotka"])}' if c.get('jednotka') else '') + f'</b><span>{esc(c["popis"])}</span></div>' for c in S['cisla'])
facts = facts.replace('</div>', '</div>', 1)
omne = md(OMNE_MD)
omne = re.sub(r'<blockquote>\s*<p>(.*?)</p>\s*</blockquote>', r'<p class="pull">\1</p>', omne, flags=re.S)
nad = esc(OMNE_FM.get('nadpis') or 'Méně zakázek, víc pozornosti pro každou z nich.')
nad = re.sub(r'^(.*?,)\s*(.*)$', r'\1 <span class="gold-d">\2</span>', nad)
page('/o-mne', 'O mně | Ondřej Biravský, realitní makléř Brno', 'Ondřej Biravský, realitní makléř CENTURY 21 Dream v Brně od roku 2017. Makléř měsíce, lektor Akademie CENTURY 21.',
     phead([('Úvod', '/'), ('O mně', None)], 'Dobrý den, jsem Ondřej.', nad) +
     f'''<div class="wrap" style="padding-bottom:var(--sec)"><div class="two"><div style="display:flex;flex-direction:column;gap:20px"><img class="portrait" src="/assets/img/ondrej.jpg" alt="Ondřej Biravský" width="1000" height="1250"><span class="lbl">Čeština · English · Deutsch</span></div><div class="prose">{omne}</div></div></div>
<section class="dark"><div class="wrap" style="padding-block:0"><div class="facts">{facts}<div><b>{esc(S["nejvetsi_obchod"])}</b><span>největší transakce</span></div></div></div></section>
<section class="sec"><div class="wrap two"><div><span class="lbl">Ocenění CENTURY 21 Česká republika</span><h2 class="h2" style="margin-top:16px">Makléř měsíce</h2></div><ul class="awards">{aw}</ul></div></section>''' + CTA)

# ---------- nabídka ----------
flt = '<div class="filters" role="group" aria-label="Filtr typu">' + ''.join(f'<button type="button" data-f="{f}" aria-pressed="{"true" if f=="Vše" else "false"}">{f}</button>' for f in ['Vše', 'Byty', 'Domy a chaty', 'Pozemky', 'Pronájem']) + '</div>'
watch = open(os.path.join(ROOT, 'templates', 'hlidani.html'), encoding='utf-8').read()
page('/nabidka', 'Aktuální nabídka nemovitostí | Ondřej Biravský', f'{len(LIST)} nemovitostí v nabídce: byty, domy, chaty a pozemky v Brně, na jižní Moravě i v Praze.',
     phead([('Úvod', '/'), ('Nabídka', None)], f'Aktuální nabídka · {len(LIST)} nemovitostí', 'Co právě <span class="gold-d">prodávám.</span>', 'Byty, domy, chaty i pozemky. Hledáte něco, co tu není? Napište mi, co sháníte, a ozvu se, jakmile se objeví.') +
     f'<div class="wrap" style="padding-bottom:var(--sec)"><h2 class="sr">Seznam nemovitostí</h2>{flt}<ul class="listings" id="sold">{"".join(card(o) for o in LIST)}</ul></div>' + watch + CTA)
SKIP = {'lokalita', 'kraj'}
for o in LIST:
    gal = ''.join(f'<li><button type="button" data-full="{IMG.format(i)}" aria-label="Zvětšit fotku {n}"><img src="{IMG.format(i)}" alt="" loading="lazy" width="400" height="300"></button></li>' for n, i in enumerate(o['imgs'], 1))
    more = f'<button type="button" class="btn btn-line gal-more">Zobrazit všech {len(o["imgs"])} fotek</button>' if len(o['imgs']) > 9 else ''
    desc = ''.join(f'<p>{esc(p.strip())}</p>' for p in re.split(r'\n', o['desc']) if p.strip())
    rows = ''.join(f'<tr><th>{esc(k.capitalize())}</th><td>{esc(v)}</td></tr>' for k, v in o['params'].items() if k not in SKIP and v)
    fx = ''.join(f'<span>{esc(f)}</span>' for f in short_facts(o))
    main = IMG.format(o['imgs'][0]) if o['imgs'] else '/assets/img/og.jpg'
    price = o['pv'] or o['status'] or 'Cena na dotaz'
    note = ((o['pnote'] + ' ') if o['pnote'] else '') + ('Nemovitost je rezervovaná, ale rád Vám nabídnu podobnou.' if o['status'] else '')
    body = phead([('Úvod', '/'), ('Nabídka', '/nabidka'), (o['title'][:40] + ('…' if len(o['title']) > 40 else ''), None)], f'{o["deal"]} · {esc(o["params"].get("kategorie",""))} · {esc(o["addr"])}', esc(o['title'])) + f'''<div class="wrap" style="padding-bottom:var(--sec)"><div class="pd"><div class="pd-main"><img src="{main}" alt="{esc(o['title'])}" fetchpriority="high" width="1600" height="1200">
<ul class="gal">{gal}</ul>{more}
<div class="prose" style="margin-top:48px"><h2>Popis nemovitosti</h2>{desc}</div>
<div class="tbl" style="max-width:760px" tabindex="0" role="region" aria-label="Parametry nemovitosti"><table><tbody>{rows}</tbody></table></div></div>
<aside class="pd-side"><span class="tag" style="position:static;align-self:flex-start">{esc(o['status'] or o['deal'])}</span><span class="price">{esc(price)}</span><p class="note2">{esc(note.strip())}</p><div class="facts-row">{fx}</div>
<a class="btn btn-dark" href="/#kontakt" data-topic="Koupě">{'Mám zájem o podobnou' if o['status'] else 'Domluvit prohlídku'}</a><a class="btn btn-line" href="tel:{{{{TEL_HREF}}}}" data-ev="click_phone">{{{{TEL}}}}</a>
<p class="note2">ID zakázky {o['id']} · <a href="https://www.century21.cz{o['path']}" target="_blank" rel="noopener" style="text-decoration:underline">detail na century21.cz</a></p></aside></div></div>
<div class="lb" role="dialog" aria-modal="true" aria-label="Fotogalerie"><img alt=""><button class="x" type="button" aria-label="Zavřít">×</button><button class="pv" type="button" aria-label="Předchozí">‹</button><button class="nx" type="button" aria-label="Další">›</button><span class="cnt"></span></div>''' + CTA
    page('/nabidka/' + o['slug'], f'{o["title"]} | Ondřej Biravský', (o['desc'][:150].rsplit(' ', 1)[0] + '…') if o['desc'] else o['title'], body, og_img=main)


# ---------- optimalizace obrázků ----------
# Každá lokální fotka (včetně nahraných přes editor) dostane WebP verze v několika šířkách,
# srcset/sizes a rozměry, aby se na mobilu stahovalo co nejméně a stránka neposkakovala.
from PIL import Image, ImageOps
OPT_DIR = os.path.join(DIST, 'assets', 'img', '_opt')
os.makedirs(OPT_DIR, exist_ok=True)
_opt_cache = {}
SIZES = {
    'art-hero': '(max-width: 960px) 100vw, 900px',
    'portrait': '(max-width: 900px) 100vw, 45vw',
}
DEFAULT_SIZES = '(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 440px'

def _variants(src):
    if src in _opt_cache: return _opt_cache[src]
    fp = os.path.join(DIST, src.lstrip('/'))
    res = None
    try:
        im = Image.open(fp); im = ImageOps.exif_transpose(im)
        if im.mode not in ('RGB', 'RGBA'): im = im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
        W, H = im.size
        widths = [w for w in (480, 800, 1200, 1600) if w < W] + [min(W, 1600)]
        widths = sorted(set(widths))
        base = re.sub(r'[^a-z0-9]+', '-', os.path.splitext(src.split('/assets/img/', 1)[1])[0].lower()).strip('-')
        out = []
        for w in widths:
            name = f'{base}-{w}.webp'
            op = os.path.join(OPT_DIR, name)
            if not os.path.exists(op):
                v = im if w == W else im.resize((w, round(H * w / W)), Image.LANCZOS)
                v.save(op, 'WEBP', quality=80, method=5)
            out.append((w, f'/assets/img/_opt/{name}'))
        res = (W, H, out)
    except Exception as e:
        print('  ! obrázek nejde zpracovat:', src, e)
    _opt_cache[src] = res
    return res

def _fix_img(m):
    tag = m.group(0)
    sm = re.search(r'\ssrc="(/assets/img/[^"]+\.(?:jpe?g|png|webp))"', tag, re.I)
    if not sm or 'srcset=' in tag or '/_opt/' in tag: return tag
    v = _variants(sm.group(1))
    if not v: return tag
    W, H, out = v
    pick = next((u for w, u in out if w >= 800), out[-1][1])
    cls = re.search(r'class="([^"]*)"', tag)
    sizes = next((SIZES[c] for c in (cls.group(1).split() if cls else []) if c in SIZES), None)
    if not sizes and 'fetchpriority' in tag: sizes = SIZES['portrait']
    wa = re.search(r'\swidth="(\d+)"', tag)
    if not sizes and wa and int(wa.group(1)) <= 300:
        sizes = f'{wa.group(1)}px'
    new = tag.replace(sm.group(0), f' src="{pick}" srcset="{", ".join(f"{u} {w}w" for w, u in out)}" sizes="{sizes or DEFAULT_SIZES}"')
    if not wa:
        new = new[:-1].rstrip('/').rstrip() + f' width="{W}" height="{H}">'
    if 'decoding=' not in new: new = new[:-1] + ' decoding="async">'
    return new

for root, _, files in os.walk(DIST):
    if os.sep + 'admin' in root: continue
    for fn in files:
        if not fn.endswith('.html'): continue
        p = os.path.join(root, fn)
        h = open(p, encoding='utf-8').read()
        h2 = re.sub(r'<img\b[^>]*>', _fix_img, h)
        if h2 != h: open(p, 'w', encoding='utf-8').write(h2)

# ---------- sitemap ----------
open(os.path.join(DIST, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{SITE}{u}</loc></url>\n' for u in sitemap) + '</urlset>\n')
print(f'Hotovo: {len(sitemap)} stránek v sitemap, {len(ARTS)} článků, {len(REFS)} referencí, {n_sold} prodaných, {len(LIST)} v nabídce.')
