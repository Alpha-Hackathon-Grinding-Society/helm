# Demo script

The video is a **screen recording of the live system**. Nothing in it is a mock-up: every
number on screen was read from a testnet while the recording was running, and every
transaction hash it shows was opened on a public block explorer.

- **File:** [`helm-demo.mp4`](helm-demo.mp4) — 2.15 MB, 1280×720, H.264, **164.92 seconds (2 min 45 s)**
- **Live URL:** <https://helm-dashboard-six.vercel.app/helm-demo.mp4>
- **Recorded by:** [`scripts/demo-video.mjs`](../scripts/demo-video.mjs), committed so the
  video can be re-recorded rather than merely re-uploaded
- **Silent.** There is no narration: the video carries its argument in title cards and in
  the interface itself, and every caption is a sentence a judge can read without audio.
  (The build environment has no speech-synthesis engine, and the alternative — shipping a
  video with a synthetic voice reading numbers — was judged worse than no voice at all.)

## The timing the PRD asks for, and where it landed

The PRD's demo script is a three-minute plan: problem, set the course, steer, enforce,
proof, architecture. The recording follows that order exactly. The total is 2 min 45 s,
which leaves fifteen seconds of headroom under the three-minute limit.

| PRD section | PRD budget | In the video | What it shows |
| --- | --- | --- | --- |
| The problem | 0:00–0:20 | 0:00–0:21 | Title card, then the live dashboard's opening panel: the current split, the envelope, the last cycle. |
| Set the course | 0:20–0:45 | 0:21–0:39 | The envelope on `/policy`: LP share, range width, cooldown, volatility exit, minimum trade, freshness — and the fact that the agent is never told where they are. |
| Steer | 0:45–1:45 | 0:39–1:21 | The cycle log on `/cycles`, scrolled through: the model's split against the contract's answer, cycle by cycle, with the transaction hash for each leg. |
| Enforce | 1:45–2:15 | 1:21–1:51 | The Reactive transaction that clamped the proposal, on the Lasna block explorer, then back to the dashboard where the same cycle is shown. |
| Proof | 2:15–2:45 | 1:51–2:13 | The backtest on `/backtest`: Helm against `best rate now`, `static 50/50`, `all lending` and `all LP` — including the column where Helm loses. |
| Architecture and repo | 2:45–3:00 | 2:13–2:45 | Title card, then the public GitHub repository. |

## Shot by shot

Timings are read off the recording, not off the script that produced it.

| # | Time | Screen | What a judge is meant to take away |
| --- | --- | --- | --- |
| 1 | 0:00–0:04 | Title card: **Helm — The model proposes. The contract decides.** | The claim, in one line. |
| 2 | 0:04–0:08 | Title card lines: a neural network splits the vault; a reactive contract clamps every split; Lasna + Base Sepolia, both live | The mechanism, before any detail. |
| 3 | 0:08–0:21 | Dashboard home, live | The real system: current split (100% lending after the exit), the envelope, the last cycle id, the chain-read timestamp. |
| 4 | 0:21–0:25 | Title card: **1 · Set the course — The envelope you sign once.** | Section marker. |
| 5 | 0:25–0:39 | Dashboard `/policy` | The six limits, with what each one stops. The agent never learns where the limits are. |
| 6 | 0:39–0:43 | Title card: **2 · Steer — The loop, running on two chains** | Section marker. |
| 7 | 0:43–0:51 | Dashboard `/cycles`, top of the log | The shape of a cycle: trigger, proposal, check, callback, explanation. |
| 8 | 0:51–1:13 | `/cycles`, scrolled in seven steps | The cycle log itself: the model asks for 7102 bps, the contract says 4000, and the split bar shows the difference. Clamps are amber; refused proposals are red. Every row carries its transaction hashes. |
| 9 | 1:13–1:21 | `/cycles`, lower down | The economic veto and the autonomous exit: the two cases where the contract acts without the model. |
| 10 | 1:21–1:25 | Title card: **3 · Enforce — The proposal was clamped on-chain** | Section marker. |
| 11 | 1:25–1:37 | Lasna block explorer, transaction `0xebd2fb0a…` | The actual Reactive transaction. The model asked for 7102 bps; the envelope allowed 4000. This is the event, on chain, with a hash. |
| 12 | 1:37–1:51 | Back to `/cycles`, the same cycle | The same cycle in the log, next to the other 170-odd. |
| 13 | 1:51–1:55 | Title card: **4 · Proof — Out of sample, against the baselines** | Section marker. The number on this card is read out of `agent/models/metrics.json` when the video is recorded, so it cannot go stale. |
| 14 | 1:55–2:13 | Dashboard `/backtest` | The table. Helm −4.26%, `best rate now` −19.18%, `static 50/50` −5.68%, `all lending` +0.16%, `all LP` −11.52%. The page says plainly that Helm loses to doing nothing on this window, and why: the price fell 22.41%. |
| 15 | 2:13–2:17 | Title card: **5 · How it fits together — One contract decides. One vault holds the money.** | Section marker. |
| 16 | 2:17–2:28 | GitHub: the public repository | The code, the tests, the scripts, the docs. |
| 17 | 2:28–2:45 | GitHub, scrolled | The repository map. |

## Re-recording it

```bash
# a browser for Playwright
npx playwright install chromium

# record the raw capture
PLAYWRIGHT_MODULE=./node_modules/playwright-core \
  node scripts/demo-video.mjs --out /tmp/helm-demo.webm

# encode it
ffmpeg -i /tmp/helm-demo.webm -c:v libx264 -pix_fmt yuv420p -crf 23 -preset slow \
  -movflags +faststart docs/helm-demo.mp4
```

The recorder takes `--dashboard URL` if the dashboard moves, and `--width` / `--height`
for the capture size. It reads the clamp transaction hash from the constant at the top of
the script; change that one line to point at a different cycle.

## Why it is silent, and what would fix it

There is no speech-synthesis engine on the build machine (`espeak`, `espeak-ng`, `festival`
and `flite` are all absent), and no local text-to-speech model is installed. The fallback
would have been a recorded voice-over, which needs either the same engine or a paid
external service — and the paid external service was not available within the allowance
that was left. So the video carries its own argument in text.

If a voice is wanted later, the honest order of preference is: a real human narrating the
script above over the existing capture (the script is written to be read aloud, shot by
shot), then a local TTS. A silent video with title cards is a normal thing to submit; a
video with a synthetic voice reading out transaction hashes is not obviously better.
