"""A stand-in for Rifd's policy system: health claims outside the network need the policy's benefit
limits, which the real system answers slowly. The delay is part of the case study (lab 3.2)."""

from __future__ import annotations

import asyncio


class LookupError_(Exception):
    pass


def needs_lookup(claim: dict) -> bool:
    return claim.get("line") == "health" and claim.get("in_network") is False


async def benefit_limit(claim: dict, key: str, delay_ms: float) -> float:
    if not key:
        raise LookupError_("RIFD_LOOKUP_KEY is not set: the policy system refuses the call")
    await asyncio.sleep(delay_ms / 1000)  # waiting on the network: the worker serves other requests meanwhile
    return 50000.0
