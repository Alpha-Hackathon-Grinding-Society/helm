"""Keccak-256, the hash Ethereum uses.

Python's `hashlib.sha3_256` is the *finalised* SHA-3 standard, which pads differently from
the original Keccak submission Ethereum uses, so it cannot stand in. This is a compact
pure-python Keccak-256 so the agent never depends on a native extension to compute a
function selector.

It is only used as a fallback: when `eth_hash` (which arrives with `eth-account`) is
installed, that implementation is preferred.
"""
from __future__ import annotations

_MASK = (1 << 64) - 1

_ROUND_CONSTANTS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)

_ROTATIONS = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)

_RATE_BYTES = 136  # 1088 bits, the rate for Keccak-256


def _rotl(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & _MASK


def _keccak_f(state: list[int]) -> None:
    for round_constant in _ROUND_CONSTANTS:
        # theta
        column = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        for x in range(5):
            delta = column[(x + 4) % 5] ^ _rotl(column[(x + 1) % 5], 1)
            for y in range(0, 25, 5):
                state[y + x] ^= delta
        # rho and pi
        rotated = [0] * 25
        for x in range(5):
            for y in range(5):
                rotated[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl(state[x + 5 * y], _ROTATIONS[x][y])
        # chi
        for y in range(0, 25, 5):
            row = rotated[y : y + 5]
            for x in range(5):
                state[y + x] = row[x] ^ ((~row[(x + 1) % 5]) & _MASK & row[(x + 2) % 5])
        # iota
        state[0] ^= round_constant


def keccak256(data: bytes) -> bytes:
    """The Keccak-256 digest of `data`, 32 bytes."""
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % _RATE_BYTES != 0:
        padded.append(0x00)
    padded[-1] ^= 0x80

    state = [0] * 25
    for offset in range(0, len(padded), _RATE_BYTES):
        block = padded[offset : offset + _RATE_BYTES]
        for i in range(_RATE_BYTES // 8):
            state[i] ^= int.from_bytes(block[i * 8 : i * 8 + 8], "little")
        _keccak_f(state)

    out = bytearray()
    for i in range(4):  # 4 * 8 bytes = 32 bytes, less than the rate
        out += state[i].to_bytes(8, "little")
    return bytes(out)


def selector(signature: str) -> str:
    """The four byte function selector of a solidity signature."""
    return "0x" + keccak256(signature.encode()).hex()[:8]


def event_topic(signature: str) -> str:
    """The 32 byte topic of a solidity event signature."""
    return "0x" + keccak256(signature.encode()).hex()
