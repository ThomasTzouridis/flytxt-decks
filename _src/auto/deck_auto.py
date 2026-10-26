# -*- coding: utf-8 -*-
"""One Flytxt deck from data, with exactly ONE model call (the copy). Everything else is script.
Usage: python3 deck_auto.py <slug> "<First>" "<Company>" <website> "<Title>" "<Industry>" "<Country>"
Steps: site facts -> screenshot + logo -> one claude -p call (Haiku) -> validate -> spec -> build.py
Writes runs/<slug>/run.json with the exact token usage of the model call. Same shape as Craze & Friends/_src/auto/deck_auto.py.
"""
import sys, os, re, json, html, subprocess, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
SPECS = os.path.join(SRC, 'specs')
SHOT = r"C:\Users\Thomas\Desktop\Presentations\3DforScience\_src\tools\shot.py"
WIN = os.name == 'nt'  # PC: PC Playwright first, Mac over ssh as fallback. Mac (the poll job): everything runs locally
MAC = 'thomastzouridis@100.93.68.58'
MAC_VENV = os.path.expanduser('~/ads_ecom/.venv/bin/python3')  # has curl_cffi (Mac); on the hub server the venv does not exist, system python3 has curl_cffi
if not os.path.exists(MAC_VENV): MAC_VENV = sys.executable
MAC_CLAY = os.path.expanduser('~/Desktop/AIOS/Internal Clay')  # proxy_fetch.load_pool()
MODEL = os.environ.get('FX_MODEL', 'claude-haiku-5-5')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
# the only result numbers a deck may carry, with their labels verbatim (sources: README "Number sources", Tanja 2026-10-15)
KPI = {'28%': 'lower churn, measured at Flytxt telecom clients',
       '+17%': 'category subscriptions at an OTT client',
       '+18%': 'streaming activity at an OTT client',
       '86%': 'lower email cost at a Tier-1 African MNO',
       '13.6x': 'conversion vs untargeted campaigns, Tier-1 African MNO',
       '8.6%': 'monthly revenue uplift at Vodafone',
       '3.6%': 'paid content conversion at Vodafone'}
BANNED = r'(?i)niya|neon-dx|neon dx|mumbai|trivandrum|winback|win-back'
slug, first, company, website, title, industry, country = (sys.argv[1:8] + [''] * 7)[:7]
domain = re.sub(r'^www\.', '', re.sub(r'^https?://', '', website.strip().lower())).split('/')[0]
url = website if website.startswith('http') else 'https://' + website
work = os.path.join(HERE, 'runs', slug); os.makedirs(work, exist_ok=True)
os.makedirs(SPECS, exist_ok=True)
log = {'slug': slug, 'model': MODEL, 'calls': [], 'started': datetime.datetime.now().isoformat(timespec='seconds')}


def words(s): return len(re.sub(r'<[^>]+>', ' ', html.unescape(s or '')).split())


# ---------- 1. facts ----------
import requests


def mac_fetch(u):
    """blocked from the PC: same page through one of the 500 Webshare proxies on the Mac"""
    if not WIN:
        try:
            r = subprocess.run([MAC_VENV, os.path.join(HERE, 'mac_fetch.py'), u], capture_output=True, text=True, encoding='utf-8',
                               errors='ignore', timeout=300, env=dict(os.environ, PYTHONPATH=MAC_CLAY))
            return r.stdout if len(r.stdout) > 2000 else ''
        except Exception:
            return ''
    try:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=20', MAC, 'cd ~/flytxt-decks/_src/auto && PYTHONPATH="$HOME/Desktop/AIOS/Internal Clay" ~/ads_ecom/.venv/bin/python3 mac_fetch.py ' + u],
                           capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)
        return r.stdout if len(r.stdout) > 2000 else ''
    except Exception:
        return ''


BLOCK = r'(?i)<title>\s*(just a moment|attention required|access denied|verify you are|security check)'


def fetch(u):
    try:
        r = requests.get(u, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}, timeout=30)
        if r.status_code == 200 and not re.search(BLOCK, r.text[:3000]): return r.text
        blocked = r.status_code in (403, 429, 503) or bool(re.search(BLOCK, r.text[:3000]))
    except Exception:
        blocked = True
    if blocked:
        t = mac_fetch(u)
        if t: print('fetched via Mac proxies:', u); return t
    return ''


def totext(h_):
    t_ = re.sub(r'(?is)<(script|style|noscript|svg|template)[^>]*>.*?</\1>', ' ', h_)
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '\n', t_)))


