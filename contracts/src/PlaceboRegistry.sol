// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Timing-vs-direction scores for Hyperliquid traders/vaults, pushed by an off-chain keeper.
contract PlaceboRegistry {
    struct Score {
        uint32 nEvents;
        int32 realBps; // avg signed 24h forward return per decision
        int32 directionBps; // mean of the placebo (shuffled-timing) clones
        int32 timingBps; // realBps - directionBps
        uint16 pValueBps; // one-sided placebo p-value * 10,000
        bool passes; // survives Benjamini-Hochberg at q=0.10
        uint64 asOf;
    }

    address public immutable keeper;
    bytes32 public methodHash; // sha256 of the published scoring script
    mapping(address => Score) public scores;
    uint32 public scored; // addresses with a score
    uint32 public passed; // addresses currently passing

    event Scored(address indexed who, int32 timingBps, uint16 pValueBps, bool passes);
    event MethodHashUpdated(bytes32 oldHash, bytes32 newHash);

    error NotKeeper();
    error LengthMismatch();
    error ZeroAsOf();

    modifier onlyKeeper() {
        if (msg.sender != keeper) revert NotKeeper();
        _;
    }

    constructor(address keeper_, bytes32 methodHash_) {
        keeper = keeper_;
        methodHash = methodHash_;
        emit MethodHashUpdated(bytes32(0), methodHash_);
    }

    function setMethodHash(bytes32 h) external onlyKeeper {
        emit MethodHashUpdated(methodHash, h);
        methodHash = h;
    }

    function push(address[] calldata who, Score[] calldata s) external onlyKeeper {
        uint256 n = who.length;
        if (n != s.length) revert LengthMismatch();
        uint32 sc = scored;
        uint32 pa = passed;
        for (uint256 i; i < n; ++i) {
            Score calldata x = s[i];
            if (x.asOf == 0) revert ZeroAsOf(); // asOf != 0 marks "scored"
            Score storage old = scores[who[i]];
            if (old.asOf == 0) ++sc;
            else if (old.passes) --pa;
            if (x.passes) ++pa;
            scores[who[i]] = x;
            emit Scored(who[i], x.timingBps, x.pValueBps, x.passes);
        }
        scored = sc;
        passed = pa;
    }

    function isSkilled(address who) external view returns (bool) {
        Score storage s = scores[who];
        return s.passes && s.asOf != 0;
    }

    function getScore(address who) external view returns (Score memory) {
        return scores[who];
    }
}
