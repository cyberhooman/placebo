// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {PlaceboRegistry} from "./PlaceboRegistry.sol";

/// @notice Read-only join of a Placebo score with live HyperCore state via HyperEVM read precompiles.
/// Addresses/encodings: hyper-evm-lib PrecompileLib/HLConstants; verified by eth_call on mainnet (see README).
contract PlaceboLens {
    address constant POSITION = 0x0000000000000000000000000000000000000800; // (address,uint32) -> Position
    address constant VAULT_EQUITY = 0x0000000000000000000000000000000000000802; // (address user,address vault) -> (uint64 equity,uint64 lockedUntil)
    address constant ORACLE_PX = 0x0000000000000000000000000000000000000807; // (uint32) -> uint64
    address constant ACCOUNT_MARGIN = 0x000000000000000000000000000000000000080F; // (uint32 dex,address) -> (int64,uint64,uint64,int64)

    PlaceboRegistry public immutable registry;

    constructor(PlaceboRegistry r) {
        registry = r;
    }

    struct Check {
        PlaceboRegistry.Score score;
        bool skilled;
        bool live; // false when the precompiles are unavailable (plain local EVM)
        int64 accountValue; // perp account value on dex 0, USD 1e6
        int64 szi; // position size in perpIndex
        uint64 oraclePx; // oracle price of perpIndex
    }

    /// @param perpIndex HyperCore perp asset index (0 = BTC; HIP-3 = dex*10000+i)
    function check(address trader, uint32 perpIndex) external view returns (Check memory c) {
        c.score = registry.getScore(trader);
        c.skilled = registry.isSkilled(trader);
        (bool ok, bytes memory r) = ACCOUNT_MARGIN.staticcall(abi.encode(uint32(0), trader));
        if (!ok || r.length < 128) return c;
        c.live = true;
        (c.accountValue,,,) = abi.decode(r, (int64, uint64, uint64, int64));
        (ok, r) = POSITION.staticcall(abi.encode(trader, perpIndex));
        if (ok && r.length >= 64) (c.szi) = abi.decode(r, (int64));
        (ok, r) = ORACLE_PX.staticcall(abi.encode(perpIndex));
        if (ok && r.length >= 32) c.oraclePx = abi.decode(r, (uint64));
    }

    /// @notice Equity `user` holds in `vault` on HyperCore (0 if precompile unavailable).
    function vaultEquity(address user, address vault) external view returns (uint64 equity, uint64 lockedUntil) {
        (bool ok, bytes memory r) = VAULT_EQUITY.staticcall(abi.encode(user, vault));
        if (ok && r.length >= 64) (equity, lockedUntil) = abi.decode(r, (uint64, uint64));
    }
}