def clean(x): return html.unescape(re.sub(r'<[^>]+>', ' ', x)).strip()


F = [f"LEAD: {first}, {title} at {company} ({domain}). Industry: {industry or 'n/a'}. Country: {country or 'n/a'}."]
h = fetch(url)
site_ok = bool(h) and len(totext(h)) > 400
pages = {}
if site_ok:
    links = re.findall(r'href="([^"#?]+)"', h)
    want = re.compile(r'(?i)about|company|unternehmen|over-ons|plans?|pricing|tarif|abo|subscri|app|loyal|reward|bonus|vorteil|member|business|b2b|customer|kunden|offer|angebot|deal|bundle|famil|prepaid|postpaid|stream|tv|internet|mobile|mobil')
    seen_p = set()
    for l in links:
        if not want.search(l) or re.search(r'(?i)\.(pdf|jpg|png|svg|css|js)$|login|signin|cart|basket|checkout|privacy|cookie|imprint|impressum|terms|agb', l): continue
        u = l if l.startswith('http') else url.rstrip('/') + '/' + l.lstrip('/')
        if domain not in u or u in seen_p: continue
        seen_p.add(u)
        ph = fetch(u)
        if ph: pages[u] = totext(ph)[:6000]
        if len(pages) >= 6: break
alltext = (totext(h) if site_ok else '') + ' ' + ' '.join(pages.values())
if site_ok:
    ttl = re.search(r'(?is)<title[^>]*>(.*?)</title>', h)
    desc = re.search(r'(?i)<meta[^>]+name="description"[^>]+content="([^"]*)"', h) or re.search(r'(?i)<meta[^>]+content="([^"]*)"[^>]+name="description"', h)
    lang = re.search(r'(?i)<html[^>]+lang="([a-z-]+)"', h)
    heads = list(dict.fromkeys(x for x in (clean(y) for y in re.findall(r'(?is)<h[12][^>]*>(.*?)</h[12]>', h)) if 3 < len(x) < 110))
    subs = list(dict.fromkeys(x for x in (clean(y) for y in re.findall(r'(?is)<h[23][^>]*>(.*?)</h[23]>', h)) if 3 < len(x) < 70 and x not in heads))
    nav = list(dict.fromkeys(x for x in (clean(y) for y in re.findall(r'(?is)<nav[^>]*>(.*?)</nav>', h)[:2] for y in re.findall(r'(?is)<a[^>]*>(.*?)</a>', y)) if 1 < len(x) < 30))
    F.append("SITE: loaded homepage" + (f" + {len(pages)} more pages ({', '.join(re.sub(r'https?://[^/]+', '', u)[:40] for u in pages)})" if pages else '') + (f", site language {lang.group(1)}" if lang else ''))
    F.append("SITE title: " + (clean(ttl.group(1))[:120] if ttl else 'n/a'))
    if desc: F.append("SITE description: " + html.unescape(desc.group(1))[:220])
    if heads: F.append("SITE headlines: " + ' | '.join(heads)[:500])
    if subs: F.append("SITE section names: " + ' | '.join(subs[:18])[:500])
    if nav: F.append("SITE navigation: " + ' | '.join(nav[:24])[:400])
    sig = {'own app': r'(?i)app store|google play|play store|download (the|our) app|unsere app|in der app',
           'customer login or my account': r'(?i)my account|mein konto|mijn account|login|log in|anmelden|inloggen|self.?care|selfcare',
           'subscription plans or tariffs': r'(?i)tarif|abo\b|abonnement|subscription|plan[s]?\b|bundle|paket|monthly|per month|/month|/mo\b|pro monat',
           'prepaid and postpaid': r'(?i)prepaid|postpaid|pay as you go|sim.only',
           'loyalty or rewards programme': r'(?i)loyalty|reward|treue|bonus|cashback|points|punkte|vorteilsprogramm|member benefits',
           'family or multi-line offers': r'(?i)family|familie|famille|multi.?sim|second line|partnerkarte|gezin',
           'streaming or TV content': r'(?i)streaming|stream\b|live tv|tv package|tv paket|channels|kanäle|serien|series|sport',
           'home internet or fibre': r'(?i)fiber|fibre|glasfaser|broadband|home internet|dsl|cable internet|wifi',
           'roaming or travel offers': r'(?i)roaming|travel|reise|abroad',
           'business or B2B segment': r'(?i)business|b2b|geschäftskunden|zakelijk|enterprise|unternehmen',
           'newsletter or email signup': r'(?i)newsletter|subscribe to|sign up for|e-mail updates',
           'promotions or discounts on the homepage': r'(?i)\d+ ?% (off|rabatt|korting)|save \d|sparen|deal|aktion|promo|offer|angebot|gratis|free for|kostenlos',
           'personalised recommendations': r'(?i)recommend|empfehl|for you|für dich|voor jou|personalis'}
    found = [k for k, rx in sig.items() if re.search(rx, alltext)]
    F.append("SITE signals seen (only these exist, never claim others): " + (', '.join(found) if found else 'none'))
    promo = list(dict.fromkeys(re.sub(r'\s+', ' ', x).strip(' .!,') for x in re.findall(r"(?i)[A-Za-z0-9äöüéè€$£%&' ]{0,30}(?:\d+ ?% off[^.|]{0,40}|\d+ ?% rabatt[^.|]{0,40}|\d+ ?% korting[^.|]{0,40}|free for \d[^.|]{0,30}|\d+ monate gratis[^.|]{0,30}|first \d+ months[^.|]{0,30})", alltext)))[:6]
    if promo: F.append("SITE promotions text: " + ' | '.join(promo))
    nums = list(dict.fromkeys(x.strip() for x in re.findall(r'[^.\n|]{0,40}\d[\d.,]{2,}\+?\s*(?:customers|kunden|klanten|subscribers|users|households|haushalte|members|mitglieder|countries|länder|stores|shops|employees|mitarbeiter|years|jahre)[^.\n|]{0,40}', alltext, re.I)))[:6]
    if nums: F.append("SITE proof numbers: " + ' | '.join(nums))
    plans = list(dict.fromkeys(m.group(0).strip() for m in re.finditer(r'(?:€|EUR|CHF|£|\$|kr\.?|DKK|SEK|NOK)\s?\d{1,4}(?:[.,]\d\d)?(?:\s?(?:/|per|pro)\s?(?:month|mo|monat|maand|md|mnd))?|\d{1,4}(?:[.,]\d\d)?\s?(?:€|EUR|CHF|kr\.?|DKK|SEK|NOK)(?:\s?(?:/|per|pro)\s?(?:month|mo|monat|maand|md|mnd))?', alltext)))[:10]
    if plans: F.append("SITE prices seen: " + ', '.join(plans))
    quotes = re.findall(r'[\u201c"]([^\u201d"]{40,200})[\u201d"]', alltext)[:3]
    if quotes: F.append("SITE quotes: " + ' || '.join(q.strip() for q in quotes))
