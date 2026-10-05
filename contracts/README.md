# Placebo contracts

Placebo tests whether a Hyperliquid trader's or vault's results come from entry timing or just market direction, by comparing real trades against shuffled-timing clones. An off-chain Python job computes the scores; these contracts publish them.

- `src/PlaceboRegistry.sol` - the keeper (set once in the constructor) pushes batches of scores per address: real vs placebo-mean 24h forward return in bps, `timingBps = real - direction`, one-sided placebo p-value, and whether it survives Benjamini-Hochberg at q=0.10. Tracks `scored` / `passed` counts (re-scoring is handled). `methodHash` = sha256 of the published scoring script; the keeper can update it (event emitted). Views: `isSkilled`, `getScore`.
- `src/PlaceboLens.sol` - read-only. `check(trader, perpIndex)` returns the registry score plus live HyperCore state through HyperEVM read precompiles: account value (0x80F accountMarginSummary, dex 0), position size (0x800), oracle price (0x807). `vaultEquity(user, vault)` uses 0x802. If precompiles are absent (plain local EVM) it returns `live = false` instead of reverting.
- `script/Deploy.s.sol` - deploys both. `script/MainnetProbe.sol` - not for deployment, used for the read-only mainnet check below.

## Build and test
Foundry (installed here at `D:/tools/foundry`, v1.8.4):
```
forge install foundry-rs/forge-std --no-commit   # lib/ is gitignored
forge build
forge test -vv
```

## Deploy (HyperEVM testnet, chain 998)
```
export PLACEBO_DEPLOYER_KEY=0x...            # never commit; env var only
export PLACEBO_KEEPER=0x...                  # optional, defaults to deployer
export PLACEBO_METHOD_HASH=0x...             # optional sha256 of the scoring script
forge script script/Deploy.s.sol --rpc-url https://rpc.hyperliquid-testnet.xyz/evm --broadcast
```
Verify: `forge verify-contract <addr> src/PlaceboRegistry.sol:PlaceboRegistry --chain 998 --verifier sourcify` (Sourcify lists chain 998 as supported; untested). Explorer: https://testnet.purrsec.com

## Measured gas (anvil, optimizer 200 runs)
- Deploy PlaceboRegistry: 667,478. Deploy PlaceboLens: 553,667. Both are under the 3M small-block limit; no big blocks needed.
- `push` of 100 fresh scores: about 3.04M (about 30k per new address; cold write). That is over the 3M small-block limit. Use batches of about 50 (about 1.5M) or enable big blocks (30M).
