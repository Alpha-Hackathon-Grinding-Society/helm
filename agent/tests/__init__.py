"""Tests for the pieces of Helm that have to be right for the rest to be right.

The suite is small on purpose and every test is about behaviour a reviewer can check by
hand: the hash function, the absence of look-ahead in the features, the agreement between
the off-chain mirror of the contract's rules and the contract itself, the arithmetic of
the backtest, and the encoding of the one transaction the agent is allowed to send.
"""
