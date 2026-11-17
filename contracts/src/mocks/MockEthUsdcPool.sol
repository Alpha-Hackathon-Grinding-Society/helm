// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import { IERC20 } from "@openzeppelin/token/ERC20/IERC20.sol";
import { Math } from "@openzeppelin/utils/math/Math.sol";

interface IMockEthUsdcPool {
    event Swap(uint256 priceE18, uint256 usdcIn, uint256 priceChangeBps);
    event LiquidityAdded(address indexed provider, uint256 usdcIn, uint256 rangeWidthBps, uint256 valueUsd);
    event LiquidityRemoved(address indexed provider, uint256 usdcOut, uint256 feesUsd);
    event FeeRateUpdated(uint256 feeRateBps);
    event FeeSettled(address indexed provider, uint256 fees);

    function priceE18() external view returns (uint256);
    function lpValue(address holder) external view returns (uint256);
    function liquidityUsd() external view returns (uint256);
    function depositLiquidity(uint256 usdcAmount, uint256 rangeWidthBps, address recipient) external returns (uint256 valueUsd);
    function withdrawLiquidity(address recipient) external returns (uint256 usdcOut);
    function swap(uint256 usdcIn) external returns (uint256 priceChangeBps);
    function setPrice(uint256 priceE18_) external;
    function positionOf(address holder)
        external
        view
        returns (uint256 usdcIn, uint256 ethUnits, uint256 entryPriceE18, uint256 rangeWidthBps, uint256 valueUsd, uint256 feesUsd);
}

