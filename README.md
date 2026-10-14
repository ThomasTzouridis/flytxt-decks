# Flytxt decks

Personalised 6-slide web decks for Tanja Morsch's outreach (Flytxt, enterprise AI for customer value). First campaign: every industry except banking and finance.

Build: `cd _src; py build.py specs/<slug>.json` writes `<slug>/index.html` (+ `logo.*`, `shot.*`). Check: `py tools/render.py <slug> <outdir>` renders every slide to PNG.
Screenshot and logo of the lead site: `py "..\..\3DforScience\_src\tools\shot.py" <slug> specs <url>`.

Spec fields (`_src/specs/<slug>.json`): slug, name, first, company, site (caption under the screenshot), logo, shot, headline (cover), saw[3] (may contain `<b>`), help_intro, cases[3] {head, text, kpi, kpi_label}, call_url, linkedin.

Slides: 1 cover (headline, prepared for, client logos, Next pill), 2 What we saw at {Company} (screenshot + 3 observations), 3 How we could help (3 use cases + Sense › Reason › Decide › Act › Learn), 4 Results we delivered (fixed), 5 Who we are (fixed: facts, awards, EU team), 6 Let's talk (Book a call, Tanja's card).

Assets: `assets/` (Flytxt white logo, backgrounds and robot from the Flytxt pptx, client logos from flytxt.ai, awards, team photos from LinkedIn 800px). Results numbers come from `Flytxt_One_Pager_Final.pdf` and `Flytxt Overview_2026.pptx`.
