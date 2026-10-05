# Placebo — the luck test for Hyperliquid

**Did they trade well, or did the market move?**

Placebo replays a trader's own trades at random times: same coins, same direction, same number of decisions, same spacing between them. Only *when* changes. If the real record can't beat 1,000 of these clones, its profit came from the market's direction, not from timing.

Every account and vault on Hyperliquid is public, down to each fill, so the test can run on anyone. The scores are written to a registry on HyperEVM, where any contract can read `isSkilled(address)`.

## Result

| Run | Addresses tested | Beat their placebo (BH, q = 0.10) | Raw p < 0.05 (chance: 5%) | Calibration (synthetic no-skill traders) |
|---|---|---|---|---|
| 8 Sep 2026 archive sample, 600 accounts across 10 volume deciles | 377 | **0** | 8.0% | 0% pass, KS p = 0.60 |
| 5 Oct 2026: top 500 leaderboard accounts by 30-day PnL + top 100 vaults by TVL | *running* | | | |

The method was fixed in [PREREGISTRATION.md](PREREGISTRATION.md) and committed before the 5 Oct data was scored. The git history shows the order.

## How it works

1. **Decisions.** Every opening fill, maker or taker, is summed by signed notional per coin per hour. Each sum is one decision.
2. **Score.** The mean signed 24-hour forward log return, measured from the close of the decision's hour.
3. **Placebo.** The whole decision timeline is circularly shifted by 1,000 random offsets inside its own span. This keeps the trader's clustering and rhythm, which a plain shuffle would destroy and so make luck look like skill.
4. **Split.** *Direction* is what the clones earn on average. *Timing* is the real score minus direction.
5. **Verdict.** The one-sided p-value is the share of clones that did at least as well. Benjamini–Hochberg at q = 0.10 corrects across every address tested.
6. **Calibration.** The same test runs on synthetic traders with no timing skill by construction. They must pass at about 0%, with uniform p-values. They do.

`python score.py` runs the self-check: a planted timing edge must be found, and a random trader must not be.

## On-chain (HyperEVM)

- `contracts/src/PlaceboRegistry.sol` stores per-address scores (`nEvents`, `realBps`, `directionBps`, `timingBps`, `pValueBps`, `passes`, `asOf`) plus `isSkilled(address)`. `methodHash` is the sha256 of `score.py`, so anyone can check which code produced the scores.
- `contracts/src/PlaceboLens.sol` joins a score with live HyperCore state through the read precompiles: account value (0x80F), position (0x800) and oracle price (0x807). It was checked read-only against mainnet: it returns HLP's account value and the live BTC oracle price.
- `keeper.py` pushes scores in batches of 50 (about 1.5M gas each, under the 3M small-block limit).
- Registry on HyperEVM testnet (998): *address after deploy*

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
