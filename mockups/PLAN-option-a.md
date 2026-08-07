# Implementation plan — Option A "Broadcast" UI

Handoff document. Rewrites the Clutch Card Football presentation layer to the
Broadcast direction. **Game mechanics do not change.**

The reference implementation already exists: **`mockups/theme_broadcast.py`** is a
working, pixel-accurate renderer of the target design at the game's real
960×720. Treat it as the executable spec — most of this job is porting its draw
code into stateful widgets, adding interaction, and covering the phases the
mockup doesn't show. Reference renders are in `mockups/out/broadcast-*.png`.

---

## 0. Ground truth before you start

| Fact | Value |
|---|---|
| Repo | `sorangio/CodeDev`, remote `dad` |
| Branch | local `dad-pygame-ui` → `dad/scott/pygame-ui`, at `d27eced` |
| Second remote | `origin` → `norangio/clutch-card-football` — **unrelated history, no common ancestor** |
| Game logic | `ccf_pygame/ccf/` — **do not modify** |
| Presentation | `ccf_pygame/ui/` — everything you touch |
| Test gate | `cd ccf_pygame && python3 -m pytest test_ai.py -q` → 30 passed |
| Runtime | pygame-ce 2.5.x, Python 3.14, 960×720 internal, 30 FPS |

Run the mockups any time to compare against your build:

```bash
python3 mockups/render.py broadcast
```

### Read this before touching anything

`origin/main` and `dad/scott/pygame-ui` **share no commits**. They are separate
imports of the same project:

- `dad/scott/pygame-ui` (where you are) has the newer gameplay — `ccf/ai.py` is
  +309 lines over origin, `ccf/state_machine.py` +110/−64. It is **desktop only**:
  no `main.py`, no `ui/keycodes.py`, and `ui/app.py` has a blocking `run()` loop.
- `origin/main` has the browser/deploy pipeline that `dad`'s branch lacks:
  `ccf_pygame/main.py` (async pygbag entry), `ui/keycodes.py`, `deploy.sh`,
  `deploy/Caddyfile.snippet`, `deploy/clutch-card-football.service`, and an
  `ui/app.py` with `browser_mode` / `tick()` / `run_async()`.

`.claude/launch.json` runs `python -m pygbag … ccf_pygame`, which needs
`ccf_pygame/main.py`. **That file is not on this branch, so the web build is
currently broken here.** See §9 — this is a decision for the owner, not for you
to resolve unilaterally.

---

## 1. Non-negotiables

1. **Do not edit anything under `ccf_pygame/ccf/`.** No rules, tables,
   probabilities, phase transitions, or timings. If a UI need seems to require a
   logic change, stop and ask.
2. `python3 -m pytest test_ai.py -q` must still report **30 passed** at every
   commit.
3. **Preserve every input binding** (§6). Existing muscle memory is the baseline.
4. **Never reveal the AI's offense card during `WAITING_DEFENSE_CARD`.** The
   state machine deliberately logs `"AI plays card ..."` without the value
   (`state_machine.py:_ai_play_offense`). `snap.off_card` *is* populated in that
   phase — the UI must gate on `off_card and def_card`, never on `off_card`
   alone. The mockups already do this; keep it.
5. Every `GamePhase` must render something deliberate (§5). No blank panels.
6. The game must stay playable end-to-end with the mouse alone **and** with the
   keyboard alone.

---

## 2. Target file layout

```
ccf_pygame/ui/
  assets/fonts/
    Inter-Regular.ttf         NEW  (subset, see §8)
    Inter-SemiBold.ttf        NEW
    Inter-Bold.ttf            NEW
    BarlowCondensed-Bold.ttf  NEW
    OFL-Inter.txt             NEW
    OFL-BarlowCondensed.txt   NEW
    press_start_2p.ttf        DELETE (no longer referenced)
  theme.py        NEW     palette + spacing tokens        (replaces colors.py)
  fonts.py        NEW     AA font loader + tight text     (replaces font.py)
  draw.py         NEW     primitives, ported from mockups/lib/draw.py
  layout.py       NEW     all screen rects in one place
  app.py          EDIT    drop CRT, keep loop/dispatch
  colors.py       DELETE
  font.py         DELETE
  crt_effect.py   DELETE
  sounds.py       KEEP    unchanged
  screens/
    play_screen.py     REWRITE  composition + event routing
    score_bar.py       NEW      (replaces scoreboard.py)
    field_band.py      NEW      (replaces field_view.py)
    hand_rail.py       NEW      (replaces card_hand.py)
    play_panel.py      NEW      (replaces card_battle.py)
    log_panel.py       NEW      (replaces play_log.py)
    chart_rail.py      NEW      (replaces drive_chart_panel.py)
    action_bar.py      NEW      (replaces decision_panel.py)
    setup_screen.py    REWRITE
    game_over.py       REWRITE
    scoreboard.py / field_view.py / card_hand.py / card_battle.py /
    play_log.py / drive_chart_panel.py / decision_panel.py   DELETE
```

