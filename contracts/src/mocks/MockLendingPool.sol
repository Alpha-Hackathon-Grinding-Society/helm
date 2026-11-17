// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { IERC20 } from "@openzeppelin/token/ERC20/IERC20.sol";

interface IMockLendingPool {
    event RateUpdated(uint256 rateBps, uint256 utilizationBps);
    event InterestAccrued(uint256 totalSupplied, uint256 rateBps);

    function deposit(uint256 amount) external returns (uint256 deposited);
    function withdraw(uint256 amount) external returns (uint256 withdrawn);
    function balanceOf(address account) external view returns (uint256);
    function rateBps() external view returns (uint256);
    function utilizationBps() external view returns (uint256);
    function accrue() external;
    function setRate(uint256 rateBps_) external;
}

/// @title MockLendingPool — a lending market that pays a rate and reports it.
/// @notice This is a market simulator, not a lending protocol. It holds the vault's supplied balance,
///         pays simple interest on it, and lets the demo replay historical rate changes by publishing
///         `RateUpdated`, which is what the reactive contract subscribes to.
contract MockLendingPool is IMockLendingPool {
    IERC20 public immutable asset;

    /// @notice Annualised supply rate, in basis points.
    uint256 internal _rateBps;
    /// @notice Utilisation, in basis points. Moves with the rate so the two tell a consistent story.
    uint256 internal _utilizationBps;

    mapping(address => uint256) public balanceOf;
    uint256 public totalSupplied;

    /// @notice Last time interest was accounted for.
    uint256 public lastAccrual;

    address public operator;

    event Deposited(address indexed account, uint256 amount);
    event Withdrawn(address indexed account, uint256 amount);

    constructor(IERC20 asset_, uint256 rateBps_, uint256 utilizationBps_) {
        asset = asset_;
        _rateBps = rateBps_;
        _utilizationBps = utilizationBps_;
        lastAccrual = block.timestamp;
        operator = msg.sender;
    }

    modifier onlyOperator() {
        require(msg.sender == operator, "not operator");
        _;
    }

    /// @notice Accrue interest up to now. Called by every interaction and by the replay script.
    /// @notice The annualised supply rate, in basis points.
    function rateBps() external view returns (uint256) {
        return _rateBps;
    }

    /// @notice Current utilisation, in basis points.
    function utilizationBps() external view returns (uint256) {
        return _utilizationBps;
    }

    function accrue() public {
        uint256 elapsed = block.timestamp - lastAccrual;
        if (elapsed == 0 || totalSupplied == 0) {
            lastAccrual = block.timestamp;
            return;
        }
        // simple interest: supplied * rate * elapsed / (10000 * 365 days)
        uint256 interest = (totalSupplied * _rateBps * elapsed) / (10_000 * 365 days);
        if (interest > 0) {
            totalSupplied += interest;
        }
        lastAccrual = block.timestamp;
        emit InterestAccrued(totalSupplied, _rateBps);
    }

    function deposit(uint256 amount) external returns (uint256 deposited) {
        accrue();
        asset.transferFrom(msg.sender, address(this), amount);
        balanceOf[msg.sender] += amount;
        totalSupplied += amount;
        emit Deposited(msg.sender, amount);
        return amount;
    }

    function withdraw(uint256 amount) external returns (uint256 withdrawn) {
        accrue();
        uint256 balance = balanceOf[msg.sender];
        require(balance >= amount, "insufficient balance");
        balanceOf[msg.sender] = balance - amount;
        totalSupplied -= amount;
        asset.transfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
        return amount;
    }

    /// @notice Publish a new rate. The demo uses this to replay a real rate history.
    function setRate(uint256 rateBps_) external onlyOperator {
        accrue();
        _rateBps = rateBps_;
        // utilisation follows the rate, damped, so the two never contradict each other
        _utilizationBps = (rateBps_ * 8_000) / 10_000;
        emit RateUpdated(rateBps_, _utilizationBps);
    }

    /// @notice Hand the operator role to another address.
    function setOperator(address operator_) external onlyOperator {
        operator = operator_;
    }
}
