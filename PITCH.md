# Pitch, demo and outreach drafts

`{BRACES}` = fill from tonight's fresh run (`web/data/index.json`), never from memory. Quote only the fresh numbers, or the 8 Sep numbers with their date.

## Pitch video (2:45, founder on camera, own voice, burned-in captions)

**0:00–0:15, cold open.** Screen shows the Hyperliquid leaderboard, then cuts to the clone cloud at 0:04.
> "This is Hyperliquid's leaderboard. I took its top {N_ACC} traders and replayed every one of their trades at random times. Same coins. Same direction. Only the timing changed. {N_PASS_ACC} of them beat their own placebo."

**0:15–0:40, why me.** Face to camera.
> "I'm Fadly. I build trading analytics: AlphaLabs, used by traders in Indonesia. I reached Gold in the WorldQuant BRAIN challenge. This year I bred trading strategies with AI for forty-nine generations. The champion made twenty-two thousand dollars in backtests. On four and a half years of data it had never seen, it made ninety-seven dollars a year. So I built the test I wish I'd had."

Checked facts: $22,271 in-sample, $97/yr on the sealed Jun 2010–Dec 2014 holdout (4.5 years) (`propfirm-apex-champion-oos-holdout-and-forward-log.md`). Don't say "live". Say "paying users" only if the CRM shows paid users, not trials.

**0:40–1:10, the method in one picture.** One wallet's red curve inside the grey cloud.
> "Every red line is a real record. Every grey line is the same trades at random times. If red can't escape the grey, the profit came from which way the market went, not from when they traded."

**1:10–1:35, the result.**
> "{N_PASS_ACC} of {N_ACC} top accounts, and {N_PASS_V} of {N_V} of the biggest vaults, beat their placebo after correcting for testing that many. By chance alone you'd expect about five percent with a raw p-value under 0.05. We saw {RAW05}. The method was locked in a public pre-registration before I looked at the data."

**1:35–2:05, the product.** Screen recording.
> "Paste any address and get the verdict. The scores live in a registry on HyperEVM, so any contract can call `isSkilled` before it routes money to a vault or a copy-trading strategy. The lens reads the vault's live account value straight from HyperCore."

**2:05–2:20, traction.** Real counts only: thread views, DMs sent and replies, any quote used with consent.

**2:20–2:40, who pays.**
> "Copy-trading apps and vault platforms list traders by PnL, and PnL mostly measures the market. Placebo is a free open score, plus a paid API for custom tests. I'm doing this full-time."

**2:40–2:45.** The cloud again. "Same coins. Same direction. Random timing." Then the repo URL.

Never: "imagine a world", "revolutionize", a TAM slide, a roadmap grid, a music intro, going over 3:00.

## Technical demo (2:30, screen only, voice-over)

1. (0:00) Repo, then PREREGISTRATION.md and its commit time, before the results commit.
2. (0:20) `python score.py`: the self-check (planted edge found, random trader not), then the calibration line.
3. (0:45) The page: one passing address, one placebo address. Explain the clone cloud and the histogram.
4. (1:20) HyperEVM testnet explorer: the registry contract, a `push` transaction, then `cast call isSkilled(...)` and `getScore(...)`.
5. (1:50) The lens: a mainnet `eth_call` showing an account value and an oracle price read from HyperCore.
6. (2:15) Limits slide: hourly resolution, 24-hour horizon, exits not scored, and one keeper backed by the method hash.

## X thread (post Wed 7 Oct, after the gate passes)

1. I replayed the trades of Hyperliquid's top {N_ACC} traders at random times. Same coins, same direction, only the timing changed. {N_PASS_ACC} beat their own placebo. 🧵
2. Why: the leaderboard ranks PnL, and PnL is mostly which way the market went. On 8 Sep, with the market up 21%, the top fifth by profit was 93% long. The bottom fifth was net short.
3. The test: shift a trader's whole timeline to 1,000 random offsets. Coins, direction and rhythm are kept; only *when* moves. If the real record can't beat the clones, timing added nothing.
4. Calibrated: synthetic traders with no skill by construction pass at 0%. Method pre-registered before I looked at the data: https://github.com/cyberhooman/placebo/PREREGISTRATION.md
5. Paste any address: https://cyberhooman.github.io/placebo/. Scores are on HyperEVM, so a contract can check `isSkilled()` before it allocates.
6. Limits: hourly resolution, 24h horizon, exits not scored. Built solo for @colosseum's World's Fair, Hyperliquid track.

## Arena forum post (Tue 6 Oct, after the gate)

> **Placebo: does a Hyperliquid trader's timing beat a placebo of their own trades?**
> I replay each trader's own trades at 1,000 random offsets (same coins, direction and rhythm) and test whether the real record beats its clones. On the top {N_ACC} accounts by 30-day PnL: {N_PASS_ACC} pass after correction. The method was pre-registered first, scores are on HyperEVM testnet, and the code is open. I'd love one thing from anyone who runs a vault or a copy-trading product: does this match how you'd want traders judged? https://cyberhooman.github.io/placebo/

## DM to a vault leader whose vault passes (send only to passes)

> Hi, solo builder in Colosseum's Hyperliquid track. I built Placebo, an open test that replays a vault's own trades at random times to separate timing from market direction. {VAULT} is one of {N_PASS} addresses out of {N_TESTED} that beat their placebo after correction: https://cyberhooman.github.io/placebo/#{ADDR}. Does the method match how you'd want depositors to judge you? A one-line reply I could quote (with your OK) would mean a lot.