Port `mockups/lib/draw.py` to `ui/draw.py` **verbatim** apart from the caching
required by §7. It already carries two fixes you must not regress:

- `_render_text` measures tracked text from the same per-character advances it
  draws with. Measuring with the kerned whole-string width clips the last glyph.
- `glow()` draws expanding **rings**, not filled rects. Stacked fills build to an
  opaque slab that washes out whatever is painted inside afterwards.

---

## 3. Design tokens

Copy from `mockups/theme_broadcast.py` — these are the exact values in the
approved renders.

```python
BG        = (11, 14, 19)     PANEL     = (21, 26, 34)
PANEL_HI  = (29, 36, 47)     BORDER    = (46, 55, 69)
TEXT      = (234, 239, 246)  MUTED     = (140, 152, 170)
DIM       = (95, 106, 122)   GOLD      = (250, 204, 21)
RED       = (226, 62, 62)    SILVER    = (198, 208, 224)
GREEN_OK  = (52, 199, 123)   ORANGE    = (255, 138, 32)
FIELD_TOP = (30, 104, 51)    FIELD_BOT = (18, 68, 34)
ENDZONE   = (15, 52, 27)     CARD_FACE = (247, 248, 251)
CARD_INK  = (24, 28, 36)     CARD_RED  = (200, 40, 48)
BONUS = {"yellow": (240,200,60), "orange": (245,145,40), "green": (60,200,110)}
```

`team_color(team)` → `RED` if `team.color.value == "red"` else `SILVER`. The
BLACK team renders as light silver; pure black is illegible on this ground, and
the current build already makes the same substitution.

**Type scale.** Barlow Condensed Bold for display (team names, scores, segment
labels, button labels, big event text). Inter for everything else — Bold for
tracked micro-labels, SemiBold for values, Regular for log lines and body.
Always render antialiased. Use `tight=True` for anything you position by
`center` / `midleft` / `midright`: Inter and Barlow have very different leading,
and tight cropping is the only way optical centring holds across both.

---

## 4. Layout geometry

Put all of this in `ui/layout.py` as module constants. Values are exact.

```
W, H            = 960, 720
SCORE_H         = 104          score bar          (0,0,960,104)
FIELD_Y, FIELD_H= 104, 124     field band         (0,104,960,124)
BODY_Y          = 228
ACTION_H        = 84
ACTION_Y        = 636          action bar         (0,636,960,84)
BODY_H          = 408

RAIL_X, RAIL_W  = 14, 252      hand rail          (14,236,252,392)
CHART_W         = 176
CHART_X         = 770          chart rail         (770,236,176,392)
CEN_X, CEN_W    = 278, 480
                               play panel         (278,236,480,138)
                               log panel          (278,384,480,244)
```

Body panels inset 8px vertically from `BODY_Y` and are `BODY_H − 16` tall.
Panel radius 12, border 1px `BORDER`. Buttons radius 10.

**Score bar.** Team colour chip 5×40 at x=20 / x=W−25. Name Barlow Bold 34 and
score Inter Bold 36, both `tight`, vertically centred on y=33. `OFFENSE` pill
(Inter Bold 9, tracking 1, gold fill, ink `(26,22,6)`) at y=55 under the team on
offense. Centre pill 132×56 at y=10 holding `Q{n}` (Barlow Bold 32, gold) and
`PLAY {turn} / {turns}` (Inter SemiBold 10, tracking 1). Second row at cy=84:
clutch as 5 gold stars, mojo as 2 orange dots, both labelled; AI difficulty chip
centred, coloured green/gold/red for easy/medium/hard.

