#!/usr/bin/env python3
"""Compare the deployed runtime bytecode with the committed Foundry artifact.

Solidity copies immutable values into the deployed code at every place they are read,
so the committed artifact can never be byte-identical to what is on the chain: the
artifact leaves a zero word where the immutable goes, and the chain carries the real
address. A naive `cast code` comparison therefore always fails, and a check that
ignores the difference entirely proves nothing.

This script does the strict version of the comparison, in two halves:

  1. every byte *outside* an immutable reference site is identical, and
  2. every immutable reference site on the chain holds one of the addresses this
     deployment is supposed to have baked in.

Together those say exactly what byte equality would have said: not one instruction of
the code moved, and the only things that differ are the addresses the constructor was
given.

Usage:
    scripts/verify-bytecode.py --artifact path.json --address 0x... --rpc URL \\
        --immutable 0xaaa --immutable 0xbbb [--label HelmVault]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def artifact_code(path: Path) -> str:
    data = json.loads(path.read_text())
    code = data["deployedBytecode"]["object"]
    return code[2:] if code.startswith("0x") else code


def onchain_code(address: str, rpc: str) -> str:
    out = subprocess.run(
        ["cast", "code", address, "--rpc-url", rpc],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if out.returncode != 0:
        raise RuntimeError(f"cast code failed: {out.stderr.strip()}")
    code = out.stdout.strip()
    return code[2:] if code.startswith("0x") else code


def address_bytes(value: str) -> bytes:
    return bytes.fromhex(value.lower().removeprefix("0x").rjust(40, "0"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--address", required=True)
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--immutable", action="append", default=[], help="an address the deployment baked in")
    parser.add_argument("--label", default="contract")
    args = parser.parse_args(argv)

    expected = artifact_code(args.artifact)
    actual = onchain_code(args.address, args.rpc)

    if len(expected) != len(actual):
        print(
            f"FAIL {args.label}: length differs — artifact {len(expected) // 2} bytes, "
            f"on chain {len(actual) // 2} bytes",
            file=sys.stderr,
        )
        return 1

    expected_bytes = bytes.fromhex(expected)
    actual_bytes = bytes.fromhex(actual)

    differing = {i for i in range(len(expected_bytes)) if expected_bytes[i] != actual_bytes[i]}

    # An address immutable is read as a PUSH20, so the artifact holds twenty zero bytes
    # where the address goes. Find every such site and check what the chain put there.
    known = {address_bytes(value): value.lower() for value in args.immutable}
    covered: set[int] = set()
    found: list[str] = []
    for offset in range(len(expected_bytes) - 19):
        if expected_bytes[offset : offset + 20] != b"\x00" * 20:
            continue
        candidate = actual_bytes[offset : offset + 20]
        if candidate in known:
            covered.update(range(offset, offset + 20))
            found.append(known[candidate])

    uncovered = differing - covered
    if uncovered:
        # Report the bytes the chain put in the first unexplained slot.
        first = min(uncovered)
        start = first
        while start > 0 and expected_bytes[start - 1] == 0:
            start -= 1
        end = first
        while end < len(expected_bytes) and expected_bytes[end] == 0:
            end += 1
        print(
            f"FAIL {args.label}: {len(uncovered)} byte(s) differ outside the immutable "
            f"sites, first at byte {first} (the chain holds "
            f"0x{actual_bytes[start:end].hex()})",
            file=sys.stderr,
        )
        return 1

    where = ", ".join(sorted(set(found))) or "none"
    print(
        f"ok {args.label}: the deployed runtime is identical to the artifact at every "
        f"byte outside {len(covered)} immutable byte(s) holding {where}; "
        f"{len(actual_bytes)} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
