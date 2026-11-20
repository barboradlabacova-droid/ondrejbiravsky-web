"""Stáhne fotky nemovitostí z Igluu do static/assets/img/igluu/ (trvalá kopie ve webu).

Spouští se automaticky na GitHubu (.github/workflows/fotky-igluu.yml), když se změní
content/igluu.json, a jednou týdně. Už stažené fotky přeskočí, nic nemaže.
Fotka se zmenší na max. 1600 px; web si z ní při sestavení udělá lehké WebP verze.
"""
import io, json, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'static', 'assets', 'img', 'igluu')
URL = 'https://live-file-api.igluu.cz/file/{}?isPublic=true'
MAX = 1600


def ids():
    d = json.load(open(os.path.join(ROOT, 'content', 'igluu.json'), encoding='utf-8'))
    seen = []
    for o in d.get('active', []):
        seen += o.get('imgs', [])          # všechny fotky do galerie
    for o in d.get('realized', []):
        seen += o.get('imgs', [])[:1]      # u prodaných stačí titulní
    return list(dict.fromkeys(seen))


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ondrejbiravsky.cz/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def one(fid):
    fp = os.path.join(OUT, f'{fid}.jpg')
    if os.path.exists(fp):
        return 'skip'
    try:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(fetch(URL.format(fid)))))
        im = im.convert('RGB')
        if im.width > MAX:
            im = im.resize((MAX, round(im.height * MAX / im.width)), Image.LANCZOS)
        tmp = fp + '.part'
        im.save(tmp, 'JPEG', quality=85, optimize=True, progressive=True)
        os.replace(tmp, fp)
        return 'ok'
    except Exception as e:
        print(f'  ! {fid}: {e}', file=sys.stderr)
        return 'err'


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    todo = ids()
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, todo))
    print(f'Fotky Igluu: {res.count("ok")} nových, {res.count("skip")} už staženo, {res.count("err")} chyb (celkem {len(todo)}).')
    sys.exit(1 if res.count('err') and not res.count('ok') and not res.count('skip') else 0)