else:
    F.append("SITE: COULD NOT BE LOADED (blocked or down). You know nothing about the website. Write only from the lead line (industry, country, title) and never describe the site, its plans, its app or its offers.")
facts = '\n'.join(F)
open(os.path.join(work, 'facts.txt'), 'w', encoding='utf-8').write(facts)
print('facts chars', len(facts), 'site', 'ok' if site_ok else 'NOT LOADED')
allowed = set(re.findall(r'\d[\d.,]*', facts)) | set(re.findall(r'\d[\d.,]*', ' '.join(KPI))) | set(re.findall(r'\d[\d.,]*', ' '.join(KPI.values())))
allowed = {a.strip('.,') for a in allowed}

# ---------- 2. assets (saved next to the spec, build.py copies them into <slug>/) ----------
shot_file = slug + '_shot.jpg'
shotp = os.path.join(SPECS, shot_file)
shotdir = os.path.join(work, 'shot')
if not os.path.exists(shotp):
    from PIL import Image as _I
    if not WIN:
        os.makedirs(shotdir, exist_ok=True); lp = os.path.join(shotdir, slug + '_mac.png')
        try:
            rr = subprocess.run([sys.executable, os.path.join(HERE, 'mac_shot.py'), url, lp], capture_output=True, text=True, timeout=420)
            if 'ok' in rr.stdout and os.path.exists(lp):
                _I.open(lp).convert('RGB').resize((1200, 750)).save(shotp, quality=88); print('shot ok (Mac)')
            else: print('SHOT FAILED', rr.stdout[-200:], rr.stderr[-300:])
        except Exception as e: print('SHOT FAILED', e)
    else:
        subprocess.run(['py', SHOT, slug, shotdir, url], capture_output=True, text=True, timeout=240)
        s1 = os.path.join(shotdir, slug + '_1.jpg')
        if os.path.exists(s1): shutil.copy(s1, shotp); print('shot ok')
        else:
            print('shot blocked on the PC, retrying on the Mac through a proxy')
            try:
                rr = subprocess.run(['ssh', '-o', 'ConnectTimeout=20', MAC, 'cd ~/flytxt-decks/_src/auto && python3 mac_shot.py ' + url + ' /tmp/fx_shot_' + slug + '.png'], capture_output=True, text=True, timeout=300)
                if 'ok' in rr.stdout:
                    os.makedirs(shotdir, exist_ok=True); lp = os.path.join(shotdir, slug + '_mac.png')
                    subprocess.run(['scp', '-q', MAC + ':/tmp/fx_shot_' + slug + '.png', lp], timeout=120)
                    _I.open(lp).convert('RGB').resize((1200, 750)).save(shotp, quality=88); print('shot ok (Mac)')
                else: print('SHOT FAILED')
            except Exception as e: print('SHOT FAILED', e)
