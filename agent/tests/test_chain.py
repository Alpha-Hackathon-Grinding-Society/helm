"""The encoding of the one transaction the agent is allowed to send."""

from helm_agent.chain import (
    DECISION_REQUESTED_TOPIC,
    PROPOSAL_POSTED_TOPIC,
    REBALANCED_TOPIC,
    Log,
    call_data,
    decode_address,
    decode_address_at,
    decode_bool,
    decode_uints,
    encode_uint,
    encode_uints,
    read_decision_requests,
    read_rebalances,
)
from helm_agent.keccak import selector


def test_uint_encoding_is_one_word() -> None:
    assert encode_uint(0) == "0" * 64
    assert encode_uint(1) == "0" * 63 + "1"
    assert len(encode_uint(2**255)) == 64


def test_uints_encoding_is_the_concatenation_of_words() -> None:
    assert encode_uints([1, 2]) == "0" * 63 + "1" + "0" * 63 + "2"


def test_uint_decoding_round_trips() -> None:
    values = [0, 1, 12345, 2**200]
    assert decode_uints("0x" + encode_uints(values), 4) == values


def test_bool_decoding() -> None:
    assert decode_bool("0x" + "0" * 64) is False
    assert decode_bool("0x" + "0" * 63 + "1") is True


def test_address_decoding() -> None:
    assert decode_address("0x" + "0" * 24 + "17e5544f98a5d2073edc2e29410d6b099305ed6f") == "0x17e5544f98a5d2073edc2e29410d6b099305ed6f"


def test_an_address_is_read_out_of_the_word_it_sits_in() -> None:
    # `ProposalRejected(uint256 indexed cycleId, uint8 reason, address proposer)` has one
    # indexed parameter, so the proposer is the *second* word of the data, not a topic.
    # Reading it from a topic that does not exist is what crashed the agent.
    data = "0x" + encode_uints([6, 0x26127EE61ECE6C105B575ED3296C5698323F029A])
    assert decode_address_at(data, 1) == "0x26127ee61ece6c105b575ed3296c5698323f029a"
    assert decode_address_at(data, 0) == "0x0000000000000000000000000000000000000006"


def test_calldata_is_the_selector_plus_the_arguments() -> None:
    data = call_data("postProposal(uint256,uint256,uint256,uint256,uint256)", [1, 2, 3, 4, 5])
    assert data.startswith(selector("postProposal(uint256,uint256,uint256,uint256,uint256)"))
    assert len(data) == 2 + 8 + 5 * 64


def test_the_event_topics_are_the_ones_the_contracts_emit() -> None:
    assert DECISION_REQUESTED_TOPIC.startswith("0x")
    assert len(DECISION_REQUESTED_TOPIC) == 66
    assert len(PROPOSAL_POSTED_TOPIC) == 66
    assert DECISION_REQUESTED_TOPIC != PROPOSAL_POSTED_TOPIC


class _OneLogClient:
    """A chain client that returns exactly one log, and nothing else."""

    def __init__(self, log: Log) -> None:
        self.log = log

    def get_logs(self, address, topics, from_block, to_block):
        return [self.log]


def test_the_decision_request_takes_its_cycle_id_from_the_indexed_topic() -> None:
    # `cycleId` is indexed on the event, so it arrives in topic 1 and not in the data. The data
    # carries the six values that are not indexed.
    log = Log(
        address="0x" + "11" * 20,
        topics=[
            DECISION_REQUESTED_TOPIC,
            "0x" + "0" * 63 + "7",
        ],
        data="0x" + encode_uints([2000 * 10**18, 300, 42, 0, 100_000 * 10**18, 1_700_000_000]),
        block_number=123,
        transaction_hash="0x" + "ab" * 32,
        log_index=0,
    )
    requests = read_decision_requests(_OneLogClient(log), "0x" + "11" * 20, 0, 200)
    assert len(requests) == 1
    request = requests[0]
    assert request.cycle_id == 7
    assert request.price_e18 == 2000 * 10**18
    assert request.rate_bps == 300
    assert request.vol_bps == 42
    assert request.current_lp_share_bps == 0
    assert request.total_value_usd == 100_000 * 10**18
    assert request.requested_at == 1_700_000_000
    assert request.block_number == 123


def test_the_rebalance_takes_its_cycle_id_from_the_indexed_topic() -> None:
    # `cycleId` is indexed on `Rebalanced` too, so the data carries the six values that are
    # not indexed.
    log = Log(
        address="0x" + "11" * 20,
        topics=[
            REBALANCED_TOPIC,
            "0x" + "0" * 63 + "9",
        ],
        data="0x" + encode_uints([4000, 4000, 40_000 * 10**18, 100_000 * 10**18, 0, 33]),
        block_number=456,
        transaction_hash="0x" + "cd" * 32,
        log_index=1,
    )
    rebalances = read_rebalances(_OneLogClient(log), "0x" + "11" * 20, 0, 500)
    assert len(rebalances) == 1
    rebalance = rebalances[0]
    assert rebalance["cycleId"] == 9
    assert rebalance["lpShareBps"] == 4000
    assert rebalance["rangeWidthBps"] == 4000
    assert rebalance["lpValueUsd"] == 40_000 * 10**18
    assert rebalance["totalValueUsd"] == 100_000 * 10**18
    assert rebalance["action"] == 0
    assert rebalance["clampMask"] == 33
    assert rebalance["blockNumber"] == 456
