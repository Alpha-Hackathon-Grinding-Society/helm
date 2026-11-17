// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { ERC20 } from "@openzeppelin/token/ERC20/ERC20.sol";

/// @notice A test-only ERC-20 anyone can mint.
/// @dev Helm's vault asset is `MockUSD` with **18 decimals**, so every amount in Helm is in wei-units of
///      USD and no decimal conversion is needed anywhere in the stack. It is not Circle's USDC and it is
///      not meant to be.
contract MockERC20 is ERC20 {
    address public minter;

    constructor(string memory name_, string memory symbol_, address minter_) ERC20(name_, symbol_) {
        minter = minter_;
    }

    function mint(address to, uint256 amount) external {
        require(msg.sender == minter, "not minter");
        _mint(to, amount);
    }
}
