# Flytxt decks

Personalised 6-slide web decks for Tanja Morsch's outreach (Flytxt, enterprise AI for customer value). First campaign: every industry except banking and finance.

Build: `cd _src; py build.py specs/<slug>.json` writes `<slug>/index.html` (+ `logo.*`, `shot.*`). Check: `py tools/render.py <slug> <outdir>` renders every slide to PNG.
Screenshot and logo of the lead site: `py "..\..\3DforScience\_src\tools\shot.py" <slug> specs <url>`.

Spec fields (`_src/specs/<slug>.json`): slug, name, first, company, site (caption under the screenshot), logo, logo_color (true = keep the logo's colors instead of the white filter, e.g. waipu.tv), shot, headline (cover), saw[3] (may contain `<b>`), help_intro, cases[3] {head, text, kpi, kpi_label}, call_url (default Tanja's Calendly), linkedin.

Slides: 1 cover (headline, prepared for, client logos, Next pill), 2 What we saw at {Company} (screenshot + 3 observations), 3 How we could help (3 use cases + one line on the agentic loop), 4 Who runs on Flytxt (fixed), 5 Who we are (fixed: facts, awards, Gartner disclaimer, EU team), 6 Virtual coffee or tea (Tanja's invitation letter, Calendly button, Tanja's card).

Assets: `assets/` (Flytxt white logo, backgrounds and robot from the Flytxt pptx, client logos from flytxt.ai, awards, team photos from LinkedIn 800px). Results numbers come from `Flytxt_One_Pager_Final.pdf` and `Flytxt Overview_2026.pptx`.

Hosting (2026-10-15): repo `ThomasTzouridis/flytxt-decks` (this folder, `_src/` and `_private/` gitignored), GitHub Pages on `main`, domain `flytxt-cases.com` bought on Spaceship account ACTISCALE (auto-renew on, Spaceship basic DNS: 4 GitHub A records + `www` CNAME to thomastzouridis.github.io). Deck URL: `https://flytxt-cases.com/<slug>/`. Push = live in about a minute.

Slide 4 (2026-10-15): four named clients with photos in `assets/cases/`: Vodafone (Vodafone tower Düsseldorf, Commons CC BY-SA 4.0), Orange (Boutique Orange Champs Elysées, Commons CC BY-SA 4.0), MTN (MTN Bénin HQ Cotonou, Commons CC BY-SA 4.0, Charbel1719), Digicel (Digicel HQ Port-au-Prince at night, Flickr UN Women, CC BY-NC-ND, swap before any public use). Facts: Vodafone numbers from Tanja's slide; Orange MEA 17 OpCos / 130M (2022 press release); MTN 217M / 22 countries; Digicel NEON-dX 2026 / 25 markets. The 13.6x / 28% / +18% / 86% results are anonymised on flytxt.ai, so they sit unattributed in the footer line; Tanja has to name the clients if they should go on the cards. Cover and slide 6 show a scrolling logo marquee (`.marq`).

Tanja's feedback (2026-10-15), applied to the template, keep it for every deck:
- waipu.tv sells only to existing customers: say cross-sell, never winback or acquisition.
- No product names (NiYA-X, NEON-dX) anywhere, the EU team does not use them.
- Locations: Amsterdam, Dubai, India (never Mumbai or Trivandrum).
- Gartner wording: "Challenger position in the Gartner® Magic Quadrant™" plus the non-endorsement line. No Gartner logo until Flytxt supplies its licensed badge (Gartner brand rules).
- No Sense › Reason › Decide › Act › Learn pills; her line: "One smart agentic analytics loop on top of your existing marketing tech stack. No IT replacement, but seamless integration. First pilot live in 8 to 12 weeks."
- Slide 6 is her softer letter ("Virtual coffee or tea, {First}?"), button to https://calendly.com/tanja-morsch-flytxt/30min.
- Only claim offers the lead's own site shows (no "4K" for waipu.tv).
- Number sources: +17% category subscriptions, +18% streaming activity (up to), 86% lower email cost, 13% multi-content subscriptions: Tanja's `20260909-Flytxt-UseCase-for-waiputv.pptx` slide 6 ("comparable OTT engagement programme"). 13.6x conversion, 86% send cost: Overview 2026 slide 11 (Tier-1 African MNO). 28% churn: Overview slide 11 (multi-market European telco). Vodafone 8.6% / 3.6% / 200M: waipu.tv pptx slide 4.
