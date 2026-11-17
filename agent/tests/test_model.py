"""The network trains, saves, loads, and stays inside its output ranges."""

import numpy as np

from helm_agent.model import AllocationModel


def test_the_network_learns_a_separable_signal() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(400, 6))
    # the allocation label is a step function of the first feature
    y = np.zeros((400, 3))
    y[:, 0] = (x[:, 0] > 0).astype(float)
    y[:, 1] = np.abs(x[:, 1]) * 1000.0
    y[:, 2] = np.abs(x[:, 2]) * 1000.0

    model = AllocationModel(n_features=6, hidden=(16, 8), seed=1)
    report = model.fit(x[:300], y[:300], x[300:], y[300:], epochs=250, batch_size=32, learning_rate=0.02)

    # the loss has to go down, not just the headline number
    assert report.history[-1]["train_loss"] < 0.5 * report.history[0]["train_loss"]
    # the allocation head is the one the money depends on, and it has to be accurate
    assert report.allocation_mae < 0.1

    # the forecast heads have to beat the trivial baseline of predicting the mean
    for column, mae in ((1, report.volatility_mae_bps), (2, report.yield_mae_bps)):
        baseline = float(np.mean(np.abs(y[300:, column] - y[:300, column].mean())))
        assert mae < baseline, f"head {column} did not beat the mean baseline"


def test_the_outputs_stay_in_their_ranges() -> None:
    model = AllocationModel(n_features=4, hidden=(8,))
    rng = np.random.default_rng(1)
    prediction = model.predict(rng.normal(size=(50, 4)))
    assert prediction.shape == (50, 3)
    assert (prediction[:, 0] >= 0.0).all() and (prediction[:, 0] <= 1.0).all()
    assert (prediction[:, 1] >= 0.0).all()
    assert (prediction[:, 2] >= 0.0).all()


def test_save_and_load_round_trip(tmp_path) -> None:
    model = AllocationModel(n_features=3, hidden=(8, 4), seed=5)
    x = np.random.default_rng(2).normal(size=(10, 3))
    before = model.predict(x)

    path = tmp_path / "model.npz"
    model.save(path, extra={"feature_mean": [0.0, 0.0, 0.0], "feature_std": [1.0, 1.0, 1.0]})

    loaded = AllocationModel.load(path)
    after = loaded.predict(x)
    assert np.allclose(before, after)

    import json

    meta = json.loads((tmp_path / "model.json").read_text())
    assert meta["feature_mean"] == [0.0, 0.0, 0.0]
    assert meta["hidden"] == [8, 4]


def test_the_gradient_actually_moves_the_weights() -> None:
    model = AllocationModel(n_features=2, hidden=(4,), seed=9)
    before = [w.copy() for w in model.weights]
    x = np.array([[0.1, 0.2], [0.3, 0.4]])
    y = np.array([[1.0, 10.0, 10.0], [0.0, 20.0, 20.0]])
    model.fit(x, y, x, y, epochs=5, batch_size=2, learning_rate=0.05)
    assert any(not np.allclose(a, b) for a, b in zip(before, model.weights))
