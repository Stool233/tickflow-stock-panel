from __future__ import annotations

from app.tickflow import policy
from app.tickflow.capabilities import Cap, CapabilityLimits, CapabilitySet

TIERS = {
    "none": {
        "kline.daily.by_symbol": {},
        "kline.daily.batch": {},
    },
    "free": {
        "quote.by_symbol": {},
        "kline.daily.by_symbol": {},
        "kline.daily.batch": {},
    },
    "starter": {
        "quote.by_symbol": {},
        "quote.batch": {},
        "quote.pool": {},
        "kline.daily.by_symbol": {},
        "kline.daily.batch": {},
        "adj_factor": {},
    },
    "pro": {
        "kline.minute.batch": {},
    },
    "expert": {
        "intraday.batch": {},
        "websocket": {},
        "financial": {},
    },
}


def capset(*caps: Cap) -> CapabilitySet:
    return CapabilitySet({cap: CapabilityLimits() for cap in caps})


def test_financial_only_key_is_valid_independent_capability():
    assert Cap.FINANCIAL not in policy.TIER_SIGNATURES["expert"]

    caps = capset(Cap.FINANCIAL)

    classified = policy._classify_tier(caps, TIERS)
    label, missing, extras = policy._compute_label_and_missing(caps, TIERS)

    assert not classified.is_invalid
    assert not classified.is_free
    assert classified.tier == "free"
    assert policy.capset_requires_paid_endpoint(caps, TIERS)
    assert label == "Free + 财务"
    assert missing == []
    assert extras == ["financial"]


def test_free_plus_quote_batch_financial_is_not_starter():
    assert Cap.QUOTE_BATCH not in policy.TIER_SIGNATURES["starter"]

    caps = capset(
        Cap.QUOTE_BY_SYMBOL,
        Cap.QUOTE_BATCH,
        Cap.KLINE_DAILY_BY_SYMBOL,
        Cap.FINANCIAL,
    )

    classified = policy._classify_tier(caps, TIERS)
    label, missing, extras = policy._compute_label_and_missing(caps, TIERS)

    assert not classified.is_free
    assert classified.tier == "free"
    assert policy.capset_requires_paid_endpoint(caps, TIERS)
    assert label == "Free + 财务"
    assert missing == []
    assert extras == ["financial"]


def test_starter_plus_financial_keeps_starter_base_label():
    caps = capset(
        Cap.QUOTE_BY_SYMBOL,
        Cap.QUOTE_BATCH,
        Cap.QUOTE_POOL,
        Cap.KLINE_DAILY_BY_SYMBOL,
        Cap.KLINE_DAILY_BATCH,
        Cap.ADJ_FACTOR,
        Cap.FINANCIAL,
    )

    classified = policy._classify_tier(caps, TIERS)
    label, missing, extras = policy._compute_label_and_missing(caps, TIERS)

    assert not classified.is_free
    assert classified.tier == "starter"
    assert policy.capset_requires_paid_endpoint(caps, TIERS)
    assert label == "Starter + 财务"
    assert missing == []
    assert extras == ["financial"]


def test_pure_free_key_does_not_require_paid_endpoint():
    caps = capset(
        Cap.QUOTE_BY_SYMBOL,
        Cap.KLINE_DAILY_BY_SYMBOL,
        Cap.KLINE_DAILY_BATCH,
    )

    classified = policy._classify_tier(caps, TIERS)
    label, missing, extras = policy._compute_label_and_missing(caps, TIERS)

    assert classified.is_free
    assert classified.tier == "free"
    assert not policy.capset_requires_paid_endpoint(caps, TIERS)
    assert label == "Free"
    assert missing == []
    assert extras == []
