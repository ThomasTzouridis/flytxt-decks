"""404.html: the generic deck every not-yet-built slug lands on (GitHub Pages serves 404.html for any missing path),
so a lead who clicks early never sees a dead link. The company comes from _private/fx_leads.json via the slug in the URL
(company names only, the repo is public). Real decks overwrite it by simply existing at <slug>/index.html.   py build_fallback.py"""
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
leads = json.load(open(os.path.join(ROOT, '_private', 'fx_leads.json'), encoding='utf-8'))
m = {}
for v in leads.values():
    m.setdefault(v['slug'], v['company'].strip())
t = open(os.path.join(SRC, 'template.html'), encoding='utf-8').read()
# no lead logo and no screenshot on the fallback: drop the logo img and the divider, drop the shot block, widen the text
t = re.sub(r'<span style="width:1px;height:34px;[^"]*"></span><img src="###LOGO###"[^>]*>', '', t)
t = re.sub(r'<div class="blk a shot"[^>]*><img src="###SHOT###"[^>]*></div>\s*<div class="blk a lbl"[^>]*>###SITE###</div>\s*<div class="blk a" style="left:630px;top:170px;width:586px;',
           '<div class="blk a" style="left:64px;top:170px;width:1152px;', t)
assert '###SHOT###' not in t and '###LOGO###' not in t
rep = {'###COMPANY###': '__CO__', '###NAME###': 'the __CO__ team', '###HEADLINE###': 'Turn __CO__&rsquo;s customer data into revenue that stays.',
       '###META_TOP###': '300', '###NOTE_TOP###': '368',
       'Virtual coffee or tea, ###FIRST###?': 'Virtual coffee or tea?', 'Dear ###FIRST###,': 'Hello,',
       '###SAW1###': 'Your homepage sells the same plans and offers to every visitor the same way, whatever they came for.',
       '###SAW2###': 'What your customers use, buy, pause and never open is the strongest signal you have for the next upgrade and the next cancellation. Today that signal sits in analytics, not in the message they receive.',
       '###SAW3###': 'Cross-sell, upsell and anti churn campaigns are built by hand, per segment, per month. The customer who is about to leave this week gets the same offer as everyone else, or none at all.',
       '###HELP_INTRO###': 'Three places where an AI that decides per customer, not per segment, pays for itself in the first quarter.',
       '###C1_HEAD###': 'Stop the cancellation before it happens', '###C1_TEXT###': 'Causal churn signals per customer from usage, pauses and support contacts. The right offer, channel and moment, picked for each customer and tested continuously.',
       '###C1_KPI###': '28%', '###C1_KPI_LABEL###': 'lower churn, measured at Flytxt telecom clients',
       '###C2_HEAD###': 'The next upgrade when it fits', '###C2_TEXT###': 'Next best plan and add-on per customer, triggered by what they actually use. No more blanket upgrade mails to people on the right plan already.',
       '###C2_KPI###': '+17%', '###C2_KPI_LABEL###': 'category subscriptions at an OTT client',
       '###C3_HEAD###': 'Keep the product in use, every week', '###C3_TEXT###': 'Personal nudges in app, push and email, orchestrated so every customer sees a reason to come back to __CO__ again.',
       '###C3_KPI###': '+18%', '###C3_KPI_LABEL###': 'streaming activity at an OTT client',
       '###CALL_URL###': 'https://calendly.com/tanja-morsch-flytxt/30min', '###LINKEDIN###': 'https://www.linkedin.com/in/tanja-morsch-weekone', '###LOGO_FILTER###': ''}
for k, v in rep.items(): t = t.replace(k, v)
assert '###' not in t, [l[:80] for l in t.splitlines() if '###' in l][:3]
t = t.replace('../assets', '/assets').replace('../vendor', '/vendor').replace('../fonts', '/fonts')
js = ('<script>(()=>{const M=' + json.dumps(m, ensure_ascii=False, separators=(',', ':')).replace('</', '<' + chr(92) + '/') + ';'
      'const e=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;");const r=M[location.pathname.split("/").filter(Boolean)[0]]||"your company";'
      'document.body.innerHTML=document.body.innerHTML.split("__CO__").join(e(r));'
      'document.title="Flytxt for "+r;})();</script>\n')
marker = '<script src="/vendor/reveal.js">'
assert marker in t
t = t.replace(marker, js + marker, 1).replace('<title>Flytxt for __CO__', '<title>Flytxt for your company', 1)
open(os.path.join(ROOT, '404.html'), 'w', encoding='utf-8', newline='\n').write(t)
print('404.html', len(t), 'bytes,', len(m), 'slugs')
