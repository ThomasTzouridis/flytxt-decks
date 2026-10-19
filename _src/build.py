# -*- coding: utf-8 -*-
"""Build one Flytxt outreach deck from a spec.  Usage: py build.py specs/<slug>.json
Writes <repo>/<slug>/index.html plus the lead logo and website screenshot next to it."""
import html, json, pathlib, re, shutil, sys

spec_path = pathlib.Path(sys.argv[1]).resolve()
sp = json.loads(spec_path.read_text(encoding="utf-8"))
src = pathlib.Path(__file__).resolve().parent
repo = src.parent
t = (src / "template.html").read_text(encoding="utf-8")

out = repo / sp["slug"]
out.mkdir(exist_ok=True)
logo = spec_path.parent / sp["logo"]
shot = spec_path.parent / sp["shot"]
shutil.copy(logo, out / ("logo" + logo.suffix.lower()))
shutil.copy(shot, out / ("shot" + shot.suffix.lower()))

first = sp.get("first") or sp["name"].split()[0]
headline = sp["headline"]
# cover: headline longer than one line pushes the meta block down
long_head = len(headline) > 48
cases = sp["cases"]
assert len(cases) == 3, "exactly 3 use cases"
m = {
    "NAME": sp["name"], "FIRST": first, "COMPANY": sp["company"], "SITE": sp.get("site", ""),
    "HEADLINE": headline, "META_TOP": "300" if long_head else "250", "NOTE_TOP": "368" if long_head else "318",
    "HELP_INTRO": sp.get("help_intro", ""),
    "CALL_URL": sp.get("call_url", "https://calendly.com/tanja-morsch-flytxt/30min"),
    # logos that are already white with colored parts (waipu.tv) keep their colors: "logo_color": true
    "LOGO_FILTER": "" if sp.get("logo_color") else "filter:brightness(0) invert(1);",
    "LINKEDIN": sp.get("linkedin", "https://www.linkedin.com/in/tanja-morsch-weekone"),
}
for i, c in enumerate(cases, 1):
    m["C%d_HEAD" % i] = c["head"]; m["C%d_TEXT" % i] = c["text"]
    m["C%d_KPI" % i] = c["kpi"]; m["C%d_KPI_LABEL" % i] = c["kpi_label"]
for i, s in enumerate(sp["saw"], 1):
    m["SAW%d" % i] = re.sub(r"</?b>", "", s)   # plain text on slide 2, no bold (Thomas 2026-10-15)
assert len(sp["saw"]) == 3, "exactly 3 'saw' lines"

t = t.replace("###LOGO###", "logo" + logo.suffix.lower()).replace("###SHOT###", "shot" + shot.suffix.lower())
for k, v in m.items():
    # saw lines may carry <b>..</b>, everything else is escaped
    t = t.replace("###%s###" % k, v if k.startswith("SAW") or k == "LOGO_FILTER" else html.escape(v, quote=False))
assert "###" not in t, [l for l in t.splitlines() if "###" in l][:3]
(out / "index.html").write_text(t, encoding="utf-8")
print("built", out / "index.html")
