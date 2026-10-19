# -*- coding: utf-8 -*-
"""Flytxt deck poller. Runs on the Mac (mac-hub job flytxt_decks, every 6 h), checkout ~/flytxt-decks.
Every running Flytxt HeyReach campaign (workspace key HEYREACH_FLYTXT_API_KEY, campaigns found via /campaign/GetAll, DRAFT and CANCELED skipped)
-> leads who connected -> one deck per lead slug (deck_auto.py, ONE Haiku call) -> git push (GitHub Pages, https://flytxt-cases.com/<slug>/).
Every slug already resolves to the generic 404.html fallback, so a lead is never sent a dead link.
Lead facts come from the campaign's HeyReach list custom fields (slug, firstname, normalizedcompanyname, website, title) and, as fallback,
from _private/fx_leads.json (keyed by lowercased LinkedIn /in/ id, built from the normalized lead CSV).
Rules: a slug is built once; a hard copy failure is never retried (no second model call), it is alerted and the fallback stays;
an infrastructure failure before the model call is retried on later runs, max 3 attempts.
The Presentation Log sheet is owned by mac-hub hr_track.py (clients/flytxt.json), this poller never writes a sheet.
  python3 _src/auto/fx_poll.py            real run
  python3 _src/auto/fx_poll.py --dry      list who would be built, change nothing
  python3 _src/auto/fx_poll.py --slug x   force one slug (must be connected in HeyReach or --force)
"""
import os, sys, re, json, time, shutil, subprocess, urllib.request, urllib.error, datetime, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
HOME = os.path.expanduser('~')
B = 'https://api.heyreach.io/api/public'
STATE = os.path.join(ROOT, '_private', 'fx_poll_state.json')
LOCK = os.path.join(ROOT, '_private', 'fx_poll.lock')
LEADMAP = os.path.join(ROOT, '_private', 'fx_leads.json')
CONNECTED = re.compile(r'(?i)accept|^connected|already')
NOT_CONNECTED = {'None', 'ConnectionSent', 'ConnectionRequested', 'Pending'}
SKIP_STATUS = {'DRAFT', 'CANCELED', 'CANCELLED'}
MAX_ATTEMPTS = 3
PER_RUN = 40            # decks per run (runs every 6 h, the deck link goes out days after the accept), the rest waits for the next run
SITE = 'https://flytxt-cases.com/'
KEY = ''


def now(): return datetime.datetime.now().isoformat(timespec='seconds')


def say(*a): print(now(), *a, flush=True)


def env(k):
    kv = dict(re.findall(r'^([A-Z0-9_]+)=(.*)$', open(os.path.join(HOME, 'Desktop', 'AIOS', '.env'), encoding='utf-8').read(), re.M))
    return kv.get(k, '').strip().strip('"').strip("'")


def alert(text):
    """DM to Thomas (the mac-hub alert channel is archived, so common.slack_alert goes nowhere)."""
    say('ALERT', text)
    try:
        tok = env('SLACK_USER_TOKEN')
        r = urllib.request.Request('https://slack.com/api/chat.postMessage', json.dumps({'channel': 'U09HBPS205B', 'text': 'Flytxt decks: ' + text}).encode(),
                                   {'Content-Type': 'application/json; charset=utf-8', 'Authorization': 'Bearer ' + tok})
        urllib.request.urlopen(r, timeout=20).read()
    except Exception as e:
        say('slack failed', e)


