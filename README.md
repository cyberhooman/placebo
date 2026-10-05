# Placebo — the luck test for Hyperliquid

**Did they trade well, or did the market move?**

Placebo replays a trader's own trades at random times: same coins, same direction, same number of decisions, same spacing between them. Only *when* changes. If the real record can't beat 1,000 of these clones, its profit came from the market's direction, not from timing.

Every account and vault on Hyperliquid is public, down to each fill, so the test can run on anyone. The scores are written to a registry on HyperEVM, where any contract can read `isSkilled(address)`.

## Result

Data: the top 500 Hyperliquid leaderboard accounts by 30-day PnL and the top 100 vaults by TVL, with the last 90 days of fills, pulled on 5 Oct 2026.

1. **Most of the leaderboard can't be judged.** 202 of the top 500 made fewer than 50 opening decisions in 90 days (median 57). That is too few to tell skill from luck.
2. **The month that ranked them was their luckiest.** For accounts testable in both periods, the median timing edge was **+31.6 bp per decision** in the 30-day window that put them on the leaderboard, against **+9.5 bp** in the two months before.
3. **Timing doesn't carry over.** Timing before and during that window is uncorrelated: Spearman rho = −0.09 (p = 0.31, n = 125).
4. **The biggest vaults look like chance.** None of the 52 testable top-100 vaults beats its placebo. 3.8% have p < 0.05, against the 5% chance alone gives. In median bp per decision, direction is +29.7 and timing is +11.8.

| Group | Tested | Beat their placebo (BH, q = 0.10) | p < 0.05 (chance: 5%) | Calibration: synthetic no-skill traders |
|---|---|---|---|---|
| Top-500 accounts, full 90 days | 216 | 4 (selection-biased window, see 2) | 10.6% | 0.5% pass, KS p = 0.48 |
| Top-500 accounts, before their leaderboard month | 178 | 6 (but calibration false-passes ≈ 4) | 12.4% | 2.2% pass, KS p = 0.76 |
| Top-100 vaults, full 90 days | 52 | **0** | 3.8% | 0.0% pass, KS p = 0.52 |

**How the method changed, all on record.** The method was fixed in [PREREGISTRATION.md](PREREGISTRATION.md) before any fresh data was scored.
- The first run showed that the pre-registered permutation p-value can never pass the Benjamini–Hochberg bar: its floor is 1/1001, and the bar is q/m = 0.00037.
- That run's "0 pass" therefore carried no information and is withdrawn, along with an earlier "0 of 377" on 8 Sep data.
- Amendment 1 (z-based p-values, and a split at the leaderboard window) was committed before the runs above.
- The raw output of all three runs is in [results/](results/).
- The pre-registered data gate (at least 300 testable addresses) failed: 268 were testable. That failure is reported, not hidden.

## How it works

1. **Decisions.** Every opening fill, maker or taker, is summed by signed notional per coin per hour. Each sum is one decision.
2. **Score.** The mean signed 24-hour forward log return, measured from the close of the decision's hour.
3. **Placebo.** The whole decision timeline is circularly shifted by 1,000 random offsets inside its own span. This keeps the trader's clustering and rhythm, which a plain shuffle would destroy and so make luck look like skill.
4. **Split.** *Direction* is what the clones earn on average. *Timing* is the real score minus direction.
5. **Verdict.** The one-sided p-value is the share of clones that did at least as well. Benjamini–Hochberg at q = 0.10 corrects across every address tested.
6. **Calibration.** The same test runs on synthetic traders with no timing skill by construction. They must pass at about 0%, with uniform p-values. They do.

The p-value is `1 − Φ(z)` with `z = (real − mean(clones)) / sd(clones)` (Amendment 1). The exact permutation p is kept beside it.

`python score.py` runs the self-check: a planted timing edge must be found, and a random trader must not be.

## On-chain (HyperEVM)

- `contracts/src/PlaceboRegistry.sol` stores per-address scores (`nEvents`, `realBps`, `directionBps`, `timingBps`, `pValueBps`, `passes`, `asOf`) plus `isSkilled(address)`. `methodHash` is the sha256 of `score.py`, so anyone can check which code produced the scores.
- `contracts/src/PlaceboLens.sol` joins a score with live HyperCore state through the read precompiles: account value (0x80F), position (0x800) and oracle price (0x807). It was checked read-only against mainnet: it returns HLP's account value and the live BTC oracle price.
- `keeper.py` pushes scores in batches of 50 (about 1.5M gas each, under the 3M small-block limit).
- **Live on HyperEVM mainnet (chain 999)**, verified on Sourcify (exact match):
  - `PlaceboRegistry` [`0xd540b8180b8d77c5b61ba73cded772e0cb8ea14a`](https://repo.sourcify.dev/999/0xd540b8180b8d77c5b61ba73cded772e0cb8ea14a): 268 scores, `passed()` = 4. Keeper `0xc695eD5fABCd6497d707280C0a8910c13C694996`.
  - `PlaceboLens` [`0xe1d70b4723aeedd94ad21f5034a783b4edf67607`](https://repo.sourcify.dev/999/0xe1d70b4723aeedd94ad21f5034a783b4edf67607): `check(vault, 0)` returns the vault's score next to its live HyperCore account value.
  - `methodHash()` = `0x2eb02253…a492b` = sha256 of `score.py` (LF line endings) at the commit that produced the scores.

## Run it

```
python pull.py            # population + 90 days of fills (public info API, rate-limited, ~3.5 h)
python score.py --fresh   # candles, placebo test, calibration, writes web/data/
python -m http.server -d web 8000
cd contracts && forge test
python keeper.py <registry address>
```

## Limits (read before quoting a result)

- Timing is measured at **hourly resolution over 24 hours**. Edge inside the hour, and exits, are not scored. A scalper's edge can be real and still invisible here.
- "Indistinguishable from placebo" is not "no skill". It means this test can't tell the record apart from its own clones.
- Hyperliquid serves only the 10,000 most recent fills per address, so very active addresses have a shorter history.
- Scores are pushed by one keeper. The method hash and this open code are what make them checkable.
- Placebo never labels an individual account as a "loser". It publishes counts, plus badges for addresses that pass.

## Prior work (disclosed)

The research question comes from the author's own Hyperliquid study of 8 Sep 2026 (600 accounts, 907,516 fills). It found that ranking wallets by PnL mostly sorts them by long vs short exposure: in a month the market rose 21%, the top quintile was 93.3% long and the bottom quintile was net short. It also found that entry timing doesn't persist out of sample. That study's analysis scripts are private. Everything in this repo was written during the Colosseum World's Fair (5–12 Oct 2026), and `replicate_sep8.py` re-runs the new method on that study's data.

MIT licence.
