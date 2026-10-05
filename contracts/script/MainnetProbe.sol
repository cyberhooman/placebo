// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {PlaceboRegistry} from "../src/PlaceboRegistry.sol";
import {PlaceboLens} from "../src/PlaceboLens.sol";

/// Not for deployment. eth_call it as contract-creation (no `to`) against a HyperEVM RPC:
/// the constructor runs the lens and returns abi.encode(Check) as the call result. See README.
contract MainnetProbe {
    constructor(address trader, uint32 perp) {
        PlaceboLens lens = new PlaceboLens(new PlaceboRegistry(address(this), 0));
        bytes memory out = abi.encode(lens.check(trader, perp));
        assembly { return(add(out, 32), mload(out)) }
    }
}