def hr(path, body=None, method='POST'):
    for a in range(6):
        try:
            r = urllib.request.Request(B + path, json.dumps(body).encode() if body is not None else None,
                                       {'X-API-KEY': KEY, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method=method)
            t = urllib.request.urlopen(r, timeout=60).read().decode()
            return json.loads(t) if t.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(20 * (a + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if a < 5: time.sleep(10 * (a + 1)); continue
            raise


def pages(path, body):
    off = 0
    while True:
        d = hr(path, dict(body, offset=off, limit=100))
        items = d.get('items') or []
        for i in items: yield i
        if len(items) < 100: return
        off += 100


def live_code(slug):
    """200 = a real deck is served, 404 = GitHub Pages is serving the generic fallback."""
    try:
        return urllib.request.urlopen(urllib.request.Request(SITE + slug + '/', headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).status
    except urllib.error.HTTPError as e: return e.code
    except Exception: return 0


def git(*args, check=True):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
    if check and r.returncode: raise RuntimeError('git %s: %s' % (' '.join(args), (r.stderr or r.stdout)[-400:]))
    return r.stdout


def requote(s):
    return urllib.request.unquote(s).lower()


def lid_of(url):
    m = re.search(r'linkedin\.com/in/([^/?#]+)', url or '', re.I)
    return requote(m.group(1)) if m else ''


def campaigns():
    """{campaign id: (name, list id)} for every Flytxt campaign that is not DRAFT or CANCELED."""
    out = {}
    for c in pages('/campaign/GetAll', {}):
        if (c.get('status') or '').upper() in SKIP_STATUS: continue
        out[c['id']] = (c.get('name') or '', c.get('linkedInUserListId'))
    return out


def connected_leads(camps):
    """{linkedin id: facts} for every lead in the running campaigns whose connection is accepted or pre-existing."""
    out, seen = {}, {}
    for cid, (cname, _lid) in camps.items():
        for i in pages('/campaign/GetLeadsFromCampaign', {'campaignId': cid}):
            st = i.get('leadConnectionStatus') or 'None'
            seen[st] = seen.get(st, 0) + 1
            pr = i.get('linkedInUserProfile') or {}
            lid = lid_of(pr.get('profileUrl'))
            if lid and st not in NOT_CONNECTED and CONNECTED.search(st):
                out[lid] = {'status': st, 'campaign': cid, 'sender': i.get('linkedInSenderFullName') or '',
                            'name': ('%s %s' % (pr.get('firstName') or '', pr.get('lastName') or '')).strip(), 'company': pr.get('companyName') or ''}
    say('HeyReach connection statuses:', seen)
    return out


def list_facts(list_id):
    """linkedin id -> the custom fields of the campaign's list (slug, website, firstname, normalizedcompanyname, title, presentation)."""
    out = {}
    for i in pages('/list/GetLeadsFromList', {'listId': list_id}):
        lid = lid_of(i.get('profileUrl'))
        if not lid: continue
        cf = {f.get('name'): (f.get('value') or '').strip() for f in (i.get('customFields') or []) if f.get('name')}
        out[lid] = {'slug': cf.get('slug', ''), 'first': cf.get('firstname') or i.get('firstName') or '', 'company': cf.get('normalizedcompanyname') or i.get('companyName') or '',
                    'website': cf.get('website', ''), 'title': cf.get('title') or i.get('position') or '', 'link': cf.get('presentation', ''),
                    'name': ('%s %s' % (i.get('firstName') or '', i.get('lastName') or '')).strip()}
    return out


def slug_files(slug):
    out = [slug + '/index.html', slug + '/logo.svg', slug + '/logo.png', slug + '/shot.jpg', slug + '/shot.png', '_src/specs/' + slug + '.json',
           '_src/specs/' + slug + '_shot.jpg', '_src/specs/' + slug + '_logo.svg', '_src/specs/' + slug + '_logo.png']
    return [f for f in out if os.path.exists(os.path.join(ROOT, f))]


def log_row(st, result, ran, secs, note):
    t = ran.get('total') or {}
    st['last'] = {'result': result, 'calls': len(ran.get('calls') or []), 'in': t.get('input_tokens', ''), 'cw': t.get('cache_creation_input_tokens', ''),
                  'cr': t.get('cache_read_input_tokens', ''), 'out': t.get('output_tokens', ''), 'total': t.get('all_tokens', ''), 'secs': secs,
                  'note': (note or '')[:300].replace('\n', ' ')}


def build(slug, lead, state):
    st = state.setdefault(slug, {'status': 'new', 'attempts': 0})
    t0 = time.time()
    if not lead.get('website'):
        st.update(status='failed', error='no website', at=now()); log_row(st, 'FAILED no website', {}, 0, '')
        alert('no website for %s (/%s/), no deck. The generic fallback page stays live.' % (lead['company'], slug)); return False
    st['attempts'] += 1
    runj = os.path.join(HERE, 'runs', slug, 'run.json')
    shutil.rmtree(os.path.dirname(runj), ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, 'deck_auto.py'), slug, lead['first'], lead['company'], lead['website'], lead.get('title', ''),
                        lead.get('industry', ''), lead.get('country', '')],
                       cwd=HERE, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1500,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONPATH=os.path.join(HOME, 'Desktop', 'AIOS', 'Internal Clay')))
    tail = (p.stdout + p.stderr)[-600:]
    ran = {}
    try: ran = json.load(open(runj, encoding='utf-8'))
    except Exception: pass
    called = bool(ran.get('calls'))
    ok = p.returncode == 0 and ran.get('status') == 'built' and os.path.exists(os.path.join(ROOT, slug, 'index.html'))
    if ok:
        git('add', '--', *slug_files(slug))
        git('commit', '-q', '-m', 'deck %s (auto)\n\nCo-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>' % slug)
        st.update(status='built', at=now(), built_ts=time.time(), tokens=(ran.get('total') or {}).get('all_tokens'))
        log_row(st, 'BUILT', ran, int(time.time() - t0), '; '.join(ran.get('soft_issues') or []))
        say('built', slug, st.get('tokens'), 'tokens'); return True
    # failure: remove half written files of this slug, the fallback keeps serving the URL
    shutil.rmtree(os.path.join(ROOT, slug), ignore_errors=True)
    for f in slug_files(slug):
        try: os.remove(os.path.join(ROOT, f))
        except OSError: pass
    if called:
        st.update(status='failed', error='copy or build failed after the model call, never retried', at=now())
        log_row(st, 'FAILED after model call (no retry)', ran, int(time.time() - t0), str(ran.get('validation_errors_last') or tail[-200:]))
        alert('deck for %s (/%s/) failed after the one model call, not retried. Fallback page stays. %s' % (lead['company'], slug, tail[-250:]))
    elif st['attempts'] >= MAX_ATTEMPTS:
        st.update(status='failed', error='infra failed %d times' % st['attempts'], at=now())
        log_row(st, 'FAILED infra, gave up', ran, int(time.time() - t0), tail[-250:])
        alert('deck for %s (/%s/) failed %d times before the model call. Fallback page stays. %s' % (lead['company'], slug, st['attempts'], tail[-250:]))
    else:
        st.update(status='retry', error=tail[-200:], at=now()); log_row(st, 'RETRY (infra, before model call)', ran, int(time.time() - t0), tail[-250:]); say('infra failure, retry next run:', slug, tail[-200:])
    return False


def push():
    for a in range(3):
        try:
            git('pull', '--rebase', '--autostash', '-q'); git('push', '-q'); return True
        except RuntimeError as e:
            say('push failed', a, e); time.sleep(15)
    return False


def main():
    global KEY
    ap = argparse.ArgumentParser(); ap.add_argument('--dry', action='store_true'); ap.add_argument('--slug'); ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 4 * 3600: say('locked, previous run active'); return
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    open(LOCK, 'w').write(now())
    try:
        KEY = env('HEYREACH_FLYTXT_API_KEY')
        if not KEY: raise RuntimeError('HEYREACH_FLYTXT_API_KEY missing in ~/Desktop/AIOS/.env')
        git('pull', '--rebase', '--autostash', '-q')
        lmap = json.load(open(LEADMAP, encoding='utf-8')) if os.path.exists(LEADMAP) else {}
        state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
        camps = campaigns()
        say('running Flytxt campaigns:', {k: v[0] for k, v in camps.items()} or 'none')
        conn = connected_leads(camps) if camps else {}
        say('connected leads in HeyReach:', len(conn))
        facts = {}
        for cid, (_n, list_id) in camps.items():
            if not list_id: continue
            try: facts.update(list_facts(list_id))
            except Exception as e: say('list facts failed', cid, e)
        cs = state.setdefault('_conn', {})
        todo, unmatched = {}, []
        for lid, info in conn.items():
            f = dict(lmap.get(lid) or {}); f.update({k: v for k, v in (facts.get(lid) or {}).items() if v})
            if not f.get('slug') or not f.get('company'):
                unmatched.append(lid); continue
            c = cs.setdefault(lid, {'first_ts': time.time(), 'first_seen': now()})
            c.update(name=f.get('name') or info['name'], company=f['company'], sender=info['sender'], campaign=info['campaign'], status=info['status'], slug=f['slug'], link=f.get('link', ''))
            todo.setdefault(f['slug'], f)
        if a.slug:
            lead = next((v for v in lmap.values() if v['slug'] == a.slug), None) or todo.get(a.slug)
            if lead and (a.slug in todo or a.force): todo = {a.slug: lead}
            else: say('slug not connected (use --force)'); return
        if unmatched:
            known = state.setdefault('_unmatched', [])
            new = [u for u in unmatched if u not in known]
            if new: alert('%d connected leads have no slug or company in the HeyReach list or the lead map, no deck: %s' % (len(new), ', '.join(new[:5]))); known += new
        pending = [s for s in todo if state.get(s, {}).get('status') in (None, 'new', 'retry') and not os.path.exists(os.path.join(ROOT, s, 'index.html'))]
        say('slugs connected:', len(todo), 'to build:', len(pending), pending[:20])
        if a.dry:
            for lid, c in cs.items(): print(c['company'], c['slug'], c.get('link'), c['first_seen'])
            return
        built = 0
        for slug in pending[:PER_RUN]:
            try:
                if build(slug, todo[slug], state): built += 1
            except Exception as e:
                state.setdefault(slug, {'attempts': 0}).update(status='retry' if state.get(slug, {}).get('attempts', 0) < MAX_ATTEMPTS else 'failed', error=str(e)[-200:])
                say('error', slug, e)
                if state[slug]['status'] == 'failed': alert('deck for %s (/%s/) crashed %d times: %s' % (todo[slug]['company'], slug, MAX_ATTEMPTS, str(e)[-200:]))
            json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        if built and not push(): alert('git push FAILED after building %d decks, they are committed locally and go out on the next run' % built)
        elif not built:
            ahead = git('rev-list', '--count', '@{u}..HEAD', check=False).strip()
            if ahead not in ('', '0'): push()
        # control check: every connected lead's deck must be live and must be the URL HeyReach sends
        done = {}
        for lid, c in cs.items():
            if c['slug'] not in done: done[c['slug']] = live_code(c['slug'])
            c['live'] = done[c['slug']]
            st = state.get(c['slug'], {})
            link_slug = (c.get('link') or '').rstrip('/').split('/')[-1]
            age = (time.time() - c['first_ts']) / 60
            if c.get('link') and link_slug != c['slug']: chk = 'URL MISMATCH: HeyReach sends /%s/, slug is /%s/' % (link_slug, c['slug'])
            elif not c.get('link'): chk = 'NO presentation FIELD IN HEYREACH LIST'
            elif c['live'] == 200: chk = 'OK'
            elif st.get('status') == 'failed': chk = 'DECK FAILED, fallback page is shown'
            elif st.get('status') == 'built': chk = 'BUILT BUT NOT LIVE YET' if (time.time() - st.get('built_ts', 0)) < 1800 else 'BUILT BUT NOT LIVE, CHECK PAGES'
            else: chk = 'BUILDING' if age < 420 else 'NO DECK %d min after connect' % age
            c['check'] = chk
            if chk in ('OK', 'BUILDING', 'BUILT BUT NOT LIVE YET'): continue
            kf = lid + '|' + chk[:20]
            if kf not in state.setdefault('_flagged', []):
                state['_flagged'].append(kf); alert('control check: %s (%s, /%s/): %s' % (c['name'], c['company'], c['slug'], chk))
        json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        if len(pending) > PER_RUN: say('%d more waiting for the next run' % (len(pending) - PER_RUN))
    finally:
        try: os.remove(LOCK)
        except OSError: pass


if __name__ == '__main__':
    try: main()
    except Exception as e:
        alert('poller crashed: %s' % str(e)[-300:]); raise