> Lay the pip rows out from measured widths, not fixed offsets — long team names
> and a 5-star clutch row collide otherwise. `_pips()` returns its right edge for
> exactly this reason; chain from it. The AI-side block is right-aligned from a
> precomputed total.

**Field band.** 8 segments across `pad=16`, `seg_w=(W−32)/8`, drawn between
`top=FIELD_Y+26` and `bot=FIELD_Y+FIELD_H−22`. Labels `["EZ","1","2","3","Z3",
"Z2","Z1","EZ"]`, zone names `["OWN G","OWN 1","OWN 2","OWN 3","RED","RED",
"RED","END ZONE"]`. **Reverse both lists when the offense is the BLACK team** so
"1" always sits by the offense's own goal — matches current `field_view.py`
behaviour. End zones get diagonal silver hatching at alpha 22; red-zone segments
are tinted `mix(FIELD_TOP, (150,40,40), 0.16)`. Quarter-segment hash marks top
and bottom at alpha 34.

Drive direction is shown by faint chevrons (alpha 20, 46px pitch) along the
midline **between the end zones only**, skipping a 46px radius around the ball.
Do not put a text overlay in the centre of the band — it collides with the
segment labels. The ball is a `football()` marker 54×32 with a drop shadow,
outlined in the offense's colour.

**Hand rail.** Two columns. Row height is derived from the card count:

```python
n     = max(1, len(hand))
rows  = (n + 1) // 2
gap   = 10
y0    = rect.y + 50
avail = (rect.bottom - 40) - y0
ch    = max(46, min(70, (avail - (rows - 1) * gap) // rows))
cw    = (rect.w - 32 - 12) // 2
```

Pass `scale=0.86` to the card face when `ch < 60`. **This is load-bearing:** Q4
deals 8 on top of the Q3 leftover, so a hand reaches **nine** cards. Fixed 70px
rows overflow the rail and collide with the footer.

Card face: white `CARD_FACE`, radius 8, rank Inter Bold 21 at top-left, vector
suit (`draw.suit`) size 30 at `(right−24, centery+6)`, index chip bottom-left.
Joker uses face `(253,246,214)` with `JOKER` in Barlow Bold. Selected card gets a
gold 3px ring inflated by 6 plus a drop shadow. Footer row: `OPPONENT` /
`{n} cards`.

**Chart rail.** Header `DRIVE CHART` + `RATING {n}` where n is
`snap.offense.rating` — the chart belongs to whoever has the ball, not to the
human. 13 rows in `["2".."10","J","Q","K","A"]` order, alternating row fill
`(26,32,42)`, rank left, `+base` right, bonus dot at `right−24` coloured from
`BONUS`.

**Action bar.** Gradient `PANEL → (14,18,24)`, 1px top border. Context line at
y+16 (Inter Bold 10, tracking 2). Buttons 42px tall at y+30, full width minus
20px margins, 12px gutters. Four buttons for post-move, two for extra point.
Disabled = fill `(18,22,29)`, border `(34,40,51)`, ink `(74,82,96)`. Primary =
gold fill with dark ink. Shortcut digit top-right of each button.

---

## 5. Phase → screen contract

Every `GamePhase` in `ccf/states.py`. "Play panel" is the 480×138 centre panel.