if not os.path.exists(shotp):
    # no screenshot: a dark placeholder with the domain, the deck still ships (the slide text carries the content)
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (1200, 750), (0, 42, 61)); fnt = None
    for fp in (r'C:\Windows\Fonts\arialbd.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'):
        if os.path.exists(fp): fnt = ImageFont.truetype(fp, 64); break
    ImageDraw.Draw(im).text((80, 330), domain, font=fnt, fill=(255, 255, 255)); im.save(shotp, quality=88); print('shot: placeholder')
# logo: shot.py info candidates, else header <img ...logo...>, else text wordmark. The template paints it white (filter), so any colour works.
logo_file = None
for ext in ('svg', 'png'):
    if os.path.exists(os.path.join(SPECS, f'{slug}_logo.{ext}')): logo_file = f'{slug}_logo.{ext}'
if not logo_file:
    cands = []
    info = os.path.join(shotdir, slug + '_info.json')
    if os.path.exists(info):
        try:
            ji = json.load(open(info, encoding='utf-8'))
            cands += [c for c in (ji.get('logos') or ji.get('logo') or []) if isinstance(c, str)]
        except Exception: pass
    if h:
        head_html = re.search(r'(?is)<header.*?</header>', h)
        hh = head_html.group(0) if head_html else h[:60000]
        cands += re.findall(r'<img[^>]+src="([^"]+)"[^>]*(?:logo|Logo|LOGO)', hh) + re.findall(r'<img[^>]*(?:logo|Logo|LOGO)[^>]*src="([^"]+)"', hh)
        cands += re.findall(r'<img[^>]+src="([^"]+)"[^>]*(?:logo|Logo|LOGO)', h) + re.findall(r'<img[^>]*(?:logo|Logo|LOGO)[^>]*src="([^"]+)"', h)
        cands += re.findall(r'(?i)<link[^>]+rel="(?:apple-touch-icon|icon)"[^>]+href="([^"]+)"', h)
    from PIL import Image
    from io import BytesIO
    for c in dict.fromkeys(cands):
        if c.startswith('<svg') or c.startswith('data:'): continue
        u = c if c.startswith('http') else ('https:' + c if c.startswith('//') else url.rstrip('/') + '/' + c.lstrip('/'))
        u = u.split('?')[0]
        try: r = requests.get(u, headers={'User-Agent': UA}, timeout=20)
        except Exception: continue
        if r.status_code != 200: continue
        if u.endswith('.svg') or b'<svg' in r.content[:300]:
            s = r.text
            if '<svg' not in s[:2000]: continue
            logo_file = slug + '_logo.svg'; open(os.path.join(SPECS, logo_file), 'w', encoding='utf-8').write(s); break
        try:
            im = Image.open(BytesIO(r.content)).convert('RGBA')
            if im.width < 48 or im.height < 16: continue
            if not any(a > 128 for a in im.getchannel('A').tobytes()[::97]): continue
            logo_file = slug + '_logo.png'; im.save(os.path.join(SPECS, logo_file)); break
        except Exception: continue
    if not logo_file:
        from PIL import ImageDraw, ImageFont
        fnt = None
        for fp in (r'C:\Windows\Fonts\arialbd.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Supplemental/Impact.ttf'):
            if os.path.exists(fp): fnt = ImageFont.truetype(fp, 120); break
        im = Image.new('RGBA', (2400, 200), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 20), company, font=fnt, fill=(255, 255, 255, 255))
        im = im.crop(im.getbbox()); logo_file = slug + '_logo.png'; im.save(os.path.join(SPECS, logo_file)); print('logo: text wordmark fallback')
