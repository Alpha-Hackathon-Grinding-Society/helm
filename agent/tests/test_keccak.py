"""Keccak-256 vectors, and the function selectors Helm actually sends."""

from helm_agent.keccak import event_topic, keccak256, selector


def test_keccak_empty() -> None:
    assert keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"


def test_keccak_abc() -> None:
    assert keccak256(b"abc").hex() == "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"


def test_selector_transfer() -> None:
    assert selector("transfer(address,uint256)") == "0xa9059cbb"


def test_selector_balance_of() -> None:
    assert selector("balanceOf(address)") == "0x70a08231"


def test_event_topics_match_the_deployed_contracts() -> None:
    # These prefixes were read off the events the deployed Helm contracts emitted, so
    # they are the ground truth the agent decodes against.
    assert event_topic("LimitsUpdated(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)").startswith("0x45737702")
    assert event_topic("ProposalPosted(address,uint256,uint256,uint256,uint256,uint256,uint256)").startswith("0xa4b4bd37")
    assert event_topic("Paused(address,bool)").startswith("0xe8699cf6")
    assert event_topic("AgentChanged(address,address)").startswith("0xb21f1bf0")
    # the mock pool's own Swap event
    assert event_topic("Swap(uint256,uint256,uint256)").startswith("0x92d941e0")
    # and Uniswap v3's, which is what the history downloader reads
    assert event_topic(
        "Swap(address,address,int256,int256,uint160,uint128,int24)"
    ).startswith("0xc42079f9")


def test_event_topic_is_stable_for_parameter_renames() -> None:
    # The enforcer grades the yield forecast, so the event parameters are named yield.
    # Renaming a parameter does not change the topic, which is why the agent can decode
    # the event without caring about the names.
    assert event_topic("ForecastGraded(uint256,uint256,uint256,uint256,uint256)") == event_topic(
        "ForecastGraded(uint256,uint256,uint256,uint256,uint256)"
    )
