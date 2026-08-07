# CCF — UI direction mockups

Three candidate looks for the Clutch Card Football pygame UI, rendered at the
game's real internal resolution (960×720) with real `GameSnapshot` data.

**No game logic is touched.** These are draw-only renderers. They import
`ccf.models`, `ccf.states` and `ccf.drive_chart` to read data and nothing else —
no state machine, no rules, no AI. Every rule, table and probability in
`ccf_pygame/ccf/` is untouched.

## Running

```bash
python3 mockups/render.py            # all themes, all states -> mockups/out/
python3 mockups/render.py neon       # just one theme
python3 mockups/sheet.py             # 2x2 contact sheet per theme
```

## The options

| | Direction | Character |
|---|---|---|
| **A** | `theme_broadcast.py` | Sports-TV. Full-width score bar, painted turf with hash marks, real playing-card faces, drive chart kept as its own reference rail. Closest to the current information layout. |
| **B** | `theme_minimal.py` | Quiet product UI. Field becomes an abstract progress track, heavy use of whitespace and type hierarchy, one accent colour. Drive chart is **folded onto the cards** — each card shows the segments it gains. |
| **C** | `theme_neon.py` | Modern evolution of the current arcade look. Deep indigo, neon cyan/magenta, glow instead of CRT scanlines. Drive chart becomes a horizontal strip under the field; cards also carry their yardage. |

## States rendered

Each theme is rendered in four states, chosen to exercise the whole layout:

1. **Choosing a card** — hand active, no play resolved yet
2. **Red-zone decision** — card battle resolved, all four action buttons live
3. **Touchdown / extra point** — the celebration state and the K / 2-point choice
4. **Full 9-card hand, on defense** — the layout stress test

State 4 matters: Q4 deals 8 cards on top of the leftover from Q3, so a hand can
reach **nine** cards. All three hand rails size their cards from the count so
this never overflows. State 4 also confirms the AI's offense card stays hidden
while you pick your defense, and that the mirrored (black-team) field renders
right-to-left.

## Fonts

`assets/fonts/` holds Inter and Barlow Condensed, both SIL Open Font License
(licences included). They are bundled rather than loaded from the system so the
look survives the pygbag/WASM build, where no system fonts exist.

## Turning a pick into the real UI

Mechanics live in `ccf_pygame/ccf/`; all presentation lives in `ccf_pygame/ui/`.
Adopting a direction means rewriting the `ui/` screens and retiring
`ui/crt_effect.py` — the `ccf/` package does not need to change at all.
