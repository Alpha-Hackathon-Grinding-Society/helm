"""The Helm allocation model.

A small multilayer perceptron with three heads:

* **allocation** - the share of the vault that should sit in the liquidity position, in
  `[0, 1]`. This is the number the contract clamps.
* **volatility** - the volatility the model expects over the next day, annualised, in basis
  points. The contract grades this against the volatility it measured itself.
* **yield** - the fee yield the model expects the market to pay over the next day, in basis
  points. The contract grades this against the yield it measured itself.

The implementation is written directly on NumPy rather than on a deep learning framework.
That is a deliberate choice: the network is three layers wide, it has to run inside a
watchdog on a testnet with no GPU, and the whole point of the exercise is that a reviewer
can read the forward pass and the backward pass without installing anything. `fit` is
ordinary mini-batch Adam with L2 regularisation, and `save`/`load` write a plain `.npz`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from helm_agent.features import FEATURE_NAMES, LABEL_NAMES


def _sigmoid(x: np.ndarray) -> np.ndarray:
    # numerically stable logistic
    out = np.empty_like(x)
    positive = x >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    out[~positive] = exp_x / (1.0 + exp_x)
    return out


def _softplus(x: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0.0)


def _softplus_grad(x: np.ndarray) -> np.ndarray:
    return _sigmoid(x)


@dataclass
class TrainReport:
    """What the training run did, in numbers."""

    epochs: int
    train_loss: float
    valid_loss: float
    allocation_mae: float
    volatility_mae_bps: float
    yield_mae_bps: float
    history: list[dict]

    def to_json(self) -> dict:
        return {
            "epochs": self.epochs,
            "train_loss": self.train_loss,
            "valid_loss": self.valid_loss,
            "allocation_mae": self.allocation_mae,
            "volatility_mae_bps": self.volatility_mae_bps,
            "yield_mae_bps": self.yield_mae_bps,
            "history": self.history,
        }


class AllocationModel:
    """A three headed MLP written on NumPy."""

    def __init__(
        self,
        n_features: int,
        hidden: tuple[int, ...] = (48, 24),
        seed: int = 7,
        output_scale: tuple[float, float] = (1000.0, 1000.0),
    ) -> None:
        """`output_scale` is how many basis points one normalised unit of the forecast is.

        The network works in normalised units throughout: the allocation is a fraction of
        the vault, and the two forecasts are measured in thousands of basis points. The
        conversion to basis points happens once, on the way out. Doing it this way means
        every head trains at the same learning rate, which is what keeps the volatility
        and yield heads from being drowned out by the allocation head.
        """
        rng = np.random.default_rng(seed)
        self.n_features = n_features
        self.hidden = hidden
        self.output_scale = output_scale
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []

        sizes = [n_features, *hidden]
        for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
            # He initialisation for tanh
            self.weights.append(rng.normal(0.0, np.sqrt(2.0 / fan_in), (fan_in, fan_out)))
            self.biases.append(np.zeros(fan_out))
        # output layer: allocation, volatility, yield
        self.weights.append(rng.normal(0.0, np.sqrt(2.0 / hidden[-1]), (hidden[-1], 3)))
        self.biases.append(np.zeros(3))

    # ------------------------------------------------------------------ forward / backward
    def _forward(self, x: np.ndarray) -> tuple[np.ndarray, list]:
        """Forward pass in normalised units.

        Column 0 is the allocation fraction, column 1 the volatility in thousands of
        basis points, column 2 the yield in thousands of basis points.
        """
        cache = [x]
        activation = x
        for i in range(len(self.hidden)):
            z = activation @ self.weights[i] + self.biases[i]
            activation = np.tanh(z)
            cache.append((z, activation))
        z = activation @ self.weights[-1] + self.biases[-1]
        raw = z.copy()
        out = np.empty_like(z)
        out[:, 0] = _sigmoid(z[:, 0])
        out[:, 1] = _softplus(z[:, 1])
        out[:, 2] = _softplus(z[:, 2])
        cache.append((raw, out))
        return out, cache

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Forward pass. Returns `(n, 3)` of allocation, volatility bps, yield bps."""
        x = np.atleast_2d(np.asarray(x, dtype=float))
        out, _ = self._forward(x)
        scaled = out.copy()
        scaled[:, 1] *= self.output_scale[0]
        scaled[:, 2] *= self.output_scale[1]
        return scaled

    def _backward(self, cache: list, grad_out: np.ndarray) -> tuple[list, list]:
        grads_w: list[np.ndarray] = [None] * len(self.weights)  # type: ignore[list-item]
        grads_b: list[np.ndarray] = [None] * len(self.biases)  # type: ignore[list-item]

        raw, out = cache[-1]
        # d/dz of the output layer
        delta = grad_out.copy()
        delta[:, 0] *= out[:, 0] * (1 - out[:, 0])  # sigmoid
        delta[:, 1] *= _softplus_grad(raw[:, 1])
        delta[:, 2] *= _softplus_grad(raw[:, 2])

        activation = cache[-2][1] if isinstance(cache[-2], tuple) else cache[-2]
        grads_w[-1] = activation.T @ delta
        grads_b[-1] = delta.sum(axis=0)

        for i in range(len(self.hidden) - 1, -1, -1):
            z_prev, a_prev = cache[i + 1]
            delta = (delta @ self.weights[i + 1].T) * (1 - a_prev**2)
            # the input to layer `i` is the activation of layer `i - 1`, except for the
            # first layer, whose input is the batch itself.
            input_activation = cache[i][1] if isinstance(cache[i], tuple) else cache[i]
            grads_w[i] = input_activation.T @ delta
            grads_b[i] = delta.sum(axis=0)
        return grads_w, grads_b

    # ------------------------------------------------------------------ training
    def fit(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_valid: np.ndarray,
        y_valid: np.ndarray,
        epochs: int = 400,
        batch_size: int = 64,
        learning_rate: float = 0.01,
        l2: float = 1e-4,
        allocation_weight: float = 6.0,
        volatility_weight: float = 1.0,
        yield_weight: float = 1.0,
        seed: int = 11,
    ) -> TrainReport:
        """Train the network with mini-batch Adam.

        The three heads are weighted: the allocation head is the one the money depends on,
        so it carries the most weight. The volatility and yield heads are the ones the
        contract grades on chain, so they are trained alongside rather than afterwards.
        """
        rng = np.random.default_rng(seed)
        n = len(x_train)
        weights = [np.zeros_like(w) for w in self.weights]
        biases = [np.zeros_like(b) for b in self.biases]
        m_w = [np.zeros_like(w) for w in self.weights]
        v_w = [np.zeros_like(w) for w in self.weights]
        m_b = [np.zeros_like(b) for b in self.biases]
        v_b = [np.zeros_like(b) for b in self.biases]
        beta1, beta2, eps = 0.9, 0.999, 1e-8
        step = 0

        loss_weights = np.array([allocation_weight, volatility_weight, yield_weight])
        # The network works in normalised units: the allocation is a fraction of the
        # vault and the two forecasts are measured in thousands of basis points. The
        # targets are put on the same scale before they are compared, so a thousand
        # basis points of forecast error counts as one unit, the same as the whole
        # allocation range.
        target_scale = np.array([1.0, 1.0 / self.output_scale[0], 1.0 / self.output_scale[1]])

        history: list[dict] = []
        for epoch in range(1, epochs + 1):
            order = rng.permutation(n)
            epoch_loss = 0.0
            for start in range(0, n, batch_size):
                idx = order[start : start + batch_size]
                xb, yb = x_train[idx], y_train[idx]
                out, cache = self._forward(xb)
                # the targets are put into the network's own units: the allocation is
                # already a fraction and the two forecasts are divided down to
                # thousands of basis points.
                error = out - yb * target_scale
                # The loss is mean(sum(error^2 * weights)) over the batch, so the
                # gradient with respect to the normalised output is
                # `2 * error * weights / batch`.
                grad = error * loss_weights * (2.0 / len(idx))
                grads_w, grads_b = self._backward(cache, grad)

                step += 1
                for i in range(len(self.weights)):
                    g = grads_w[i] + l2 * self.weights[i]
                    m_w[i] = beta1 * m_w[i] + (1 - beta1) * g
                    v_w[i] = beta2 * v_w[i] + (1 - beta2) * g * g
                    mhat = m_w[i] / (1 - beta1**step)
                    vhat = v_w[i] / (1 - beta2**step)
                    self.weights[i] -= learning_rate * mhat / (np.sqrt(vhat) + eps)

                    gb = grads_b[i]
                    m_b[i] = beta1 * m_b[i] + (1 - beta1) * gb
                    v_b[i] = beta2 * v_b[i] + (1 - beta2) * gb * gb
                    mhat = m_b[i] / (1 - beta1**step)
                    vhat = v_b[i] / (1 - beta2**step)
                    self.biases[i] -= learning_rate * mhat / (np.sqrt(vhat) + eps)

                epoch_loss += float(np.mean(np.sum((error**2) * loss_weights, axis=1)))
            train_loss = epoch_loss / max(1, math_ceil(n / batch_size))
            valid_loss, metrics = self._evaluate(x_valid, y_valid, loss_weights, target_scale)
            history.append(
                {
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "valid_loss": valid_loss,
                    "allocation_mae": metrics["allocation_mae"],
                    "volatility_mae_bps": metrics["volatility_mae_bps"],
                    "yield_mae_bps": metrics["yield_mae_bps"],
                }
            )

        valid_loss, metrics = self._evaluate(x_valid, y_valid, loss_weights, target_scale)
        return TrainReport(
            epochs=epochs,
            train_loss=history[-1]["train_loss"],
            valid_loss=valid_loss,
            allocation_mae=metrics["allocation_mae"],
            volatility_mae_bps=metrics["volatility_mae_bps"],
            yield_mae_bps=metrics["yield_mae_bps"],
            history=history,
        )

    def _evaluate(
        self,
        x: np.ndarray,
        y: np.ndarray,
        loss_weights: np.ndarray,
        target_scale: np.ndarray,
    ) -> tuple[float, dict]:
        out, _ = self._forward(x)
        error = out - y * target_scale
        # the loss is the mean over the batch of the weighted sum over the three heads
        loss = float(np.mean(np.sum((error**2) * loss_weights, axis=1)))
        metrics = {
            "allocation_mae": float(np.mean(np.abs(out[:, 0] - y[:, 0]))),
            "volatility_mae_bps": float(
                np.mean(np.abs(out[:, 1] - y[:, 1] * target_scale[1])) * self.output_scale[0]
            ),
            "yield_mae_bps": float(
                np.mean(np.abs(out[:, 2] - y[:, 2] * target_scale[2])) * self.output_scale[1]
            ),
        }
        return loss, metrics

    # ------------------------------------------------------------------ persistence
    def save(self, path: Path, extra: dict | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {}
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            arrays[f"w{i}"] = w
            arrays[f"b{i}"] = b
        np.savez(path, **arrays)
        meta = {
            "n_features": self.n_features,
            "hidden": list(self.hidden),
            "output_scale": list(self.output_scale),
            "feature_names": list(FEATURE_NAMES),
            "label_names": list(LABEL_NAMES),
        }
        if extra:
            meta.update(extra)
        path.with_suffix(".json").write_text(json.dumps(meta, indent=2))

    @classmethod
    def load(cls, path: Path) -> "AllocationModel":
        data = np.load(path)
        meta = json.loads(path.with_suffix(".json").read_text())
        model = cls(
            n_features=meta["n_features"],
            hidden=tuple(meta["hidden"]),
            output_scale=tuple(meta["output_scale"]),
        )
        for i in range(len(model.weights)):
            model.weights[i] = data[f"w{i}"]
            model.biases[i] = data[f"b{i}"]
        return model


def math_ceil(value: float) -> int:
    import math

    return int(math.ceil(value))