| Phase | Screen | Play panel | Action bar | Hand |
|---|---|---|---|---|
| `SETUP_TEAMS` | Setup | — | — | — |
| `QUARTER_START` | Play | `snap.message` banner | idle hint | inert |
| `WAITING_OFFENSE_CARD` | Play | "Pick your OFFENSE card" | `SELECT A CARD` + hint | **active** |
| `WAITING_DEFENSE_CARD` | Play | "Pick your DEFENSE card" | `SELECT A CARD` + hint | **active**, header reads `PICK DEFENSE` |
| `AI_PLAYING_CARD` | Play | "AI is thinking…" | idle | inert |
| `SHOWING_CARD_BATTLE` | Play | both cards + `VS` | idle | inert |
| `SHOWING_MOVEMENT` | Play | both cards + `+N SEGMENTS` badge | idle | inert |
| `SHOWING_TOUCHDOWN` | Play | `TOUCHDOWN` + `{team} +6` | idle | inert |
| `WAITING_EXTRA_POINT_CHOICE` | Play | `TOUCHDOWN` + `{team} +6` | **KICK PAT / GO FOR 2 · d6 ≥ 5** | inert |
| `SHOWING_EXTRA_POINTS` | Play | `extra_pts_desc` + `d6:[roll]` when `extra_pt_roll` | idle | inert |
| `SHOWING_SAFETY` | Play | `SAFETY!` treatment | idle | inert |
| `SHOWING_WAR` | Play | `snap.message` — **cards hidden** | idle | inert |
| `SHOWING_JOKER` | Play | `snap.message` + both cards | idle | inert |
| `WAITING_POST_MOVE` | Play | `Ball at {pos}` | **PUNT / FIELD GOAL / CLUTCH / SHORT PUNT** | inert |
| `AI_POST_MOVE` | Play | "AI choosing action…" | idle | inert |
| `SHOWING_PUNT` | Play | `snap.message` | idle | inert |
| `SHOWING_SHORT_PUNT` | Play | `snap.message` | idle | inert |
| `SHOWING_FIELD_GOAL` | Play | `snap.message` | idle | inert |
| `SHOWING_CLUTCH` | Play | `snap.message` | idle | inert |
| `WAITING_CONFIRM` | Play | `snap.message` + "click to continue" | idle | inert |
| `QUARTER_END` | Play | `snap.message` | idle | inert |
| `GAME_OVER` | Game over | — | — | — |

Notes:
- `SHOWING_WAR` hides the cards on purpose — the current build does the same
  (`play_screen.py` sets `show_cards = False` for that phase).
- Button enable state comes from `snap.can_punt` / `can_fg` / `can_clutch` /
  `can_short_punt`. Never compute availability yourself.
- The gold `FIELD GOAL` primary styling applies only when `snap.can_fg`.

---

## 6. Input map — preserve exactly

| Input | Phase | Effect |
|---|---|---|
| `0`–`9` | waiting for card | select + immediately play that index |
| `↑` / `↓` | waiting for card | move selection |
| `Enter` / `Space` | waiting for card | play selection |
| click a card | waiting for card | play that card |
| click elsewhere | waiting for card | `click_advance()` |
| `1`–`4` | `WAITING_POST_MOVE` | punt / FG / clutch / short punt, **only if enabled** |
| click a button | `WAITING_POST_MOVE` | same, only if enabled |
| `K` | `WAITING_EXTRA_POINT_CHOICE` | kick PAT |
| `2` | `WAITING_EXTRA_POINT_CHOICE` | two-point attempt |
| any key | showing phases | `click_advance()` |
| any click | showing phases | `click_advance()` |
| `Enter` | `GAME_OVER` | play again |
| `Tab` / arrows / `Enter` | `SETUP_TEAMS` | navigate / edit / start |

**Derive hit-testing from the same constants you draw with.** The current
`card_hand.py` does not, and it is broken: `draw()` starts rows at `y+36` while
`handle_click()` maps from `y+45`, a 9px shift that makes the top sliver of each
card select the card above it — and the top of card 0 select nothing, falling
through to `click_advance()` and advancing the game instead. The new `HandRail`
must compute card rects once into `self._card_rects` and have both `draw()` and
`handle_click()` use that list.

Also fix the second half of that bug: `play_screen.py` builds its hand hit-rect
as `H − SCORE_H` (648px) tall while the rail is only drawn `HAND_H` (400px)
tall, so clicks in the chart area still enter the hand hit-test. Hit-test
against the real panel rect from `layout.py`.

---

## 7. Performance — read before porting

The mockups render **once**. The game renders **30×/second in WASM**. Ported
naively, these helpers will tank the frame rate:

- `grad_rect()` builds a gradient pixel-by-pixel with `set_at`, then
  `smoothscale`s it. Currently called every frame for the score bar (104 rows),
  the field band (124 rows) and the action bar.
- `shadow()` and `glow()` allocate a surface and stack 10–20 rounded rects per
  call.
- The field's end-zone hatching, hash marks and chevrons are dozens of line
  draws per frame that only change when the drive direction flips.

Required:

1. **Memoise gradients.** Cache `_gradient()` on `(size, c_top, c_bottom, vertical)`.
2. **Memoise shadow/glow.** Cache on `(size, radius, spread, alpha, colour)` and
   blit the cached surface.
3. **Pre-render static layers.** Build the field band (turf, hatching, hash
   marks, chevrons, labels, zone names) into one cached `Surface` keyed on
   `mirror`. Blit it, then draw only the ball on top. Do the same for the chart
   rail keyed on `(rating, mirror)` — it only changes on possession change.