/// @title MockEthUsdcPool — the ETH/USD market Helm reads, and the venue its LP position sits in.
/// @notice A deliberately simple market simulator. It is **not** an AMM and it does not try to be one.
///         What it does:
///
///         1. It holds a market price that moves like a constant product when USD comes in, and it
///            publishes every move as `Swap`, which is what the reactive contract on Lasna subscribes to.
///         2. It holds LP positions. A position is stored as the USD and the ETH the provider brought in.
///            Its value at the current price is the standard constant-product value
///            `2 * sqrt(k * P)`, where `k = usdc * ethUnits` is the position's own invariant. That is
///            exactly the full-range impermanent-loss formula, so the impermanent loss a position shows
///            is the real one for a full-range position.
///         3. It pays a fee on every swap to the liquidity providers, and a narrower range earns a
///            larger share of those fees, because concentrated liquidity captures more of the flow.
///
///         What it does **not** do: it does not model out-of-range concentrated liquidity, and it does
///         not model the extra impermanent loss that a narrow band suffers. Both of those are modelled
///         in the Python backtest, which is the source of truth for Helm's quantitative claims. The
///         on-chain pool exists so the reactive loop has something real to move money through.
contract MockEthUsdcPool is IMockEthUsdcPool {
    IERC20 public immutable asset;

    /// @notice The market price of ETH in USD, in 1e18.
    uint256 internal _priceE18;
    /// @notice Swap fee, in basis points of the input.
    uint256 public feeRateBps = 30;

    /// @notice Swap fees that have not been settled to a provider yet.
    uint256 public feePool;
    /// @notice Total provider fee weight. A narrow band carries more weight.
    uint256 public totalFeeWeight;
    /// @notice Cumulative fee index. A provider's share is `weight * (feeIndex - snapshot) / 1e18`.
    uint256 public feeIndex;
    /// @notice Total USD supplied by providers. This is the virtual book depth used for price impact.
    uint256 public totalLiquidityUsdCached;

    address public operator;

    struct Position {
        /// @notice Total USD the provider brought in (both legs of the position, valued in USD).
        uint256 usdcIn;
        /// @notice ETH units the position carries, at 1e18 per ETH.
        uint256 ethUnits;
        /// @notice The price the position was opened at, in 1e18.
        uint256 entryPriceE18;
        /// @notice Half-width of the band, in basis points.
        uint256 rangeWidthBps;
        /// @notice Fee weight of this position.
        uint256 feeWeight;
        /// @notice Fee index when the position was opened or last settled.
        uint256 feeIndexSnapshot;
        /// @notice Fees already settled to this provider.
        uint256 feesSettled;
    }

    mapping(address => Position) public positions;

    constructor(IERC20 asset_, uint256 priceE18_) {
        asset = asset_;
        _priceE18 = priceE18_;
        operator = msg.sender;
    }

    modifier onlyOperator() {
        require(msg.sender == operator, "not operator");
        _;
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                       Price and fees                                             */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice Trade USD for ETH. The price moves like a constant product and a fee is taken.
    /// @param usdcIn USD coming in. The trader pays it in; the pool keeps it as fee revenue and depth.
    /// @return priceChangeBps Signed change in the price, in basis points.
    function swap(uint256 usdcIn) external returns (uint256 priceChangeBps) {
        require(usdcIn > 0, "zero in");
        uint256 priceBefore = _priceE18;
        uint256 supply = totalLiquidityUsdCached;

        // constant-product move on the virtual book: USD coming in pushes the ETH price up.
        uint256 newPrice = priceBefore;
        if (supply > 0) {
            newPrice = (priceBefore * (supply + usdcIn)) / supply;
        }
        _priceE18 = newPrice;
        // Signed change in the price, carried as a two's-complement uint256.
        priceChangeBps = uint256(
            priceBefore > 0 ? ((int256(newPrice) - int256(priceBefore)) * 10_000) / int256(priceBefore) : int256(0)
        );

        uint256 fee = (usdcIn * feeRateBps) / 10_000;
        if (fee > 0) {
            feePool += fee;
            if (totalFeeWeight > 0) {
                feeIndex += (fee * 1e18) / totalFeeWeight;
            }
        }

        // The trader hands over real USD. The ETH leg is virtual (the pool settles it from its own
        // inventory), but the USD is real cash, so fee revenue is always payable to providers.
        asset.transferFrom(msg.sender, address(this), usdcIn);

        emit Swap(newPrice, usdcIn, uint256(priceChangeBps));
    }

    /// @notice Set the market price directly. The replay script uses this to reproduce a real price path.
    function setPrice(uint256 priceE18_) external onlyOperator {
        require(priceE18_ > 0, "zero price");
        uint256 priceBefore = _priceE18;
        _priceE18 = priceE18_;
        uint256 changeBps = uint256(
            priceBefore > 0 ? ((int256(priceE18_) - int256(priceBefore)) * 10_000) / int256(priceBefore) : int256(0)
        );
        emit Swap(priceE18_, 0, changeBps);
    }

    function setFeeRate(uint256 feeRateBps_) external onlyOperator {
        feeRateBps = feeRateBps_;
        emit FeeRateUpdated(feeRateBps_);
    }

    function setOperator(address operator_) external onlyOperator {
        operator = operator_;
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                       Liquidity                                                  */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice Add liquidity. The provider brings USD; the position is opened 50/50 by value.
    /// @param usdcAmount USD to add.
    /// @param rangeWidthBps Half-width of the band, in basis points. A narrower band earns more fees.
    /// @param recipient Provider to credit.
    function depositLiquidity(uint256 usdcAmount, uint256 rangeWidthBps, address recipient)
        external
        returns (uint256 valueUsd)
    {
        require(usdcAmount > 0, "zero amount");
        require(rangeWidthBps > 0, "zero width");

        // settle what the provider has already earned *before* the weight changes, otherwise the new
        // weight would be applied retroactively to the whole window.
        _settleFees(recipient);

        asset.transferFrom(msg.sender, address(this), usdcAmount);

        Position storage p = positions[recipient];
        uint256 price = _priceE18;
        uint256 ethUnits = (usdcAmount * 1e18) / (2 * price);

        if (p.usdcIn == 0) {
            p.entryPriceE18 = price;
            p.rangeWidthBps = rangeWidthBps;
            p.feeIndexSnapshot = feeIndex;
        }
        p.usdcIn += usdcAmount;
        p.ethUnits += ethUnits;
        p.feeWeight = _weight(p.usdcIn, p.rangeWidthBps);
        totalFeeWeight = totalFeeWeight + _weight(usdcAmount, p.rangeWidthBps);
        totalLiquidityUsdCached += usdcAmount;

        valueUsd = _valueOf(p, price);
        emit LiquidityAdded(recipient, usdcAmount, p.rangeWidthBps, valueUsd);
    }

    /// @notice Remove all of a provider's liquidity, paying them USD plus their settled fees.
    function withdrawLiquidity(address recipient) external returns (uint256 usdcOut) {
        Position storage p = positions[recipient];
        uint256 fees = _settleFees(recipient);
        uint256 value = _valueOf(p, _priceE18);

        uint256 paid = value + fees;
        uint256 cash = asset.balanceOf(address(this));
        if (paid > cash) {
            // The ETH leg of every position is virtual and is settled by the operator. If the operator
            // has not seeded the pool, the withdrawal is capped by the cash on hand.
            require(cash >= paid, "pool underfunded");
        }
        asset.transfer(recipient, paid);

        totalFeeWeight = totalFeeWeight - p.feeWeight;
        totalLiquidityUsdCached = totalLiquidityUsdCached - p.usdcIn;
        delete positions[recipient];

        usdcOut = paid;
        emit LiquidityRemoved(recipient, paid, fees);
    }

    /// @notice Settle a provider's accrued fees into their position.
    function _settleFees(address provider) internal returns (uint256 fees) {
        Position storage p = positions[provider];
        if (p.feeWeight == 0) return 0;
        uint256 accrued = (p.feeWeight * (feeIndex - p.feeIndexSnapshot)) / 1e18;
        p.feeIndexSnapshot = feeIndex;
        p.feesSettled += accrued;
        fees = accrued;
        if (accrued > 0) emit FeeSettled(provider, accrued);
    }

    /// @notice Fee weight of a position. A narrower band captures more flow, so it earns more per dollar.
    function _weight(uint256 usdcIn, uint256 rangeWidthBps) internal pure returns (uint256) {
        uint256 w = rangeWidthBps < 100 ? 100 : rangeWidthBps;
        return (usdcIn * 100) / w;
    }

    /// @notice The value of a position at a price: `2 * sqrt(k * P)`, the constant-product value.
    /// @dev `k = usdcIn * ethUnits / 2` because `usdcIn` is the *total* deposited (both legs valued in
    ///      USD) while only half of it sits on the USD side of the invariant. The price is divided by
    ///      1e18 because `ethUnits` and `usdcIn` are both raw 1e18-scaled token amounts, so the
    ///      invariant has to be multiplied by the price expressed in USD per ETH, not in raw units.
    function _valueOf(Position storage p, uint256 price) internal view returns (uint256) {
        if (p.usdcIn == 0) return 0;
        uint256 k = (p.usdcIn * p.ethUnits) / 2;
        return 2 * Math.sqrt((k * price) / 1e18);
    }

    /* ------------------------------------------------------------------------------------------- */
    /*                                         Views                                                    */
    /* ------------------------------------------------------------------------------------------- */

    /// @notice The current ETH/USD price, in 1e18.
    function priceE18() external view returns (uint256) {
        return _priceE18;
    }

    /// @notice Total USD supplied by providers. This is the depth of the virtual book.
    function liquidityUsd() external view returns (uint256) {
        return totalLiquidityUsdCached;
    }

    function lpValue(address holder) external view returns (uint256) {
        Position storage p = positions[holder];
        return _valueOf(p, _priceE18) + (p.feeWeight * (feeIndex - p.feeIndexSnapshot)) / 1e18;
    }

    function positionOf(address holder)
        external
        view
        returns (uint256 usdcIn, uint256 ethUnits, uint256 entryPriceE18, uint256 rangeWidthBps, uint256 valueUsd, uint256 feesUsd)
    {
        Position storage p = positions[holder];
        return (
            p.usdcIn,
            p.ethUnits,
            p.entryPriceE18,
            p.rangeWidthBps,
            _valueOf(p, _priceE18),
            p.feesSettled + (p.feeWeight * (feeIndex - p.feeIndexSnapshot)) / 1e18
        );
    }
}
