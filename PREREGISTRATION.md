# Placebo: pre-registration

Written Mon 5 Oct 2026 at 15:53 WIB (08:53 UTC). The fresh fills download was running, and no fresh result had been computed or seen. This file is committed before the results are, so the git history shows the order.

## Question

For each Hyperliquid account or vault: does its entry **timing** make money, or does its result come only from **which coins and which direction** it held while the market moved?

## Population

- **Accounts:** the top 500 on the Hyperliquid leaderboard by 30-day PnL, downloaded 2026-10-05 08:50 UTC from `stats-data.hyperliquid.xyz/Mainnet/leaderboard`. Rows with under $1M of 30-day volume are excluded, since they are holders, not traders.
- **Vaults:** the top 100 open vaults by TVL from `stats-data.hyperliquid.xyz/Mainnet/vaults`, downloaded the same time. 95 remain after removing duplicates of leaderboard rows.
- **Data:** the last 90 days of fills per address (`userFillsByTime`, `aggregateByTime`). Hyperliquid serves only the 10,000 most recent fills, so very active addresses have a shorter history. Hourly candles come from `candleSnapshot`.

## Method (fixed now)

1. **Decision.** Every opening fill (`Open Long`, `Open Short`, `Long > Short`, `Short > Long`), maker or taker, is summed by signed notional per (coin, hour). The sign of the sum is one decision. Forty fills in one hour count as one decision.
2. **Real score T.** The mean, over the address's decisions, of `sign x log(close[t+24h] / close[t])`, where `t` is the close of the hour the decision was made in. Each decision has equal weight. This measures timing at hourly resolution over 24 hours. Edge inside the hour, and exits, are not measured. That is a known limit, stated in the README.
3. **Placebo.** The address's whole decision timeline is shifted by a random offset of k hours and wrapped around its own span `[first, last]`. Coins, directions, the number of decisions and the spacing between them all stay the same. Only *when* changes. 1,000 offsets are drawn, or every possible offset when the span is shorter than 1,000 hours. Decisions that land where a coin has no price are dropped from that clone.
4. **Split.** `direction = mean of the placebo scores` is what the coins and directions earn at random times. `timing = T - direction`.
5. **p-value.** One-sided: `(1 + #{placebo >= T}) / (1 + K)`.
6. **Correction.** Benjamini-Hochberg at q = 0.10 across all eligible addresses. **Passes** = survives the correction.
7. **Eligible.** At least 50 decisions over a span of at least 14 days.

## Headline numbers (to report whatever they turn out to be)

- **H-A:** how many eligible top-500 accounts pass, and how many eligible vaults pass. Also the count with raw p < 0.05, against the roughly 5% expected by chance.
- **H-B:** the median direction part and the median timing part, in bp per decision, for accounts and for vaults. Also the share of addresses whose timing part is below zero.
- **H-C (depends on the market regime; reported, not a gate):** the Spearman correlation between 30-day ROI rank and current net exposure (net / gross notional from `clearinghouseState`), shown next to the BTC and equal-weight market returns over the same 30 days. The 8 Sep 2026 measurement (market +21%, top quintile 93.3% long, bottom net -0.91) stays quoted under its own date.

## Gate: Tue 6 Oct 2026, 12:00 WIB

- **K1 (data):** fewer than 300 eligible addresses means stop, and switch to the Robinhood Chain fallback.
- **K2 (calibration):** replace every eligible address's timeline with one random circular shift. These are synthetic traders with no timing skill by construction. Run the full test on them. It fails if more than 2% of them pass after correction, or the KS test of their p-values against uniform gives p < 0.01. If it fails and can't be fixed by 12:00, stop.
- **No gate on the value of H-A.** If almost nobody beats their own placebo, that is the finding, not a failure.

**Change from the panel's gate (DEBATE_2026-10-05.md §9).** The panel required (b) a past-edge vs exposure correlation of at least |0.5| and (c) a split-half direction share of at least 0.5. (b) depends on the market regime: a flat month fails it for reasons unrelated to whether the test works. So it moves to H-C as a reported number. (c) is not needed for any claim in the pitch. The gate now checks what the product needs: enough data, and a test that is calibrated.

## What is never claimed

- Not that an account "has no skill". The test says only that its hourly entry timing over 24 hours is not distinguishable from its own placebo.
- No account is named as a "loser" in public. Only counts, plus badges for addresses that pass.
- Not that an LLM or AI agent was lucky, unless its address was actually scored here.
