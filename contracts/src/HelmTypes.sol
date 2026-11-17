// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

/// @notice Bit flags describing every way the reactive contract changed a model's proposal.
/// @dev `0` means the proposal was accepted exactly as the model wrote it. The flags are
///      OR-ed together, so a proposal can be clamped for more than one reason at once.
///      The dashboard renders these as the "what the contract changed" column.
library HelmClamp {
    /// @notice The proposal was accepted unchanged.
    uint8 internal constant NONE = 0;
    /// @notice LP share was above the user's maximum and was pulled down to it.
    uint8 internal constant LP_ABOVE_MAX = 1 << 0;
    /// @notice LP share was below the user's minimum and was pushed up to it.
    uint8 internal constant LP_BELOW_MIN = 1 << 1;
    /// @notice LP range width was above the user's maximum and was pulled down to it.
    uint8 internal constant RANGE_ABOVE_MAX = 1 << 2;
    /// @notice LP range width was below the user's minimum and was pushed up to it.
    uint8 internal constant RANGE_BELOW_MIN = 1 << 3;
    /// @notice Forecast volatility was above the user's exit level, so LP was forced to zero.
    uint8 internal constant VOLATILITY_EXIT = 1 << 4;
    /// @notice The on-chain fee edge did not beat lending, so LP was forced to zero.
    uint8 internal constant ECONOMIC_VETO = 1 << 5;
    /// @notice The move was smaller than the user's minimum trade and was skipped.
    uint8 internal constant NO_TRADE = 1 << 6;
}

/// @notice How a cycle ended.
library HelmAction {
    /// @notice A model proposal was evaluated and executed.
    uint8 internal constant FROM_MODEL = 0;
    /// @notice The contract moved the vault without asking the model at all.
    uint8 internal constant AUTONOMOUS_EXIT = 1;
}

/// @notice The user's approved risk envelope. Stored on the vault and mirrored on the reactive contract.
struct HelmLimits {
    /// @notice Minimum LP share of the vault, in basis points.
    uint256 lpShareMinBps;
    /// @notice Maximum LP share of the vault, in basis points.
    uint256 lpShareMaxBps;
    /// @notice Narrowest LP range width the user accepts, in basis points (half-width).
    uint256 rangeWidthMinBps;
    /// @notice Widest LP range width the user accepts, in basis points (half-width).
    uint256 rangeWidthMaxBps;
    /// @notice Minimum seconds between two cycles.
    uint256 cooldownSec;
    /// @notice Realized volatility, in basis points, above which LP is forced to zero.
    uint256 volExitLevelBps;
    /// @notice Smallest change in LP share, in basis points, worth spending gas on.
    uint256 minTradeBps;
    /// @notice How long a model proposal stays acceptable after it was requested, in seconds.
    uint256 freshnessSec;
}

/// @notice Everything the model must send with a proposal.
struct HelmProposal {
    /// @notice The cycle this proposal answers.
    uint256 cycleId;
    /// @notice LP share of the vault the model asks for, in basis points.
    uint256 lpShareBps;
    /// @notice LP range half-width the model asks for, in basis points.
    uint256 rangeWidthBps;
    /// @notice The model's next-hour realized volatility forecast, in basis points.
    uint256 forecastVolBps;
    /// @notice The model's next-hour lending rate forecast, in basis points.
    uint256 forecastRateBps;
    /// @notice When the model made the proposal.
    uint256 proposedAt;
}

/// @notice The market snapshot a cycle is opened against.
struct HelmSnapshot {
    /// @notice ETH/USDC price at the time the cycle opened, in 1e18.
    uint256 priceE18;
    /// @notice Lending rate at the time the cycle opened, in basis points.
    uint256 rateBps;
    /// @notice Realized volatility at the time the cycle opened, in basis points.
    uint256 volBps;
    /// @notice Block the snapshot was taken from.
    uint256 blockNumber;
}
