// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {PlaceboRegistry} from "../src/PlaceboRegistry.sol";
import {PlaceboLens} from "../src/PlaceboLens.sol";

contract Mock {
    fallback() external {
        // ignores input; returns 4 words: accountValue=777, marginUsed=1, ntlPos=2, rawUsd=3 (extra words ok for other calls)
        bytes memory out = abi.encode(int64(777), uint64(1), uint64(2), int64(3));
        assembly { return(add(out, 32), 128) }
    }
}

contract PlaceboTest is Test {
    PlaceboRegistry reg;
    address keeper = address(0xBEEF);
    event Scored(address indexed who, int32 timingBps, uint16 pValueBps, bool passes);

    function setUp() public {
        reg = new PlaceboRegistry(keeper, bytes32(uint256(1)));
    }

    function _s(bool passes, uint64 asOf) internal pure returns (PlaceboRegistry.Score memory) {
        return PlaceboRegistry.Score(100, 50, 20, 30, 400, passes, asOf);
    }

    function _one(address a, PlaceboRegistry.Score memory s) internal {
        address[] memory w = new address[](1);
        PlaceboRegistry.Score[] memory ss = new PlaceboRegistry.Score[](1);
        w[0] = a;
        ss[0] = s;
        vm.prank(keeper);
        reg.push(w, ss);
    }

    function test_onlyKeeper() public {
        address[] memory w = new address[](0);
        PlaceboRegistry.Score[] memory s = new PlaceboRegistry.Score[](0);
        vm.expectRevert(PlaceboRegistry.NotKeeper.selector);
        reg.push(w, s);
        vm.expectRevert(PlaceboRegistry.NotKeeper.selector);
        reg.setMethodHash(bytes32(0));
    }

    function test_methodHash() public {
        vm.prank(keeper);
        reg.setMethodHash(bytes32(uint256(2)));
        assertEq(reg.methodHash(), bytes32(uint256(2)));
    }

    function test_lengthMismatchAndZeroAsOf() public {
        address[] memory w = new address[](2);
        PlaceboRegistry.Score[] memory s = new PlaceboRegistry.Score[](1);
        vm.prank(keeper);
        vm.expectRevert(PlaceboRegistry.LengthMismatch.selector);
        reg.push(w, s);
        w = new address[](1);
        s[0] = _s(true, 0);
        vm.prank(keeper);
        vm.expectRevert(PlaceboRegistry.ZeroAsOf.selector);
        reg.push(w, s);
    }

    function test_isSkilledAndGet() public {
        _one(address(1), _s(true, 5));
        _one(address(2), _s(false, 5));
        assertTrue(reg.isSkilled(address(1)));
        assertFalse(reg.isSkilled(address(2)));
        assertFalse(reg.isSkilled(address(3)));
        assertEq(reg.getScore(address(1)).timingBps, 30);
    }

    function test_rescoreAccounting() public {
        address a = address(1);
        _one(a, _s(true, 1));
        assertEq(reg.scored(), 1);
        assertEq(reg.passed(), 1);
        _one(a, _s(true, 2)); // pass -> pass
        assertEq(reg.scored(), 1);
        assertEq(reg.passed(), 1);
        _one(a, _s(false, 3)); // pass -> fail
        assertEq(reg.scored(), 1);
        assertEq(reg.passed(), 0);
        _one(a, _s(false, 4)); // fail -> fail
        assertEq(reg.passed(), 0);
        _one(a, _s(true, 5)); // fail -> pass
        assertEq(reg.passed(), 1);
        assertEq(reg.scored(), 1);
    }

    function test_event() public {
        vm.expectEmit(true, false, false, true);
        emit Scored(address(7), 30, 400, true);
        _one(address(7), _s(true, 1));
    }

    function test_batch100() public {
        address[] memory w = new address[](100);
        PlaceboRegistry.Score[] memory s = new PlaceboRegistry.Score[](100);
        for (uint256 i; i < 100; ++i) {
            w[i] = address(uint160(1000 + i));
            s[i] = _s(i % 4 == 0, 9);
        }
        vm.prank(keeper);
        uint256 g = gasleft();
        reg.push(w, s);
        emit log_named_uint("gas push(100)", g - gasleft());
        assertEq(reg.scored(), 100);
        assertEq(reg.passed(), 25);
        assertTrue(reg.isSkilled(address(1000)));
        assertFalse(reg.isSkilled(address(1001)));
    }

    function test_lensLocalNotLive() public {
        _one(address(1), _s(true, 1));
        PlaceboLens lens = new PlaceboLens(reg);
        PlaceboLens.Check memory c = lens.check(address(1), 0);
        assertFalse(c.live);
        assertTrue(c.skilled);
        assertEq(c.score.nEvents, 100);
    }

    function test_lensWithMockPrecompile() public {
        PlaceboLens lens = new PlaceboLens(reg);
        vm.etch(address(0x000000000000000000000000000000000000080F), address(new Mock()).code);
        PlaceboLens.Check memory c = lens.check(address(1), 0);
        assertTrue(c.live);
        assertEq(c.accountValue, 777);
    }
}
