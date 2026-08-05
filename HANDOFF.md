# Sudoku Race — handoff

Head-to-head Sudoku prototype. Two players get the identical board; first to fill
it wins. Single-player races a simulated "ghost"; multiplayer is real, over a
WebSocket room server.

**Files** (that's all of them):

| File | What it is |
|---|---|
| `index.html` | The entire game — markup, CSS, JS, board data. ~99 KB, self-contained, no dependencies, no build step. |
| `server.py` | WebSocket room server. Pure relay: owns room codes, pairs players, picks the board index. Knows nothing about sudoku. |
| `requirements.txt` | `websockets>=13` — the server's only dependency. |
| `.gitignore` | Excludes `.claude/`, `__pycache__/`. |

Repo: `github.com/maksimacimovic/Sudoku-Race`, branch `main`.
Deployed server: `wss://sudoku-race-qgwr.onrender.com` (Render free tier).

---

## How to run it

**Fully local (no accounts, no internet).** Two terminals:

```
py -3 C:\Users\korisnik\Sudoku_PvP\server.py
py -3 -m http.server 8000 --directory C:\Users\korisnik\Sudoku_PvP
```

Then on any phone on the same Wi-Fi: `http://<PC-LAN-IP>:8000/index.html`
(was `192.168.2.199` at time of writing — re-check with `ipconfig`, it can change
on lease renewal).

Windows Firewall prompts on first run of each. **Allow on Private networks** or
the PC answers locally but phones get nothing.

**`SERVER_URL` resolves itself** from the page's origin, so nothing needs editing
between local and hosted:

| Page served from | Connects to |
|---|---|
| `file://` | `ws://127.0.0.1:8787` |
| `localhost`, `192.168.x`, `10.x`, `172.16–31.x` | `ws://<same host>:8787` |
| anything else | `DEPLOYED_SERVER` (the Render `wss://` URL) |

The private-range regex deliberately excludes public `172.x` (e.g. `172.5.5.5`
falls through to Render). A page on `https` **must** use `wss://` — a hardcoded
`ws://` gets blocked as mixed content, which is why this is origin-derived.

**Netlify is not currently wired up.** The owner burned credits on it and moved to
local hosting. If you reconnect it, note that a **drag-and-drop Netlify site never
auto-updates from GitHub** — that was the cause of a "why are there no changes"
episode. Link the repo (build command empty, publish directory `.`) so pushes
deploy themselves.

---

## Session changelog, in order

Each is one commit; `git log --reverse` matches this list.

1. `9eb3d59` Initial commit of the existing prototype plus the new room server.
2. `9a2e9d9` Pointed the client at the deployed Render server; made server logs
   flush so Render's log tab actually shows room events.
3. `b46d668` **PvP progress fix.** Symptom: "enemy is not moving". Cause was not
   networking — the opponent's real position was being filtered through
   `opponentDisplay()`, the deceptive bar built for the ghost. Multiplayer now
   draws the opponent's true progress; solo keeps the deception.
4. `971d7d7` Rails advance per correct cell (was 3-cell notches). Solo ghost
   stays notched so it can't creep alongside you.
5. `db8eeca` **Rail rebuilt as a tug-of-war** per an updated design doc: portrait ·
   bar · portrait, your teal filling rightward, their red leftward, crown at the
   centre as the finish. Pins and travelling markers gone.
6. `cf7cad6` Breathing room between bar and board (gap was 2px).
7. `e541009` **Lives ON.** Hearts per side, 3 / 2 / 1 by difficulty, elimination on
   the last heart.
8. `b9b5076` Emotes button added to the action row (placeholder).
9. `bbcda09` Emotes implemented: press-and-hold picker, emote lands on the bar,
   relayed in PvP. Added `emote` to the server's relay set.
10. `49ec787` Four action buttons spread evenly; emoji tiles shrink on narrow screens.
11. `55f9a54` Emotes: cooldown removed, usable during a lockout.
12. `06b475b` Bar spans the full board width; hearts moved above the portraits.
13. `ec30909` Emotes ride each player's position on the bar rather than its ends.
14. `2ef9094` Portraits enlarged to 96px; board height budget now allows for
    `env(safe-area-inset-bottom)`.
15. `3158a17` Portraits scaled back to 64px (96 was too big); short screens
    restored to their previous board sizes exactly.
16. `7f34bcc` Cells-remaining counter beside each portrait, ticking as it drops.
17. `fade75f` Auto-complete button moved between the counters; **ghost made more
    human** (accelerates, occasional long pause, cautious when low on hearts).
18. `e314674` **Number-first input** with the `NF` header toggle and armed-digit dash.
19. `c9036be` Placing a digit clears that candidate from all 20 peer notes; undo
    restores exactly the ones it swept.
20. `ce59e16` Crown enlarged with a 1s cartoon hop on a win; **losing reveals the
    remaining cells in red** before the results.
21. `fc6133d` Hearts and name aligned to the portrait rather than the wider column.
22. `300e596` Solo-only **Auto win / Auto lose** shortcuts in the debug panel.
23. `6698610` Those shortcuts close the debug panel first so the ending is visible.
24. `a018f7d` Portraits to 100px, name tight to the bar, hearts sized to the
    portrait width.
25. `2bbabc6` **Pre-match stare-off** — avatars, names, W·L records, difficulty,
    3-2-1. Solo shows it too. Records persisted; server relays the opponent's.
26. `e0ad906` Your own portrait no longer pops on every correct digit.
27. `5f4bcee` **End screen** — full-screen with a fade/lift transition, crowned and
    glowing winner, four actions.
28. `2a65012` Dropped the flavour caption under "You win!".
29. `6d4cb3d` Stat table: labels centred, your figures left, theirs right,
    colour-matched to the sides.
30. `e2c61ac` `SERVER_URL` resolved from the page's origin.

---

## Decisions made without being asked

These weren't specified. Each is a judgement call you may want to revisit.

**Multiplayer shows the opponent's true progress; solo keeps the lie.**
`opponentDisplay()` gates the ghost to 25/50/75/90% milestones and clamps it to
never appear more than 12pp ahead of you. Against a scripted ghost that's the
whole point. Against a real person it made them look frozen. Solo keeps it
untouched; `paintRail()` branches on `game.mode`.

**The cells-remaining counter is derived from *shown* progress, not truth.**
Critical: if it used the ghost's real count it would leak the entire deception —
the bar would say "barely moved" while the number said "18 left". In solo the
number is deliberately a plausible fiction consistent with the bar. In
multiplayer it's exact.

**The solo ghost's W·L record is the mirror of yours.** Its wins are your losses.
That is literally true and avoids inventing an opponent history.

**The ghost plays more carefully when low on hearts** (mistake rate × 0.35 on its
last heart). Without this, hard mode gives the ghost 1 heart and a flat 1% error
rate over ~55 cells — it eliminated *itself* about 42% of the time, making hard
accidentally the easiest tier. Now ~16%.

**Number-first persists across boards** while Notes resets per board. NF is an
input-method preference; having it reset every rematch would be irritating.

**The "Board" button on the end screen** shows the finished grid with a floating
"Results" pill to return. Nothing specified what it should do.

**Emote set** is `😠 🤩 😮 😢 😅` — my read of the reference image's emotional
range, minus a middle finger that was in it. One array at the top of the emote
code.

**A plain win has no caption**, but losses and unusual wins keep their reason
("You ran out of hearts", "X left the match") because those can't be inferred
from the title.

**The counter font is capped at 26px.** It scales off `--av`, and at a 100px
portrait it computed to 34px — larger than the board's own 22px digits, making
the counter the loudest thing on screen.

**Rematch takes a new board** from the rotation rather than replaying the same
puzzle. The old "same board" option was dropped when four buttons replaced three.

---

## Asked for, but done differently

**"Lives are OFF"** was the original spec; lives were later turned ON with the
hearts request. The lockout is no longer the only penalty.

**"55 seconds red X"** on a mistake — read as 5 seconds, and implemented as *the
lockout duration* rather than a hardcoded number, so it always ends exactly when
input unlocks and follows the debug slider. Never confirmed.

**"Keep playing after you lose" was removed.** Earlier you asked for no popup on
losing and an "Auto complete" button so you could keep solving. The later
"losing reveals the board in red, then the popup" request supersedes it: the
board auto-completes, so the button had nothing to do and was deleted. If you
want the option back it needs a "reveal now / keep playing" choice.

**`stepGhost()`, `startLockout()` and the mistake branch were on a "do not touch"
list** and have since been modified — with your instruction each time (counters,
then the more-human ghost). `opponentDisplay()`, `endLockout()`,
`applyLockoutMask()`, the `cfg` literal and all nine slider defaults are still
untouched.

**The "Analysis" button is inert.** A `TODO(analysis)` placeholder — you said
you'd trim buttons after seeing them.

**The settings gear is inert** by request — a placeholder for a real settings screen.

**Emotes have no rate limit at all**, client or server, by explicit request. One
player can flood the other's screen as fast as their finger moves.

**Avatars/crown are inline SVG, not the design's PNGs.** Embedding them as base64
would bloat the file; referencing them would break single-file self-containment.
Swapping in `<img>` tags is a two-line change.

**The lockout blur is not the design's mechanism.** The design specifies per-cell
sharp regions (outer ring + two boxes, rest blurred 3.4px at 50% opacity). The
implementation is a single radial-gradient blur blocker, tuned across several
rounds, with `blur`/`coverage` sliders. Switching to the design's version would
discard that tuning and make those two sliders meaningless.

---

## Traps for a fresh reader

**`--chrome` is a hand-maintained magic number and it will bite you.** The board
sizes itself from what's left over:

```
--board: min(369px, calc(100vw - 24px),
             calc(100dvh - var(--chrome) - env(safe-area-inset-bottom)))
```

`--chrome` must equal the summed height of *everything that isn't the board*
(header + rail + gap + pad + actions + wrap padding). **Change any of those and
the number is silently wrong** — too small and the page scrolls, too large and
the board is needlessly cramped. It caused real scroll bugs at least four times
this session (44px, 12px, 10px, 12px). Current values: **417** default, **342**
under `max-height:750px`. Re-measure from the DOM rather than doing arithmetic;
the numbers in the comments are actual measurements plus 2px slack.

**Animating `transform` on a centred element replaces its centring.** Bit us
twice, hard. `.pin` used `translateX(-50%)`; a keyframe of plain `scale()`
dropped it and shunted the element 21px sideways for the animation's duration,
then snapped back — reported as "laggy". **Every keyframe on a transform-centred
element must repeat the translate.** See `srCrownWin` and `srAvPop`. Conversely,
`.portrait` is a normal flex child now, so its pop is a plain `scale()` — the
design file still has `translateX(-50%)` in its `srPop` keyframes, which would be
wrong here.

**`[hidden]{display:none !important}` is load-bearing.** Author `display:flex`
rules beat the UA's `[hidden]` rule, so `hidden` silently did nothing on flex
containers and two rows rendered at once. The `!important` reset near the top of
the CSS is what makes `hidden` reliable.

**Specificity: `.btn` is defined after most component classes.** A single-class
rule like `.autobtn` loses to `.btn` on equal specificity. The button sizing
silently did nothing until it was scoped to `.railtop .autobtn`.

**Media query order matters for `--av`.** The `max-width:360px` override must come
*after* `max-height:750px`, because a small phone matches both and the later rule
wins. They're adjacent in the file with a comment saying so — don't reorder.

**Elements are drawn from state every frame.** `loop()` runs `paintRail()` and
`paintPenalties()` on every animation frame. Two consequences: (a) reading a
rect immediately after setting state gives you the *previous* frame's value, and
(b) CSS transitions mean rects are often mid-flight. Several apparent bugs during
testing were just this. Compare the underlying percentages, not pixels.

**Once a race ends, the loop stops painting.** `if(!S.over)` gates everything. So
anything that must reflect the final state has to be called explicitly from the
end path — `paintRail()`, `clearPenalties()`, `syncDevButtons()` are all invoked
from `showResults()`/`playerFinished()` for exactly this reason. A winning move
once froze the bar one notch short because of this.

**The ghost's stats are derived by observation, not instrumentation.**
`stepGhost()` was off-limits, so `loop()` watches `S.ghostLockUntil` for changes
to count the ghost's mistakes, lockouts and locked time. The comparison is
`!==`, not `>`: lowering the lockout slider can make a *newer* lockout end
*sooner* than the previous one, and a `>` test silently skipped those. The same
bug existed in my own shake trigger — that one compares `S.lockStart`, which only
ever moves forward, because `S.lockUntil` gets zeroed on expiry.

**`S.notes` is an array of 81 `Set`s, not arrays.** History entries store spread
copies (`[...set]`) and rebuild with `new Set(...)`.

**`renderCell()` always rewrites the note glyphs**, even when hiding them.
Skipping the rewrite left stale digits inside hidden containers — invisible, but
the DOM asserted something untrue and it made a real bug hard to read.

**The server relays unknown fields verbatim.** That's exploited twice: `failed:
true` rides along on `finished` to signal elimination, and `record` rides on
`create`/`join`. Adding a message *type* needs a server change (`RELAYED` set);
adding a *field* to an existing type does not.

**Closing a socket can tear down the session that replaced it.** `net.open()`
guards with `if(net.ws !== ws) return` in the close handler. Without it, an old
socket finishing its handshake flipped `game.mode` back to `'solo'` mid-match.

---

## Known bugs and rough edges

**Nothing is known to be broken.** Everything below is a rough edge.

- **`--chrome` drift** is the biggest structural liability. See above. A
  `ResizeObserver` that measured the chrome and set `--board` in JS would remove
  the whole class of bug; I kept it in CSS to preserve the pure-CSS geometry.
- **The board shrinks a lot on short screens.** 393×852 keeps the design's 369px,
  but 375×667 gets ~325px and 320×568 ~226px (≈25px cells). The rail is tall now
  — hearts, 100px portraits, names, bar. Trimming the name labels or putting
  hearts beside the portraits would buy the most back.
- **`hideResult()` is used as "dismiss" in places where the game isn't over.**
  Works, but the naming invites confusion with the end screen's transition state.
- **`opDisplay` in `S` is dead** (1 occurrence — its own initialiser). Leftover
  from the original prototype.
- **`rematchAsk` is undocumented** in `server.py`'s protocol comment, though it's
  sent and handled.
- **The stat table's header row is arguably redundant** now that names sit above
  with the portraits and the columns are colour-coded. Removing it would tighten
  the end screen by ~30px.
- **`.claude/` and `__pycache__/` are gitignored but `server.py` is public.** If
  the frontend is ever served from the repo root, `server.py` and
  `requirements.txt` are fetchable. No secrets in them; cosmetic only.
- **Render free tier sleeps** after ~15 min idle, so the first multiplayer match
  after a quiet spell waits ~30s. A player who taps Create and gives up early
  sees "Could not reach the server"; retrying works.
- **Rooms live in server memory.** Any redeploy or restart drops matches in
  progress.
- **The rematch flow costs 3 seconds** now that the stare-off runs on rematches
  too. Deliberate, for consistency, but it may feel slow when iterating.
- **A cheater can read the solution.** The client derives it locally, so it's in
  memory. Fine for friendly testing; if it ever matters, the server has to hold
  the solution and validate moves.
- **The rival's portrait still pops** on their every placement in PvP. Yours was
  removed as distracting; theirs may be too.
- **Undo/erase make the cells-remaining counter go up.** You described it as
  "only goes down"; it tracks actual cells filled, so reversing a move must
  reverse the count. It does so silently (the tick animation only fires on a drop).
- **Erasing a placed digit doesn't restore peer candidates.** Conventional
  behaviour — re-deriving them would mean guessing what you'd pencilled. Undo
  *does* restore them, because that's a true inverse.

---

## Half-finished

**Analysis screen — not started.** Button exists on the end screen, wired to an
empty handler with `TODO(analysis)`. Intended as a per-move review: where the time
went, which cells cost the mistakes. All the raw material is already tracked
(`mistakes`, `lockouts`, `totalLockoutMs`, and their ghost equivalents), but there
is no per-move history — `S.history` is an undo stack, not a timeline, and it gets
consumed by undo.

**Settings screen — not started.** Gear button is an inert placeholder.

**Multiplayer difficulty is host-only in principle but not enforced.** A joining
client's local difficulty pick is ignored — the server hands out the host's. There
is a `TODO(multiplayer)` on the picker noting a joiner should take what the server
gives it. Currently harmless because `begin` overwrites `game.difficulty`.

**Rematch agreement exists but is lightly tested.** `rematchWait` / `rematchAsk`
round-trip works in the protocol suite; the *UI* path of two humans both pressing
Rematch on real devices has not been exercised.

**Analytics counters exist but nothing consumes them** beyond the end screen.
They were added "for the results screen and analytics later".

---

## Verification state

- **Board pools**: all 30 puzzles (10 per difficulty) verified — 81 chars, digits
  only, no conflicting givens, **exactly one solution each**, no duplicates.
  Blanks: easy 41–47, medium 42–50, hard 52–57. Easy and medium overlap
  substantially; hard is cleanly separated.
- **Protocol suite against the local server**: 18/18.
- **Against the deployed Render server**: 10/10, plus 4/4 on emote relay and 4/4
  on record exchange (including sanitising `"not-a-record"` and `{w:-5,l:"x"}`).
  Relay round-trip ≈190 ms.
- **Real two-client PvP verified end to end**: identical board, names crossed,
  progress and lockouts relayed both ways, finish with stats, forfeit on
  disconnect.
- **Rotation**: 1000 draws per pool — zero immediate repeats, every board once per
  cycle of 10, even distribution.
- **Layout**: zero page scroll at 393×852, 375×667 and 320×568, with every
  transient element (auto-complete button, debug panel, emote row) shown.

Caveat: **the browser preview used for testing was unreliable.** It frequently
refused to re-execute `file://` documents, so stale JS state persisted across
"reloads" and produced several false failures; taking a screenshot sometimes
perturbed page state (it once activated a Rematch button mid-assertion). Findings
here come from DOM assertions re-run in clean states. Anything surprising is worth
re-checking on a real device before believing it.

---

## TODOs

In the code:

- `index.html:1871` — `TODO(multiplayer)`: difficulty should come from the server
  for a joining client.
- `index.html:2099` — `TODO(analysis)`: build the per-move review screen.

Not in the code, but outstanding:

1. **Decide the Analysis screen's content**, or remove the button.
2. **Trim the end-screen buttons** — you said "then we will remove buttons".
3. **Reconnect or abandon Netlify.** Local hosting works; Render still serves
   multiplayer across networks.
4. **Consider replacing `--chrome`** with a measured value set from JS.
5. **Add a difficulty picker to single player** — solo uses whatever was last
   selected on the multiplayer screen, defaulting to easy.
6. **Decide whether the rival's portrait pop stays.**
7. **Document `rematchAsk`** in the server's protocol comment.
8. **Remove dead `opDisplay`** from `S`.
9. **Consider gating the debug button** behind `?debug=1` so testers can't reach
   it — the panel is a fixed overlay and can't break the layout, but the sliders
   can make the game unplayable.
10. **Server-side rate limiting** if this ever goes beyond friends (emotes are
    unlimited by design; nothing validates move legality).