print('logo', logo_file)

# ---------- 3. the one model call ----------
PROMPT = open(os.path.join(HERE, 'PROMPT.md'), encoding='utf-8').read()
CLAUDE_ARGS = ['-p', '--model', MODEL, '--output-format', 'json', '--tools', '', '--disable-slash-commands', '--setting-sources', '',
               '--no-session-persistence', '--system-prompt', 'You are a precise B2B copywriter. Return only JSON.']
UNAVAILABLE = r'(?i)not logged in|usage limit|limit reached|out of usage|session limit|weekly limit|disabled claude subscription|oauth token|revoked'


def mac_tokens():
    """Mac: the long lived setup-token tokens in AIOS .env, in order. An account that cannot serve (not logged in, limit hit)
    answers with 0 tokens and no copy, so moving to the next one is not a second model call."""
    envf = os.path.expanduser('~/Desktop/AIOS/.env')
    kv = dict(re.findall(r'^([A-Z0-9_]+)=(.*)$', open(envf, encoding='utf-8').read(), re.M)) if os.path.exists(envf) else {}
    names = os.environ.get('FX_CLAUDE_TOKENS', 'REPLYOS_CLAUDE_OAUTH_TOKEN_2,REPLYOS_CLAUDE_OAUTH_TOKEN,REPLYOS_CLAUDE_OAUTH_TOKEN_3').split(',')
    return [kv[n].strip().strip('"').strip("'") for n in names if kv.get(n, '').strip()]


def record(d):
    u = d.get('usage') or {}
    log['calls'].append(dict({k: u.get(k) for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')},
                             cost_usd=d.get('total_cost_usd'), model=list(d.get('modelUsage', {}))))


def call(msg):
    if not WIN:
        cbin = os.path.expanduser('~/.local/bin/claude'); cfg = os.path.expanduser('~/.claude-accounts/flytxt-decks')
        os.makedirs(cfg, exist_ok=True)
        for tok in mac_tokens():
            e = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}
            e.update(CLAUDE_CONFIG_DIR=cfg, CLAUDE_CODE_OAUTH_TOKEN=tok)
            r = subprocess.run([cbin] + CLAUDE_ARGS, input=msg, capture_output=True, text=True, encoding='utf-8', timeout=300, cwd=work, env=e)
            d = json.loads(r.stdout[r.stdout.index('{'):])
            if d.get('is_error') and re.search(UNAVAILABLE, str(d.get('result'))) and not (d.get('usage') or {}).get('output_tokens'):
                print('claude account unavailable, next token:', str(d.get('result'))[:80]); continue
            break
        else:
            raise SystemExit('no Claude account could serve the call')
        record(d)
        if d.get('is_error'): raise SystemExit('claude error: ' + str(d.get('result'))[:300])
        return d['result']
    r = subprocess.run(['claude'] + CLAUDE_ARGS, input=msg, capture_output=True, text=True, encoding='utf-8', timeout=300, cwd=work, shell=True)
    d = json.loads(r.stdout[r.stdout.index('{'):])
    record(d)
    return d['result']


def validate(sp):
    errs = []
    hd = sp.get('headline') or ''
    if not hd: errs.append('headline missing')
    if len(hd) > 72: errs.append(f'headline has {len(hd)} chars, max 72')
    saw = sp.get('saw') or []
    if len(saw) != 3: errs.append('saw must have 3 items')
    for i, s in enumerate(saw):
        if not 18 <= words(s) <= 46: errs.append(f'saw[{i}] has {words(s)} words, must be 20 to 44')
    cs = sp.get('cases') or []
    if len(cs) != 3: errs.append('cases must have 3 items')
    for i, c in enumerate(cs):
        if not isinstance(c, dict): errs.append(f'cases[{i}] is not an object'); continue
        if not 2 <= len((c.get('head') or '').split()) <= 8: errs.append(f'cases[{i}].head must be 2 to 7 words')
        if not 18 <= words(c.get('text')) <= 38: errs.append(f'cases[{i}].text has {words(c.get("text"))} words, must be 20 to 36')
        if c.get('kpi') not in KPI: errs.append(f'cases[{i}].kpi {c.get("kpi")!r} is not in the KPI pool')
        elif c.get('kpi_label') != KPI[c['kpi']]: errs.append(f'cases[{i}].kpi_label must be exactly {KPI[c["kpi"]]!r}')
    if len({c.get('kpi') for c in cs if isinstance(c, dict)}) < len(cs): errs.append('each case needs a different kpi')
    if not sp.get('help_intro'): errs.append('help_intro missing')
    if not sp.get('site_tag'): errs.append('site_tag missing')
    blob = json.dumps({k: v for k, v in sp.items() if k != 'kpi_label'}, ensure_ascii=False)
    if re.search(BANNED, blob): errs.append('banned word found (product names, Mumbai, Trivandrum, winback)')
    if re.search(r'<\s*/?\s*(b|strong)[\s>]', blob, re.I): errs.append('bold found, plain text only')
    if re.search(r'[\u2013\u2014]| - ', html.unescape(blob)): errs.append('dash found, remove every dash')
    if re.search(r'(?i)fact sheet|scraped|crawled', blob): errs.append('never mention the fact sheet or scraping')
    for num in set(re.findall(r'\d[\d.,]*', html.unescape(blob))):
        n = num.strip('.,')
        if n not in allowed and not (n.isdigit() and 1900 < int(n) < 2100) and not (n.isdigit() and int(n) <= 12): errs.append(f'number {num} is not in the FACT SHEET or the KPI pool')
    return errs


