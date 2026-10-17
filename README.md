# Flytxt decks

Personalised 6-slide web decks for Tanja Morsch's outreach (Flytxt, enterprise AI for customer value). First campaign: every industry except banking and finance.

Build: `cd _src; py build.py specs/<slug>.json` writes `<slug>/index.html` (+ `logo.*`, `shot.*`). Check: `py tools/render.py <slug> <outdir>` renders every slide to PNG.
Screenshot and logo of the lead site: `py "..\..\3DforScience\_src\tools\shot.py" <slug> specs <url>`.

Spec fields (`_src/specs/<slug>.json`): slug, name, first, company, site (caption under the screenshot), logo, logo_color (true = keep the logo's colors instead of the white filter, e.g. waipu.tv), shot, headline (cover), saw[3] (may contain `<b>`), help_intro, cases[3] {head, text, kpi, kpi_label}, call_url (default Tanja's Calendly), linkedin.

Slides: 1 cover (headline, prepared for, client logos, Next pill), 2 What we saw at {Company} (screenshot + 3 observations), 3 How we could help (3 use cases + one line on the agentic loop), 4 More of our work (fixed), 5 Who we are (fixed: facts, awards, Gartner logo, EU team), 6 Virtual coffee or tea (Tanja's invitation letter verbatim, Book a call button to Calendly, Tanja's card).

Assets: `assets/` (Flytxt white logo, backgrounds and robot from the Flytxt pptx, client logos from flytxt.ai, awards, team photos from LinkedIn 800px). Results numbers come from `Flytxt_One_Pager_Final.pdf` and `Flytxt Overview_2026.pptx`.

Hosting (2026-10-15): repo `ThomasTzouridis/flytxt-decks` (this folder, `_src/` and `_private/` gitignored), GitHub Pages on `main`, domain `flytxt-cases.com` bought on Spaceship account ACTISCALE (auto-renew on, Spaceship basic DNS: 4 GitHub A records + `www` CNAME to thomastzouridis.github.io). Deck URL: `https://flytxt-cases.com/<slug>/`. Push = live in about a minute.

Slide 4 (2026-10-17): three named clients, 368px cards. Vodafone keeps its photo (`assets/cases/vodafone.jpg`, Vodafone tower Düsseldorf, Commons CC BY-SA 4.0). Orange and MTN show a brand panel instead of a building photo (Thomas 2026-10-17: no random office buildings for multibillion companies, a clean logo is better): Orange = black panel with the orange square (`assets/clients/orange_square.svg`, crisp hand-drawn SVG, the old `orange.svg` is a low-res PNG wrapper and stays for the marquee), MTN = #ffcb05 panel with the black MTN ellipse (`assets/clients/mtn.svg`). CSS `.ph.lg.orange` / `.ph.lg.mtn` in the template, no small brand tile on those two. Rule for new cards: real photo only if it is as strong as the Vodafone tower, otherwise brand panel. Facts: Vodafone numbers from Tanja's slide; Orange MEA 17 OpCos / 130M (2022 press release); MTN 217M / 22 countries. Digicel card REMOVED on 2026-10-16 on Tanja's request: Flytxt only has the Trinidad and Tobago deal, not 25 markets, and three references are enough. Digicel stays in the logo marquee. Unused photos in `assets/cases/` (orange.jpg = Orange Cameroun HQ Douala, mtn.jpg = MTN Plaza Lagos, both Commons CC BY-SA 4.0; digicel.jpg CC BY-NC-ND). The 13.6x / 28% / +18% / 86% results are anonymised on flytxt.ai, so they sit unattributed in the footer line; Tanja has to name the clients if they should go on the cards. Cover and slide 6 show a scrolling logo marquee (`.marq`).

Tanja's feedback (2026-10-15), applied to the template, keep it for every deck:
- waipu.tv sells only to existing customers: say cross-sell, never winback or acquisition.
- No product names (NiYA-X, NEON-dX) anywhere, the EU team does not use them.
- Locations: Amsterdam, Dubai, India (never Mumbai or Trivandrum).
- Gartner: "Challenger position in the Gartner® Magic Quadrant™" with the Gartner logo (`assets/awards/gartner.svg`, original color on a white tile).
- No Sense › Reason › Decide › Act › Learn pills; her line verbatim: "One smart agentic analytics loop on top of your existing Marketing Tech stack. No IT replacement, but seamless integration. First pilot live in 8-12 weeks."
- Slide 6 is her softer letter ("Virtual coffee or tea, {First}?"), button to https://calendly.com/tanja-morsch-flytxt/30min.
- Only claim offers the lead's own site shows (no "4K" for waipu.tv).
- Number sources: +17% category subscriptions, +18% streaming activity (up to), 86% lower email cost, 13% multi-content subscriptions: Tanja's `20260909-Flytxt-UseCase-for-waiputv.pptx` slide 6 ("comparable OTT engagement programme"). 13.6x conversion, 86% send cost: Overview 2026 slide 11 (Tier-1 African MNO). 28% churn: Overview slide 11 (multi-market European telco). Vodafone 8.6% / 3.6% / 200M: waipu.tv pptx slide 4.
- Apply her feedback verbatim, no own rewording on top.
- Client logos (2026-10-16): never white-filtered, always original brand colors on a white tile (MTN on its yellow #ffcb05), in the marquee and on the slide 4 cards. Check every new logo in a render.

Phones and Next buttons (2026-10-17, Tanja: 57 to 70% of LinkedIn is read on mobile, the deck was tiny on her phone, and the Next pills stopped working from slide 3 on touch screens):
- Up to 700px wide the template switches to `html.phone` (set in the head, reveal.css disabled, Reveal not started): one readable slide per screen, continuous vertical scroll that snaps to each slide start, slides taller than the screen simply scroll on. Bottom bar with prev/next, counter and dots. Same pattern as Craze & Friends.
- The Next pills are JS now (`Reveal.next()` on laptop and tablet, jump to the next slide on phones), no more `#/0/n` hash links.
- Desktop layout is unchanged. Test phones at 390x844 and 360x640 with Playwright `is_mobile` + `has_touch` before every push.