4. Budget: a full `draw()` must stay under ~8ms on desktop. Measure with
   `pygame.time.get_ticks()` around `play_screen.draw()` before you call it done.

---

## 8. Fonts

Sources are already vendored at `mockups/assets/fonts/` (Inter + Barlow
Condensed, both SIL OFL, licence files included). Copy the four faces you need
into `ccf_pygame/ui/assets/fonts/` **with the two OFL files** — the licences must
ship alongside the fonts.

Full-fat those four faces are ~1.3MB, which is a lot to push through a WASM
download. Subset them to the glyphs the UI actually uses:

```bash
pip install fonttools brotli
pyftsubset Inter-Regular.ttf --output-file=Inter-Regular.subset.ttf \
  --unicodes=U+0020-007E,U+00B7,U+2013,U+2014,U+2191,U+2192,U+2193,U+2265 \
  --layout-features='' --no-hinting
```

That range covers ASCII plus the `·`, `–`, `—`, `↑`, `→`, `↓`, `≥` used in
labels and hints. Expect ~20–40KB per face. Verify no tofu boxes appear in any
of the four reference states before committing the subsets.

Suit symbols are **drawn as vectors** (`draw.suit`), not typeset, so no font
needs U+2660–2663. Keep it that way — it stays crisp at the 15–30px sizes the
hand uses and removes a font-coverage dependency.

`fonts.py` must render antialiased. The old `font.py` forced `antialias=False`
for the pixel font; that setting will make Inter look broken.

---

## 9. Decision required — web build

Blocking for Task 9 only; Tasks 1–8 are unaffected. **Ask the owner, do not pick.**

The browser entry point (`main.py`), `ui/keycodes.py` and the `browser_mode` /
`tick()` / `run_async()` variant of `app.py` live on `origin/main`, which shares
no history with this branch. Options:

- **(a) Desktop only for now.** Build Option A here, ship `python3 game.py`,
  leave `ccf.norangio.dev` on the old build. Cheapest; the deployed site drifts
  further from the real game.
- **(b) Port the browser shell onto this branch.** Copy `main.py`,
  `ui/keycodes.py`, `deploy.sh` and `deploy/` from `origin/main`, and give the
  new `app.py` the `browser_mode` / `tick()` / `run_async()` API `main.py`
  expects. Adds maybe a day; gets the new UI deployed.
- **(c) Reconcile the histories first.** Bring dad's gameplay (`ccf/ai.py`
  +309 lines, `ccf/state_machine.py` +110/−64, `ccf/models.py` +4) onto
  `origin/main` as a graft, then do the UI there. Cleanest long-term, largest
  up-front cost, and it touches `ccf/` — so it must not be bundled into the UI
  work.

If (b) or (c): a blocking `while` loop will not run under WASM. The loop body
must be reachable as a single `tick()` that `main.py` can `await` between.
Structure `app.py` that way from Task 1 regardless of the decision — it costs
nothing now and avoids a rewrite later.

---

## 10. Task breakdown

Each task is one commit. Conventional commits, subject under 72 chars.

### Task 1 — foundation
Add `ui/theme.py`, `ui/fonts.py`, `ui/draw.py`, `ui/layout.py`. Copy fonts +
licences into `ui/assets/fonts/`. Port `draw.py` from `mockups/lib/draw.py` with
the §7 caching. Restructure `app.py` so the per-frame body is a `tick()` method
called by `run()`. Do not delete anything yet.
**Accept:** game still runs unchanged; 30 tests pass.

### Task 2 — score bar + field band
`screens/score_bar.py`, `screens/field_band.py`. Wire into `play_screen.py`
alongside the old widgets, replacing only these two regions.
**Accept:** matches `broadcast-2-redzone.png` top 228px; BLACK-team possession
mirrors the field (compare `broadcast-4-fullhand.png`); field band is a cached
surface.

### Task 3 — hand rail
`screens/hand_rail.py` with count-derived sizing and shared draw/hit-test rects.
**Accept:** 1–9 cards all fit without overflow or footer collision; clicking any
pixel of a card plays *that* card; `0`–`9`, arrows, Enter/Space all work;
matches `broadcast-1-select.png` and `broadcast-4-fullhand.png`.

