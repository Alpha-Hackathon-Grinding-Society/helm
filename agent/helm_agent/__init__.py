"""Helm agent: the model that proposes an allocation, and the listener that posts it.

The package is deliberately split so that each piece can be tested on its own:

* `data`      - pulls real Uniswap v3 swap history from Base mainnet and caches it.
* `features`  - turns that history into the feature vectors the model consumes.
* `model`     - the neural network that maps features to an allocation.
* `backtest`  - out-of-sample evaluation of the model against three baselines.
* `policy`    - the decision layer: the model's output constrained by the user's envelope.
* `llm`       - the Kite Passport (Anthropic) explanation layer, with a deterministic fallback.
* `chain`     - the thin on-chain client the listener uses.
* `listener`  - the long-running loop: watch for a cycle, answer it, post the proposal.
"""

__version__ = "0.1.0"
