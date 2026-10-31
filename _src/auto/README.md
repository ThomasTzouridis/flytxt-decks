# Flytxt deck automation (Mac, mac-hub job `flytxt_decks`)

Clone of the Craze & Friends automation (`Desktop\Presentations\Craze & Friends\_src\auto`), same rules, Flytxt copy.

## Flow (end to end, no hands)

1. HeyReach campaign "Flytxt | Tanja Morsch" (workspace 168063, list 1042117, 663 leads) sends the connection request. Every lead in the list carries the custom fields `firstname`, `title`, `normalizedcompanyname`, `website`, `slug`, `presentationlink` (= `presentation`, the deck URL `https://flytxt-cases.com/<slug>/`).
2. Every link already works: `404.html` (built by `build_fallback.py` from `_private/fx_leads.json`, company names only) is the generic deck GitHub Pages serves for any slug without a folder.
3. mac-hub runs `fx_poll.py` every 6 h on the Mac (checkout `~/flytxt-decks`, deploy key `~/.ssh/flytxt_deploy`, ssh alias `github-flytxt`): every running Flytxt campaign (`/campaign/GetAll`, DRAFT and CANCELED skipped, so nothing is hard-coded) -> leads whose connection is accepted -> one deck per slug via `deck_auto.py` -> `git push` -> live in about a minute. Max 40 decks per run.
4. `deck_auto.py` = site facts (homepage + up to 6 inner pages, Webshare proxy fallback through `mac_fetch.py`), screenshot (`mac_shot.py`, Playwright + Webshare proxies), logo (`_src/tools/logo.py` only, the shared tool from SOP Lead Logo: header candidates rendered in a browser, forced white for the dark slide, guard refuses small, narrow or unreadable files, `build.py` refuses anything else; no usable logo means a white text wordmark), ONE Haiku call (`PROMPT.md`, `claude -p` on the Mac with the setup tokens `REPLYOS_CLAUDE_OAUTH_TOKEN_2`, `_1`, `_3` from AIOS `.env`, config dir `~/.claude-accounts/flytxt-decks`), validation, spec `_src/specs/<slug>.json`, `build.py`. Token usage per deck in `runs/<slug>/run.json`.
5. Tracking is NOT in this folder: every deck posts beacons (open, slide, book, ping, leave) to mac-hub `/webhook/flytxt-deck-track`, Calendly links get `utm_source=flytxt-deck`, `utm_campaign=<slug>`; mac-hub `hr_track.py` (`clients/flytxt.json`, jobs `flytxt_track` every 4 h, `flytxt_perf` 04:00) writes the Presentation Log, Meetings and Performance tabs of the sheet `1sBD1flZseTmt_VjiKkSQ1Kb5_YaWPVmxP9ZV7CDd20E`. This poller never writes a sheet.

## Rules baked in

- A slug is built once. A hard copy failure (invalid JSON, number not in the facts, KPI not in the pool, banned word) is never retried, no second model call: Slack DM to Thomas, the fallback page stays. Infra failures before the model call retry on later runs, max 3.
- Copy rules (Tanja 2026-10-15): no product names, no Mumbai/Trivandrum, cross-sell never acquisition or winback, only claim what the lead's site shows, numbers only from the KPI pool (28%, +17%, +18%, 86%, 13.6x, 8.6%, 3.6%) with their labels verbatim, no dashes, no bold.
- Control check every run: the `presentation` URL HeyReach sends must end in the lead's slug and must answer 200 once built; otherwise a Slack DM.
- Alerts go as Slack DM to Thomas (`SLACK_USER_TOKEN`, user U09HBPS205B), prefixed "Flytxt decks:".

## Commands

```
python3 _src/auto/fx_poll.py --dry              who is connected, what would be built
python3 _src/auto/fx_poll.py --slug <s> --force  build one deck now (also for a test), commits and pushes
py _src/auto/build_fallback.py                   rebuild 404.html after the lead map changed
py _src/auto/deck_auto.py <slug> "<First>" "<Company>" <website> "<Title>" "<Industry>" "<Country>"   one deck on the PC (claude CLI + shot.py)
```

State: `_private/fx_poll_state.json` (per slug status, attempts, tokens, per lead first connected, live code, check), lock `_private/fx_poll.lock`. Lead map `_private/fx_leads.json` (from `Desktop\flytxt lead fit\flytxt_leads_normalized.csv`, keyed by lowercased LinkedIn id). `_private/` is gitignored on both machines and copied by hand (scp) when the list changes.

mac-hub: `~/Desktop/AIOS/automations/mac-hub/jobs/flytxt_decks.py` (runpy of this poller), `schedule_table.py` line `flytxt_decks` every 21600 s, timeout 10800. After a schedule change restart the agent: `launchctl kickstart -k gui/$(id -u)/com.actiscale.macsched`.