msg = PROMPT + '\n\nFACT SHEET\n' + facts + '\n\nReturn the JSON now.'
out = call(msg)


def mech(x):
    """fixes that never need the model: strip bold tags, turn dashes into commas"""
    if isinstance(x, str):
        x = re.sub(r'</?\s*(b|strong)\s*>', '', x, flags=re.I)
        return re.sub(r'\s*[\u2013\u2014]\s*| - ', ', ', x)
    if isinstance(x, list): return [mech(i) for i in x]
    if isinstance(x, dict): return {k: mech(v) for k, v in x.items()}
    return x


try:
    sp = mech(json.loads(out[out.index('{'):out.rindex('}') + 1]))
    for c in sp.get('cases') or []:
        if isinstance(c, dict) and c.get('kpi') in KPI: c['kpi_label'] = KPI[c['kpi']]   # label always verbatim from the pool
    errs = validate(sp)
except Exception as e:
    sp, errs = None, ['output was not valid JSON: ' + str(e)]
hard = [e for e in errs if 'not in the FACT SHEET' in e or 'JSON' in e or 'must have 3' in e or 'missing' in e or 'KPI pool' in e or 'banned' in e or 'not an object' in e or 'different kpi' in e]
soft = [e for e in errs if e not in hard]
if soft: print('soft issues (kept, no second call):', soft)
spec = None if hard else sp
if hard: print('HARD errors, no second call, deck not built:', hard)
log['validation_errors_last'] = errs; log['soft_issues'] = soft if sp else []
if spec is None:
    log['status'] = 'FAILED validation'; json.dump(log, open(os.path.join(work, 'run.json'), 'w'), indent=1); sys.exit('copy failed hard validation, one call only, no retry')

# ---------- 4. spec + build ----------
U = html.unescape  # build.py escapes every field except saw, so entities (&rsquo; ...) become real characters here
final = {'slug': slug, 'name': first, 'first': first, 'company': company, 'site': f"{domain} · {U(spec['site_tag'])}", 'logo': logo_file, 'shot': shot_file,
         'headline': U(spec['headline']), 'saw': spec['saw'], 'help_intro': U(spec['help_intro']),
         'cases': [{'head': U(c['head']), 'text': U(c['text']), 'kpi': c['kpi'], 'kpi_label': c['kpi_label']} for c in spec['cases']],
         'call_url': 'https://calendly.com/tanja-morsch-flytxt/30min', 'linkedin': 'https://www.linkedin.com/in/tanja-morsch-weekone'}
sp_path = os.path.join(SPECS, slug + '.json')
json.dump(final, open(sp_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
b = subprocess.run([sys.executable, 'build.py', os.path.join('specs', slug + '.json')], cwd=SRC, capture_output=True, text=True, encoding='utf-8')
print(b.stdout.strip(), b.stderr.strip()[-300:])
log['status'] = 'built' if 'built' in b.stdout else 'build failed'
tot = {k: sum(c[k] or 0 for c in log['calls']) for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')}
log['total'] = dict(tot, all_tokens=sum(tot.values()), cost_usd=sum(c['cost_usd'] or 0 for c in log['calls']))
json.dump(log, open(os.path.join(work, 'run.json'), 'w'), indent=1)
print('TOKENS', json.dumps(log['total']), 'calls', len(log['calls']))