### Task 4 — play panel + log panel
`screens/play_panel.py`, `screens/log_panel.py`. Implement the full §5 table.
**Accept:** every phase in §5 renders its specified content; the AI's offense
card is never visible during `WAITING_DEFENSE_CARD`; log colour-codes quarter
markers, touchdowns, and clutch/mojo lines.

### Task 5 — chart rail + action bar
`screens/chart_rail.py`, `screens/action_bar.py`.
**Accept:** rating tracks `snap.offense.rating` across possession changes;
enable states honour the `can_*` flags; `1`–`4` and `K`/`2` bindings work;
matches `broadcast-2-redzone.png` and `broadcast-3-touchdown.png`.

### Task 6 — retire the old UI
Delete `colors.py`, `font.py`, `crt_effect.py`, `press_start_2p.ttf` and the
seven superseded screen modules. Remove the CRT call from `app.py`.
**Accept:** no imports of deleted modules remain (`grep -rn "crt_effect\|ui.colors\|ui.font" ccf_pygame`); game runs clean.

### Task 7 — setup screen
Not mocked — build to spec. Same ground and panel language. Centred 560px
column on `BG`; title in Barlow Bold 42 gold; the 11 existing fields
(`setup_screen.py`) as labelled rows 44px apart, label left in Inter SemiBold 13
`MUTED`, value right in Inter Bold 15 `TEXT`; int/choice fields get `‹ ›` chevron
hit-targets; selected row gets a 1px gold border and `PANEL_HI` fill; gold
`START GAME` button 220×48 below. Keep every field, range and default exactly as
they are, and keep Tab/arrow/Enter navigation.
**Accept:** produces a `provide_setup()` payload identical to today's for the
same inputs; mouse-only and keyboard-only both reach START.

### Task 8 — game over screen
Not mocked — build to spec. `GAME OVER` in Barlow Bold 48 `MUTED` at y=80; the
result line in Barlow Bold 56, gold on a human win, red on a loss, `TEXT` on a
tie; both final scores as team blocks reusing the score-bar treatment; the stats
table (`SEGMENTS`, `FG made/att + %`, `PUNTS`) in a 520×160 panel with a column
per team; gold `PLAY AGAIN` button 240×48. Preserve the `(AI)` suffix in
`ai_vs_ai` mode and the Enter binding.
**Accept:** all stats present and correct; play-again restarts cleanly.

### Task 9 — web build
Only after §9 is decided. If (a), skip and note it in `README.md`.

### Task 10 — docs
Update `ccf_pygame/README.md` (screenshots, controls, font credits) and the
project doc — see §12.

---

## 11. Verification checklist

Before calling it done:

- [ ] `cd ccf_pygame && python3 -m pytest test_ai.py -q` → 30 passed
- [ ] `git diff --stat dad/scott/pygame-ui -- ccf_pygame/ccf/` is **empty**
- [ ] Full game, Q1→Q4, human vs AI, mouse only
- [ ] Full game, keyboard only
- [ ] AI vs AI mode runs to completion without input
- [ ] Each of the three difficulties starts and plays
- [ ] Both team colours as the human — field mirrors correctly for BLACK
- [ ] Observed at least once each: WAR, Joker offense, Joker defense, safety,
      field goal good, field goal missed, punt, short punt, clutch, 2-pt attempt
- [ ] 9-card hand rendered without overflow (reach Q4 with a card in hand)
- [ ] AI offense card stays hidden while picking defense
- [ ] Sounds still fire: first down, touchdown, field goal, win
- [ ] `play_screen.draw()` under ~8ms
- [ ] No tofu boxes anywhere after font subsetting

---

## 12. Housekeeping found along the way

Not part of this work — flag, don't silently fix:

- `claude.md` is a **broken symlink** to a nonexistent `AGENTS.md`, and
  `.gitignore` excludes `CLAUDE.md`. The workspace convention is a real
  `CLAUDE.md` with `AGENTS.md` as the symlink to it. Ask the owner before
  restructuring — this is dad's repo.
- `ccf_pygame/build/` is stale local pygbag output from 2026-03-18, built from
  the *other* history — it contains `main.py` and `ui/keycodes.py`, which do not
  exist in this source tree. It is correctly gitignored, but it will mislead
  anyone who greps it for "current" code. Delete it locally before you start.
