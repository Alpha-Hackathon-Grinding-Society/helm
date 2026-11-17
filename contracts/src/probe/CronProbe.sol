// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { AbstractReactive } from "@reactive/src/base/AbstractReactive.sol";

/// @notice A minimal cron probe: does this Lasna node deliver cron events at all?
contract CronProbe is AbstractReactive {
    address internal constant LEGACY_SYSTEM_ADDR = 0x0000000000000000000000000000000000fffFfF;

    uint256 public constant CRON_TOPIC = 0xf02d6ea5c22a71cffe930a4523fcb4f129be6c804db50e4202fb4e0b07ccb514;

    uint256 public ticks;
    uint256 public lastTickBlock;

    constructor() payable {
        SYSTEM.subscribe(
            block.chainid, LEGACY_SYSTEM_ADDR, CRON_TOPIC, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
        );
    }

    function react(LogRecord calldata log_) external override onlySystem {
        if (log_.topic0 == CRON_TOPIC) {
            ticks += 1;
            lastTickBlock = block.number;
        }
    }
}
