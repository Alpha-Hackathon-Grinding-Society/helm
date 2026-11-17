// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { ISystemContract } from "@reactive/src/interfaces/ISystemContract.sol";

/// @notice Stand-in for the Reactive system contract on Lasna.
/// @dev It records every subscription and every callback request so the test can assert on the exact
///      payload the real network would have delivered.
contract MockSystem {
    struct CallbackRequest {
        uint256 chainId;
        address recipient;
        uint64 gasLimit;
        bytes4 selector;
        bytes args;
    }

    CallbackRequest[] internal requests;

    function subscribe(uint256, address, uint256, uint256, uint256, uint256) external { }

    function unsubscribe(uint256, address, uint256, uint256, uint256, uint256) external { }

    function requestCallbackV_1_0(ISystemContract.CallbackConfiguration_V_1_0 memory config_) external {
        bytes memory payload = config_.payload;
        bytes4 selector;
        bytes memory args;
        if (payload.length >= 4) {
            selector = bytes4(payload);
            args = new bytes(payload.length - 4);
            for (uint256 i = 0; i < args.length; i++) {
                args[i] = payload[i + 4];
            }
        }
        requests.push(
            CallbackRequest({
                chainId: config_.chainId,
                recipient: config_.recipient,
                gasLimit: config_.gasLimit,
                selector: selector,
                args: args
            })
        );
    }

    function requestCallback(ISystemContract.CallbackVersion, bytes memory) external { }

    function debt(address) external pure returns (uint256) {
        return 0;
    }

    function requestCount() external view returns (uint256) {
        return requests.length;
    }

    function requestAt(uint256 i)
        external
        view
        returns (uint256 chainId, address recipient, uint64 gasLimit, bytes memory args)
    {
        CallbackRequest storage r = requests[i];
        return (r.chainId, r.recipient, r.gasLimit, r.args);
    }

    /// @notice The four-byte selector of a recorded callback payload.
    function payloadSelector(uint256 i) external view returns (bytes4) {
        return requests[i].selector;
    }
}
