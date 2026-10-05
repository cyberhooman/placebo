// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {PlaceboRegistry} from "../src/PlaceboRegistry.sol";
import {PlaceboLens} from "../src/PlaceboLens.sol";

/// Env: PLACEBO_DEPLOYER_KEY (hex private key, never stored), optional PLACEBO_KEEPER (default = deployer), PLACEBO_METHOD_HASH (bytes32).
contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PLACEBO_DEPLOYER_KEY");
        address keeper = vm.envOr("PLACEBO_KEEPER", vm.addr(pk));
        bytes32 mh = vm.envOr("PLACEBO_METHOD_HASH", bytes32(0));
        vm.startBroadcast(pk);
        PlaceboRegistry reg = new PlaceboRegistry(keeper, mh);
        PlaceboLens lens = new PlaceboLens(reg);
        vm.stopBroadcast();
        console.log("registry", address(reg));
        console.log("lens", address(lens));
    }
}
